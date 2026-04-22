class BaseParser:
    def __init__(self, query):
        self.query = query

    def parse(self):
        raise NotImplementedError

    def format_result(self, title, price, link=None):
        return {
            "title": title,
            "price": price,
            "link": link
        }