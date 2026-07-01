import os
import time
import re
import requests

# ==== НАСТРОЙКИ (берутся из переменных окружения на Render) ====
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
PRODUCT_URL = os.environ.get(
    "PRODUCT_URL",
    "https://www.zara.com/de/en/corsetry-inspired-top-with-ruffles-p04661050.html?v1=522584644",
)
CHECK_INTERVAL_SECONDS = int(os.environ.get("CHECK_INTERVAL_SECONDS", "300"))  # 5 минут

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
    try:
        r = requests.post(url, data=payload, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"[!] Не удалось отправить сообщение в Telegram: {e}")


def is_out_of_stock(html: str) -> bool:
    """
    Возвращает True, если товар полностью распродан (нет ни одного размера),
    и False, если хотя бы что-то есть в наличии.
    """
    lowered = html.lower()
    # Zara показывает явный текст "OUT OF STOCK" на странице товара, когда всё распродано
    if "out of stock" in lowered:
        return True
    return False


def check_once(previous_state: dict) -> dict:
    try:
        resp = requests.get(PRODUCT_URL, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print(f"[!] Ошибка запроса к Zara: {e}")
        return previous_state

    html = resp.text
    out_of_stock_now = is_out_of_stock(html)

    if previous_state.get("out_of_stock") is None:
        # Первая проверка — просто запоминаем состояние, не шлём уведомление
        print(f"[i] Стартовое состояние: {'нет в наличии' if out_of_stock_now else 'в наличии'}")
    elif previous_state["out_of_stock"] is True and out_of_stock_now is False:
        # Было "нет в наличии" -> стало "есть в наличии" — вот оно!
        send_telegram_message(
            f"🎉 Товар снова в наличии (появился размер)!\n{PRODUCT_URL}"
        )
        print("[+] Отправлено уведомление о поступлении!")
    else:
        print(f"[i] Без изменений: {'нет в наличии' if out_of_stock_now else 'в наличии'}")

    previous_state["out_of_stock"] = out_of_stock_now
    return previous_state


def main():
    print("Бот запущен. Слежу за товаром:")
    print(PRODUCT_URL)
    send_telegram_message("✅ Бот запущен и начал следить за товаром.\n" + PRODUCT_URL)

    state = {"out_of_stock": None}
    while True:
        state = check_once(state)
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
