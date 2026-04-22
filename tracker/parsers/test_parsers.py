from yandex_market import YandexMarketParser
from dns import DNSParser
from mvideo import MVideoParser


def test_all():
    query = "iphone 13"

    print("\n--- Yandex Market ---")
    print(YandexMarketParser(query).parse())

    print("\n--- DNS ---")
    print(DNSParser(query).parse())

    print("\n--- MVideo ---")
    print(MVideoParser(query).parse())


if __name__ == "__main__":
    test_all()