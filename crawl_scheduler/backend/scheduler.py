import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from croniter import croniter
from datetime import datetime
from app.models.crawl_task import CrawlTaskRepository
from crawl_scheduler.backend.crawl_engine import run_crawl_task


scheduler = None


def init_scheduler():
    global scheduler
    if scheduler is not None and scheduler.running:
        return scheduler

    scheduler = BackgroundScheduler()
    _load_tasks()
    scheduler.start()
    print("[CrawlScheduler] 调度器已启动", flush=True)
    return scheduler


def _load_tasks():
    global scheduler
    if not scheduler:
        return

    tasks = CrawlTaskRepository.get_enabled_tasks()
    for task in tasks:
        try:
            _add_job(task)
        except Exception as e:
            print(f"[CrawlScheduler] 加载任务 {task['id']} 失败: {e}", flush=True)


def _add_job(task):
    global scheduler
    if not scheduler:
        return

    job_id = f"crawl_task_{task['id']}"
    try:
        parts = task['cron_expr'].split()
        if len(parts) == 5:
            trigger = CronTrigger(
                minute=parts[0], hour=parts[1], day=parts[2],
                month=parts[3], day_of_week=parts[4]
            )
        else:
            print(f"[CrawlScheduler] 无效的Cron表达式: {task['cron_expr']}", flush=True)
            return

        scheduler.add_job(
            run_crawl_task,
            trigger=trigger,
            args=[task['id']],
            id=job_id,
            replace_existing=True,
            misfire_grace_time=60
        )

        next_run = None
        try:
            cron = croniter(task['cron_expr'], datetime.now())
            next_run = cron.get_next(datetime).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass

        CrawlTaskRepository.update(task['id'], next_run=next_run)
        print(f"[CrawlScheduler] 已添加任务: {task['task_name']} (ID:{task['id']}) Cron:{task['cron_expr']} 下次执行:{next_run}", flush=True)

    except Exception as e:
        print(f"[CrawlScheduler] 添加任务 {task['id']} 到调度器失败: {e}", flush=True)


def reload_task(task_id):
    global scheduler
    if not scheduler:
        return

    job_id = f"crawl_task_{task_id}"
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass

    task = CrawlTaskRepository.get_by_id(task_id)
    if task and task['status'] == 1:
        _add_job(task)
    else:
        next_run = None
        CrawlTaskRepository.update(task_id, next_run=next_run)
        print(f"[CrawlScheduler] 已移除任务 ID:{task_id}", flush=True)


def remove_task(task_id):
    global scheduler
    if not scheduler:
        return

    job_id = f"crawl_task_{task_id}"
    try:
        scheduler.remove_job(job_id)
        print(f"[CrawlScheduler] 已移除任务 ID:{task_id}", flush=True)
    except Exception:
        pass


def shutdown_scheduler():
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        print("[CrawlScheduler] 调度器已关闭", flush=True)
