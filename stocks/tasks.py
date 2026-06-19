import logging
import time
from celery import shared_task
from celery.utils.log import get_task_logger
from .utils import fetch_and_save_stock_data
from .models import StockIndicator, TrackedStock

logger = get_task_logger(__name__)


@shared_task
def test_celery():
    logger.info("Celery test task executed.")
    return "Celery is working!"


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def update_stock_data_task(self, symbol):
    logger.info(f"TASK: Updating data for {symbol}")
    result_message = fetch_and_save_stock_data(symbol)
    logger.info(f"TASK: Finished {symbol} — {result_message}")
    return result_message


@shared_task
def update_all_stocks_task():
    """Daily task: refresh all tracked symbols."""
    logger.info("--- Daily Stock Update Started ---")

    tracked = set(TrackedStock.objects.values_list('symbol', flat=True))
    existing = set(StockIndicator.objects.values_list('symbol', flat=True).distinct())
    symbols = tracked | existing

    if not symbols:
        logger.info("TASK: No symbols to update.")
        return "No symbols to update."

    logger.info(f"TASK: Queuing {len(symbols)} symbols: {list(symbols)}")

    for symbol in symbols:
        update_stock_data_task.delay(symbol)

    logger.info("--- Daily Stock Update: all jobs queued ---")
    return f"Queued updates for {len(symbols)} symbols."
