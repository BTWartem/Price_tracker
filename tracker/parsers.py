# tracker/parsers.py
import logging
from .parsers.scrapy_runner import ScrapyRunner

logger = logging.getLogger(__name__)

def get_parser(url):
    """
    Фабрика парсеров - возвращает ScrapyRunner для любого URL
    """
    logger.info(f"🔧 Создаем Scrapy парсер для: {url}")
    return ScrapyRunner(url)