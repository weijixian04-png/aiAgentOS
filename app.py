import tornado.ioloop
import tornado.web
from tornado.httpserver import HTTPServer
import os

from app.models.db import init_db, init_default_users, init_scout_sources, init_api_interfaces, init_digital_employees, init_sentiment_samples
from app.models.user import UserRepository
from app.models.gesture_config import GestureConfigRepository
from app.models.crawl_task import CrawlTaskRepository, CrawlLogRepository

# 导入控制器
from app.controllers.auth import LoginHandler, LogoutHandler, UserLoginHandler, RegisterHandler
from app.controllers.home import AdminHandler, IndexHandler, WelcomeHandler
from app.controllers.user import UserListHandler, UserApiHandler, UserInfoHandler
from app.controllers.model import ModelListHandler, ModelApiHandler, ModelTokenStatsHandler, ModelChatHandler, ModelChatApiHandler, ModelOptionsHandler
from app.controllers.role import RoleListHandler, RoleApiHandler
from app.controllers.permission import PermissionListHandler, PermissionApiHandler
from app.controllers.function import FunctionListHandler, ModuleListHandler, FunctionApiHandler, ModuleApiHandler
from app.controllers.scout import ScoutListHandler, ScoutApiHandler, ScoutCollectHandler
from app.controllers.employee import EmployeeListHandler, EmployeeApiHandler, EmployeeChatHandler, EmployeeChatApiHandler, EmployeeListApiHandler
from app.controllers.interface import InterfaceListHandler, InterfaceApiHandler
from app.controllers.warehouse import WarehouseListHandler, WarehouseApiHandler, WarehouseDetailHandler, WarehouseStatsApiHandler
from app.controllers.deep_collect import DeepCollectListHandler, DeepCollectApiHandler, DeepCollectStatsApiHandler
from app.controllers.chat import ChatHandler, ChatApiHandler, ChatSessionListHandler
from app.controllers.friend_chat import FriendChatHandler
from app.controllers.friendship import FriendApiHandler, PrivateChatApiHandler
from app.controllers.group_chat import GroupChatApiHandler
from app.controllers.chat_system import ChatSystemHandler
from app.controllers.admin_group import AdminGroupHandler, AdminGroupApiHandler, AdminFileHandler, AdminFileApiHandler, AdminServerHandler, AdminServerApiHandler
from app.controllers.datav import DataVListHandler, DataVScreenHandler, DataVApiHandler, DataVStatsApiHandler, DataVLocationApiHandler, DataVCacheClearHandler
from app.controllers.sentiment import SentimentListHandler, SentimentApiHandler, SentimentStatsApiHandler, SentimentAnalyzeHandler, SentimentDetailHandler
from app.controllers.gesture import GestureDemoHandler
from app.controllers.gesture_static import GestureStaticFileHandler
from app.controllers.gesture_config import GestureConfigListHandler, GestureConfigApiHandler, GestureToggleApiHandler
from app.controllers.crawl_task import CrawlTaskListHandler, CrawlTaskApiHandler, CrawlLogListHandler, CrawlLogApiHandler, CrawlLogDetailHandler
from wechat_chat.backend.chat_routes import get_chat_routes

def make_app():
    routes = [
            # 首页
            (r"/", IndexHandler),
            
            # 认证路由
            (r"/auth/login", LoginHandler),
            (r"/auth/user/login", UserLoginHandler),
            (r"/auth/register", RegisterHandler),
            (r"/auth/logout", LogoutHandler),
            
            # 后台主页
            (r"/admin", AdminHandler),
            (r"/admin/welcome", WelcomeHandler),
            
            # 用户管理路由
            (r"/admin/users", UserListHandler),
            (r"/api/users", UserApiHandler),
            (r"/api/user/info", UserInfoHandler),
            
            # 角色管理路由
            (r"/admin/roles", RoleListHandler),
            (r"/api/roles", RoleApiHandler),
            
            # 权限管理路由
            (r"/admin/permissions", PermissionListHandler),
            (r"/api/permissions", PermissionApiHandler),
            
            # 功能管理路由
            (r"/admin/functions", FunctionListHandler),
            (r"/admin/modules", ModuleListHandler),
            (r"/api/functions", FunctionApiHandler),
            (r"/api/modules", ModuleApiHandler),
            
            # 模型引擎路由
            (r"/admin/models", ModelListHandler),
            (r"/api/models", ModelApiHandler),
            (r"/api/models/token-stats", ModelTokenStatsHandler),
            (r"/api/models/options", ModelOptionsHandler),
            (r"/admin/models/chat", ModelChatHandler),
            (r"/api/models/chat", ModelChatApiHandler),
            
            # 瞭望管理路由
            (r"/admin/scout", ScoutListHandler),
            (r"/api/scout", ScoutApiHandler),
            (r"/admin/scout/collect", ScoutCollectHandler),
            
            # 数字员工路由
            (r"/admin/employees", EmployeeListHandler),
            (r"/admin/employees/chat", EmployeeChatHandler),
            (r"/api/employees", EmployeeApiHandler),
            (r"/api/employees/chat", EmployeeChatApiHandler),
            (r"/api/employees/list", EmployeeListApiHandler),
            
            # 接口管理路由
            (r"/admin/interfaces", InterfaceListHandler),
            (r"/api/interfaces", InterfaceApiHandler),
            
            # 数据仓库路由
            (r"/admin/warehouse", WarehouseListHandler),
            (r"/admin/warehouse/detail", WarehouseDetailHandler),
            (r"/api/warehouse", WarehouseApiHandler),
            (r"/api/warehouse/stats", WarehouseStatsApiHandler),

            # 数智大屏路由
            (r"/admin/datav", DataVListHandler),
            (r"/screen/datav", DataVScreenHandler),
            (r"/api/datav", DataVApiHandler),
            (r"/api/datav/stats", DataVStatsApiHandler),
            (r"/api/datav/location", DataVLocationApiHandler),
            (r"/api/datav/cache", DataVCacheClearHandler),

            # 智能舆情路由
            (r"/admin/sentiment", SentimentListHandler),
            (r"/api/sentiment", SentimentApiHandler),
            (r"/api/sentiment/stats", SentimentStatsApiHandler),
            (r"/api/sentiment/analyze", SentimentAnalyzeHandler),
            (r"/api/sentiment/detail/(\d+)", SentimentDetailHandler),

            # AI深度采集路由
            (r"/admin/deep-collect", DeepCollectListHandler),
            (r"/api/deep-collect", DeepCollectApiHandler),

            # 用户侧聊天路由
            (r"/chat", ChatHandler),
            (r"/api/chat", ChatApiHandler),
            (r"/api/chat/sessions", ChatSessionListHandler),
            
            # 好友聊天路由
            (r"/chat/friend", FriendChatHandler),
            (r"/api/friend", FriendApiHandler),
            (r"/api/chat/private", PrivateChatApiHandler),
            
            # 群聊路由
            (r"/chat/system", ChatSystemHandler),
            (r"/api/group", GroupChatApiHandler),
            
            # 后台管理路由
            (r"/admin/group", AdminGroupHandler),
            (r"/api/admin/group", AdminGroupApiHandler),
            (r"/admin/file", AdminFileHandler),
            (r"/api/admin/file", AdminFileApiHandler),
            (r"/admin/server", AdminServerHandler),
            (r"/api/admin/server", AdminServerApiHandler),
            
            # 手势交互路由
            (r"/gesture/demo", GestureDemoHandler),
            (r"/gesture_control/(.*)", GestureStaticFileHandler, {"path": "gesture_control"}),
            
            # 手势配置管理路由
            (r"/admin/gesture", GestureConfigListHandler),
            (r"/api/gesture/config", GestureConfigApiHandler),
            (r"/api/gesture/toggle", GestureToggleApiHandler),

            # 定时爬取路由
            (r"/admin/crawl", CrawlTaskListHandler),
            (r"/api/crawl_task", CrawlTaskApiHandler),
            (r"/admin/crawl/logs", CrawlLogListHandler),
            (r"/api/crawl_log", CrawlLogApiHandler),
            (r"/api/crawl_log/(\d+)", CrawlLogDetailHandler),
        ]
    
    # 整合子系统路由
    routes.extend(get_chat_routes())
    
    return tornado.web.Application(
        routes,
        template_path=os.path.join(os.path.dirname(__file__), "app", "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "app", "static"),
        cookie_secret="cnAgentOS-2026-secret-key-change-in-production",
        debug=True,
        xsrf_cookies=True,
        login_url="/auth/login",
    )

def init_admin_user():
    """初始化默认管理员用户"""
    if not UserRepository.get_user_by_username("admin"):
        UserRepository.create_user("admin", "admin888", "admin")
        print("默认管理员用户创建成功: admin/admin888")
    else:
        # 如果admin用户已存在但角色不是admin，更新角色
        user = UserRepository.get_user_by_username("admin")
        if user and user["role"] != "admin":
            UserRepository.update_user(user["id"], role="admin")
            print("已更新admin用户角色为超级管理员")

def _init_default_crawl_tasks():
    """初始化默认爬取任务"""
    default_tasks = [
        {
            "task_name": "百度新闻-四川农业大学",
            "url": "https://www.baidu.com/s?rtt=1&bsst=1&cl=2&tn=news&rsv_dl=ns_pc&word=%E5%9B%9B%E5%B7%9D%E5%86%9C%E4%B8%9A%E5%A4%A7%E5%AD%A6",
            "cron_expr": "0 */2 * * *",
            "extract_rule": "text",
            "status": 1
        }
    ]
    existing = CrawlTaskRepository.get_all(1, 100)
    existing_names = [t['task_name'] for t in existing]
    for task in default_tasks:
        if task['task_name'] not in existing_names:
            CrawlTaskRepository.create(
                task['task_name'], task['url'],
                task['cron_expr'], task['extract_rule'],
                task['status']
            )
            print(f"已创建默认爬取任务: {task['task_name']}")

if __name__ == "__main__":
    init_db()
    init_default_users()
    init_admin_user()
    init_scout_sources()
    init_api_interfaces()
    init_digital_employees()
    init_sentiment_samples()
    
    # 初始化手势配置
    GestureConfigRepository.init_gesture_config_table()
    GestureConfigRepository.init_default_gesture_configs()
    
    # 初始化定时爬取模块
    CrawlTaskRepository.init_table()
    CrawlLogRepository.init_table()
    
    # 初始化默认爬取任务
    _init_default_crawl_tasks()
    
    app = make_app()
    app.listen(1086)
    print("====== Server 启动成功 ====== 端口：1086 =======", flush=True)
    
    # 启动爬取调度器
    from crawl_scheduler.backend.scheduler import init_scheduler
    init_scheduler()
    
    tornado.ioloop.IOLoop.current().start()
