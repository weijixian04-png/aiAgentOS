import json
import tornado.web
from urllib.parse import urlparse
from croniter import croniter
from datetime import datetime

from app.controllers.base import BaseHandler
from app.models.crawl_task import CrawlTaskRepository, CrawlLogRepository
from crawl_scheduler.backend.scheduler import reload_task, remove_task
from crawl_scheduler.backend.crawl_engine import run_crawl_task


class CrawlTaskListHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        xsrf_token = self.xsrf_token.decode('utf-8')
        self.render("crawl_task_list.html",
                    current_user=self.current_user,
                    xsrf_token=xsrf_token)


class CrawlTaskApiHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        try:
            page = int(self.get_argument("page", 1))
            page_size = int(self.get_argument("limit", 10))
        except ValueError:
            page = 1
            page_size = 10

        tasks = CrawlTaskRepository.get_all(page, page_size)
        total = CrawlTaskRepository.get_total_count()

        self.write(json.dumps({
            "code": 0,
            "msg": "success",
            "count": total,
            "data": tasks
        }))

    @tornado.web.authenticated
    def post(self):
        action = self.get_body_argument("action", "")

        if action == "add":
            self._add_task()
        elif action == "edit":
            self._edit_task()
        elif action == "delete":
            self._delete_task()
        elif action == "toggle":
            self._toggle_status()
        elif action == "run_now":
            self._run_now()
        else:
            self.set_status(400)
            self.write(json.dumps({"code": 1, "msg": "无效的操作"}))

    def _add_task(self):
        task_name = self.get_body_argument("task_name", "").strip()
        url = self.get_body_argument("url", "").strip()
        cron_expr = self.get_body_argument("cron_expr", "0 * * * *").strip()
        extract_rule = self.get_body_argument("extract_rule", "title").strip()
        status = self.get_body_argument("status", "1").strip()

        if not task_name or not url:
            self.write(json.dumps({"code": 1, "msg": "任务名称和URL不能为空"}))
            return

        if not self._validate_url(url):
            self.write(json.dumps({"code": 1, "msg": "无效的URL格式，需以http/https开头"}))
            return

        if not self._validate_cron(cron_expr):
            self.write(json.dumps({"code": 1, "msg": "无效的Cron表达式"}))
            return

        status_int = 1 if status in ("1", "true", "on") else 0

        if CrawlTaskRepository.create(task_name, url, cron_expr, extract_rule, status_int):
            from app.models.crawl_task import CrawlTaskRepository as CTR
            tasks = CTR.get_all(1, 1)
            if tasks:
                new_task = tasks[0]
                if status_int == 1:
                    reload_task(new_task['id'])
            self.write(json.dumps({"code": 0, "msg": "添加成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "添加失败"}))

    def _edit_task(self):
        task_id = self.get_body_argument("id", "")
        task_name = self.get_body_argument("task_name", "").strip()
        url = self.get_body_argument("url", "").strip()
        cron_expr = self.get_body_argument("cron_expr", "").strip()
        extract_rule = self.get_body_argument("extract_rule", "").strip()
        status = self.get_body_argument("status", "")

        if not task_id:
            self.write(json.dumps({"code": 1, "msg": "ID不能为空"}))
            return

        try:
            task_id = int(task_id)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID"}))
            return

        update_params = {}
        if task_name:
            update_params['task_name'] = task_name
        if url:
            if not self._validate_url(url):
                self.write(json.dumps({"code": 1, "msg": "无效的URL格式"}))
                return
            update_params['url'] = url
        if cron_expr:
            if not self._validate_cron(cron_expr):
                self.write(json.dumps({"code": 1, "msg": "无效的Cron表达式"}))
                return
            update_params['cron_expr'] = cron_expr
        if extract_rule:
            update_params['extract_rule'] = extract_rule
        if status != "":
            update_params['status'] = 1 if status in ("1", "true", "on") else 0

        if not update_params:
            self.write(json.dumps({"code": 1, "msg": "至少需要修改一项"}))
            return

        if CrawlTaskRepository.update(task_id, **update_params):
            reload_task(task_id)
            self.write(json.dumps({"code": 0, "msg": "修改成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "修改失败"}))

    def _delete_task(self):
        task_id = self.get_body_argument("id", "")
        if not task_id:
            self.write(json.dumps({"code": 1, "msg": "ID不能为空"}))
            return

        try:
            task_id = int(task_id)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID"}))
            return

        CrawlLogRepository.delete_by_task(task_id)
        remove_task(task_id)
        if CrawlTaskRepository.delete(task_id):
            self.write(json.dumps({"code": 0, "msg": "删除成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "删除失败"}))

    def _toggle_status(self):
        task_id = self.get_body_argument("id", "")
        if not task_id:
            self.write(json.dumps({"code": 1, "msg": "ID不能为空"}))
            return

        try:
            task_id = int(task_id)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID"}))
            return

        CrawlTaskRepository.toggle_status(task_id)
        reload_task(task_id)
        self.write(json.dumps({"code": 0, "msg": "状态切换成功"}))

    def _run_now(self):
        task_id = self.get_body_argument("id", "")
        if not task_id:
            self.write(json.dumps({"code": 1, "msg": "ID不能为空"}))
            return

        try:
            task_id = int(task_id)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID"}))
            return

        task = CrawlTaskRepository.get_by_id(task_id)
        if not task:
            self.write(json.dumps({"code": 1, "msg": "任务不存在"}))
            return

        result = run_crawl_task(task_id)
        if result and result.get('success'):
            self.write(json.dumps({
                "code": 0,
                "msg": "执行成功",
                "data": result
            }))
        else:
            self.write(json.dumps({
                "code": 1,
                "msg": f"执行失败: {result.get('error', '未知错误') if result else '未知错误'}"
            }))

    def _validate_url(self, url):
        try:
            result = urlparse(url)
            return all([result.scheme in ('http', 'https'), result.netloc])
        except Exception:
            return False

    def _validate_cron(self, cron_expr):
        try:
            croniter(cron_expr)
            return True
        except Exception:
            return False


class CrawlLogListHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        xsrf_token = self.xsrf_token.decode('utf-8')
        self.render("crawl_log_list.html",
                    current_user=self.current_user,
                    xsrf_token=xsrf_token)


class CrawlLogApiHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        try:
            page = int(self.get_argument("page", 1))
            page_size = int(self.get_argument("limit", 10))
        except ValueError:
            page = 1
            page_size = 10

        task_id = self.get_argument("task_id", "")
        status = self.get_argument("status", "")
        start_date = self.get_argument("start_date", "")
        end_date = self.get_argument("end_date", "")

        task_id = int(task_id) if task_id else None

        logs, total = CrawlLogRepository.get_all(
            page, page_size,
            task_id=task_id,
            status=status if status else None,
            start_date=start_date if start_date else None,
            end_date=end_date if end_date else None
        )

        self.write(json.dumps({
            "code": 0,
            "msg": "success",
            "count": total,
            "data": logs
        }))


class CrawlLogDetailHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, log_id):
        try:
            log_id = int(log_id)
        except ValueError:
            self.set_status(400)
            self.write(json.dumps({"code": 1, "msg": "无效的ID"}))
            return

        log = CrawlLogRepository.get_by_id(log_id)
        if not log:
            self.set_status(404)
            self.write(json.dumps({"code": 1, "msg": "日志不存在"}))
            return

        self.write(json.dumps({"code": 0, "data": log}))
