from celery import shared_task
from .utils import fetch_and_save_stock_data
import logging
from celery.exceptions import Retry
from celery.utils.log import get_task_logger
import time

logger = get_task_logger(__name__)

@shared_task(bind=True, retry_kwargs={'max_retries':3,})
def update_stock_data_daily(self):
    symbols = ['AAPL', 'TSLA', 'MSFT']
    for  symbol in symbols:
        try:
            logger.info(f"Fetching stock data for {symbol}")
            fetch_and_save_stock_data(symbol)
            logger.info(f"Error fetching data for {symbol}")
        except Exception as exc:
            logger.warning(f"Error fetching data for {symbol}, retrying... ({exc})")
            try:
                raise self.retry(exc=exc, countdown=60)
            except self.MaxRetriesExceededError:
                logger.error(f"Max retries exceeded for {symbol}. Skipping.")