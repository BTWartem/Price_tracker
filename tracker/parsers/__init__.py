# tracker/parsers/__init__.py
from .simple_parser import SimpleParser

def get_parser(url, product_id=None):
    """
    Фабрика парсеров - возвращает SimpleParser
    """
    return SimpleParser(url, product_id)

__all__ = ['get_parser', 'SimpleParser']