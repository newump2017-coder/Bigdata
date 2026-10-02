"""
وظيفتان مجدولتان لتحديث Materialized Views.
يمكن تشغيلهما يدويًا من الـAPI عبر POST /jobs/{name}/run.
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .materialized_views import refresh_mv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jobs")

scheduler = BackgroundScheduler(timezone="UTC")


def _run_refresh_daily_sales():
    n = refresh_mv("daily_sales_summary")
    logger.info("[job] refreshed daily_sales_summary: %s docs", n)
    return n


def _run_refresh_top_products():
    n = refresh_mv("top_products_summary")
    logger.info("[job] refreshed top_products_summary: %s docs", n)
    return n


JOBS = {
    "refresh_daily_sales": {
        "description": "تحديث العرض المادي daily_sales_summary (يوميًا 00:00).",
        "func": _run_refresh_daily_sales,
        "trigger": CronTrigger(hour=0, minute=0),
    },
    "refresh_top_products": {
        "description": "تحديث العرض المادي top_products_summary (كل ساعة).",
        "func": _run_refresh_top_products,
        "trigger": CronTrigger(minute=0),
    },
}


def register_jobs():
    for name, spec in JOBS.items():
        scheduler.add_job(
            spec["func"],
            trigger=spec["trigger"],
            id=name,
            name=name,
            replace_existing=True,
        )
        logger.info("registered job: %s", name)


def run_job(name: str) -> dict:
    if name not in JOBS:
        raise KeyError(name)
    try:
        result = JOBS[name]["func"]()
        return {"job": name, "status": "success", "affected_docs": result}
    except Exception as e:
        logger.exception("job failed: %s", name)
        return {"job": name, "status": "failed", "error": str(e)}
