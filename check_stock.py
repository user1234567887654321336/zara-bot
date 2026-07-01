import os
import json
import requests

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
PRODUCT_URL = os.environ.get(
    "PRODUCT_URL",
    "https://www.zara.com/de/en/corsetry-inspired-top-with-ruffles-p04661050.html?v1=522584644",
)
STATE_FILE = "state.json"

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
    return {"out_of_stock": None}


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def main():
    state = load_previous_state()

    resp = requests.get(PRODUCT_URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    out_of_stock_now = is_out_of_stock(resp.text)

    if state.get("out_of_stock") is None:
        print(f"Первый запуск. Текущее состояние: {'нет в наличии' if out_of_stock_now else 'в наличии'}")
    elif state["out_of_stock"] is True and out_of_stock_now is False:
        send_telegram_message(f"🎉 Товар снова в наличии (появился размер)!\n{PRODUCT_URL}")
        print("Отправлено уведомление о поступлении!")
    else:
        print(f"Без изменений: {'нет в наличии' if out_of_stock_now else 'в наличии'}")

    state["out_of_stock"] = out_of_stock_now
    save_state(state)


if __name__ == "__main__":
    main()
