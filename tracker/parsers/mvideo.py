import requests
from base import BaseParser


class MVideoParser(BaseParser):

    def parse(self):
        url = "https://search.mvideo.ru/bff/products/search"

        params = {
            "query": self.query,
            "limit": 10
        }

        headers = {"User-Agent": "Mozilla/5.0"}

        r = requests.get(url, params=params, headers=headers)
        data = r.json()

        products = data.get("body", {}).get("products", [])

        results = []

        for p in products:
            results.append(
                self.format_result(
                    p.get("name"),
                    p.get("price", {}).get("salePrice")
                )
            )

        return results