import requests
from bs4 import BeautifulSoup
from base import BaseParser


class DNSParser(BaseParser):

    def parse(self):
        url = f"https://www.dns-shop.ru/search/?q={self.query}"

        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers)

        soup = BeautifulSoup(r.text, "html.parser")

        items = soup.select(".catalog-product")

        results = []

        for item in items[:10]:
            title = item.select_one(".catalog-product__name")
            price = item.select_one(".product-buy__price")

            results.append(
                self.format_result(
                    title.text.strip() if title else None,
                    price.text.strip() if price else None
                )
            )

        return results