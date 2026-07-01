import os
import json
import requests

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
STATE_FILE = "state.json"

# Список товаров для отслеживания: (название страны, ссылка на товар)
PRODUCTS = [
    ("Германия", "https://www.zara.com/de/en/corsetry-inspired-top-with-ruffles-p04661050.html?v1=522584644"),
    ("Испания", "https://www.zara.com/es/en/corsetry-inspired-top-with-ruffles-p04661050.html"),
    ("Португалия", "https://www.zara.com/pt/en/corsetry-inspired-top-with-ruffles-p04661050.html"),
    ("Польша", "https://www.zara.com/pl/pl/top-gorsetowy-z-falbankami-p04661050.html"),
    ("Украина", "https://www.zara.com/ua/uk/топ-корсет-із-воланами-p04661050.html"),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def send_telegram_message(text: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": False}
    r = requests.post(url, data=payload, timeout=15)
    r.raise_for_status()


def is_out_of_stock(html: str) -> bool:
    return "out of stock" in html.lower()


def load_previous_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def check_one(country: str, url: str, state: dict) -> None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print(f"[{country}] Ошибка запроса: {e}")
        return

    out_of_stock_now = is_out_of_stock(resp.text)
    previous = state.get(url, {}).get("out_of_stock")

    if previous is None:
        print(f"[{country}] Первый запуск. Состояние: {'нет в наличии' if out_of_stock_now else 'в наличии'}")
    elif previous is True and out_of_stock_now is False:
        send_telegram_message(f"🎉 [{country}] Товар снова в наличии (появился размер)!\n{url}")
        print(f"[{country}] Отправлено уведомление о поступлении!")
    else:
        print(f"[{country}] Без изменений: {'нет в наличии' if out_of_stock_now else 'в наличии'}")

    state[url] = {"out_of_stock": out_of_stock_now}


def main():
    state = load_previous_state()
    for country, url in PRODUCTS:
        check_one(country, url, state)
    save_state(state)


if __name__ == "__main__":
    main()
