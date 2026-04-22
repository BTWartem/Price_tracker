import requests
from base import BaseParser


class YandexMarketParser(BaseParser):

    def parse(self):
        url = "https://search.marka.yandex.ru/api/v2/search"

        params = {
            "text": self.query,
            "page": 1,
            "how": "aprice",
            "onstock": 1
        }

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }

        r = requests.get(url, params=params, headers=headers)

        # ❗ защита от падений
        if r.status_code != 200:
            print("Yandex error:", r.status_code)
            return []

        data = r.json()

        results = []

        # структура может меняться → проверяем аккуратно
        products = data.get("data", {}).get("products", [])

        for p in products[:10]:
            results.append(
                self.format_result(
                    p.get("name"),
                    p.get("price", {}).get("value"),
                    p.get("link")
                )
            )

        return results