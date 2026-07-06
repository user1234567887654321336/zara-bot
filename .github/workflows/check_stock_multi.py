import os
import json
import requests

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
STATE_FILE = "state.json"

# Список товаров для отслеживания: (название страны, ссылка на товар)
# Платье ZW Collection Mini Dress, Oyster-white, 2112/258/251
PRODUCTS = [
    ("Германия", "https://www.zara.com/de/en/zw-collection-short-dress-p02112258.html"),
    ("Испания", "https://www.zara.com/es/en/zw-collection-short-dress-p02112258.html"),
    ("Португалия", "https://www.zara.com/pt/en/zw-collection-short-dress-p02112258.html"),
    ("Великобритания", "https://www.zara.com/uk/en/zw-collection-short-dress-p02112258.html"),
    ("Украина", "https://www.zara.com/ua/uk/%D0%BA%D0%BE%D1%80%D0%BE%D1%82%D0%BA%D0%B0-%D1%81%D1%83%D0%BA%D0%BD%D1%8F-zw-collection-p02112258.html?v1=515230994"),
    # Польша, Франция будут добавлены отдельно, когда пришлют ссылки
]

# Фразы "нет в наличии" на разных языках - бот будет искать любую из них
OUT_OF_STOCK_PHRASES = [
    "out of stock",       # английский
    "agotado",             # испанский
    "esgotado",            # португальский
    "épuisé",              # французский
    "épuisée",
    "wyprzedane",          # польский
    "niedostępny",
    "brak w magazynie",
    "esaurito",            # итальянский
    "esaurita",
    "немає в наявності",   # украинский
    "нет в наличии",       # русский (на всякий случай)
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
    lowered = html.lower()
    return any(phrase in lowered for phrase in OUT_OF_STOCK_PHRASES)


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

    html = resp.text
    out_of_stock_now = is_out_of_stock(html)
    previous = state.get(url, {}).get("out_of_stock")

    # Диагностика: показываем длину страницы и короткий отрывок вокруг проверки,
    # чтобы можно было убедиться, что бот реально видит настоящую страницу
    print(f"[{country}] Длина полученной страницы: {len(html)} символов")

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
