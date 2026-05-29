import json
import tornado.web

from app.controllers.base import BaseHandler
from app.models.db import (
    DEFAULT_SQLITE_PATH,
    get_database_config,
    get_database_status,
    init_db,
    init_api_interfaces,
    init_digital_employees,
    init_scout_sources,
    save_database_config,
    test_database_connection,
)
from app.models.user import UserRepository
from wechat_chat.backend.db import init_db as init_wechat_db


def _public_database_config(config):
    mysql_config = config.get("mysql", {})
    return {
        "type": config.get("type", "sqlite"),
        "sqlite_path": config.get("sqlite_path") or DEFAULT_SQLITE_PATH,
        "mysql": {
            "host": mysql_config.get("host", "127.0.0.1"),
            "port": mysql_config.get("port", 3306),
            "user": mysql_config.get("user", "root"),
            "database": mysql_config.get("database", "ai_agent_os"),
            "charset": mysql_config.get("charset", "utf8mb4"),
            "password_set": bool(mysql_config.get("password")),
        },
    }


def _init_default_data():
    init_db()
    if not UserRepository.get_user_by_username("admin"):
        UserRepository.create_user("admin", "admin888", "admin")
    else:
        user = UserRepository.get_user_by_username("admin")
        if user and user["role"] != "admin":
            UserRepository.update_user(user["id"], role="admin")
    init_scout_sources()
    init_api_interfaces()
    init_digital_employees()
    init_wechat_db()


class DatabaseConfigHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        xsrf_token = self.xsrf_token.decode("utf-8")
        config = get_database_config()
        self.render(
            "database_config.html",
            current_user=self.current_user,
            xsrf_token=xsrf_token,
            database_config=_public_database_config(config),
            database_status=get_database_status(),
        )


class DatabaseConfigApiHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        config = get_database_config()
        self.write(json.dumps({
            "code": 0,
            "msg": "success",
            "data": _public_database_config(config),
            "status": get_database_status(),
        }, ensure_ascii=False))

    @tornado.web.authenticated
    def post(self):
        old_config = get_database_config()
        next_config = json.loads(json.dumps(old_config))
        db_type = self.get_body_argument("type", old_config.get("type", "sqlite")).strip().lower()
        if db_type not in ("sqlite", "mysql"):
            self.write(json.dumps({"code": 1, "msg": "数据库类型只能是sqlite或mysql"}, ensure_ascii=False))
            return

        next_config["type"] = db_type
        if db_type == "sqlite":
            next_config["sqlite_path"] = self.get_body_argument("sqlite_path", DEFAULT_SQLITE_PATH).strip() or DEFAULT_SQLITE_PATH
        else:
            mysql_config = next_config.setdefault("mysql", {})
            mysql_config["host"] = self.get_body_argument("host", mysql_config.get("host", "127.0.0.1")).strip() or "127.0.0.1"
            try:
                mysql_config["port"] = int(self.get_body_argument("port", str(mysql_config.get("port", 3306))).strip() or 3306)
            except ValueError:
                self.write(json.dumps({"code": 1, "msg": "MySQL端口必须是数字"}, ensure_ascii=False))
                return
            mysql_config["user"] = self.get_body_argument("user", mysql_config.get("user", "root")).strip() or "root"
            password = self.get_body_argument("password", "")
            if password:
                mysql_config["password"] = password
            mysql_config["database"] = self.get_body_argument("database", mysql_config.get("database", "ai_agent_os")).strip() or "ai_agent_os"
            mysql_config["charset"] = self.get_body_argument("charset", mysql_config.get("charset", "utf8mb4")).strip() or "utf8mb4"

        ok, message = test_database_connection(next_config)
        if not ok:
            self.write(json.dumps({"code": 1, "msg": message}, ensure_ascii=False))
            return

        save_database_config(next_config)
        try:
            _init_default_data()
        except Exception as exc:
            save_database_config(old_config)
            self.write(json.dumps({"code": 1, "msg": f"数据库初始化失败: {exc}"}, ensure_ascii=False))
            return

        self.write(json.dumps({
            "code": 0,
            "msg": "数据库配置已保存",
            "data": _public_database_config(get_database_config()),
            "status": get_database_status(),
        }, ensure_ascii=False))
