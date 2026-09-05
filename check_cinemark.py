import json
import os
import re
import requests
from playwright.sync_api import sync_playwright

# -----------------------------------------------------------------
# CONFIGURACIÓN: agregá acá todas las películas que quieras vigilar
# -----------------------------------------------------------------
MOVIES = [
    {
        "name": "OASIS: DON'T LOOK BACK IN ANGER",
        "url": "https://www.cinemark.com.ar/pelicula/oasis-don-t-look-back-in-anger",
    },
    # Podés agregar más así:
    # {
    #     "name": "OTRA PELICULA",
    #     "url": "https://www.cinemark.com.ar/pelicula/otra-pelicula",
    # },
]

STATE_FILE = "state.json"

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def send_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID como secrets/env vars")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    resp = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "disable_web_page_preview": False,
        },
        timeout=20,
    )
    if not resp.ok:
        print("Error enviando mensaje a Telegram:", resp.status_code, resp.text)


def get_formatos_disponibles(visible_text):
    """
    Busca, en el texto VISIBLE de la página ya renderizada por el navegador,
    el contenido entre 'Formatos disponibles' y 'Duración'.
    Vacío -> todavía no hay funciones cargadas.
    Con contenido -> ya se puede comprar.
    """
    match = re.search(
        r"Formatos disponibles\s*\n?\s*(.*?)\s*\n\s*Duraci[oó]n",
        visible_text,
        re.S | re.I,
    )
    if not match:
        return None
    return match.group(1).strip()


def check_movie(page, movie):
    page.goto(movie["url"], wait_until="networkidle", timeout=45000)
    # Esperamos un toque extra por si el contenido tarda en hidratar
    page.wait_for_timeout(2000)
    visible_text = page.inner_text("body")
    return get_formatos_disponibles(visible_text)


def main():
    state = load_state()
    changed_any = False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        for movie in MOVIES:
            key = movie["url"]
            try:
                formatos = check_movie(page, movie)
            except Exception as e:
                print(f"Error chequeando {movie['name']}: {e}")
                continue

            if formatos is None:
                print(
                    f"[AVISO] No pude encontrar la sección 'Formatos disponibles' en "
                    f"{movie['name']}. Puede que la página haya cambiado de estructura."
                )
                continue

            hay_venta_ahora = len(formatos) > 0
            hay_venta_antes = state.get(key, {}).get("hay_venta", False)

            print(
                f"{movie['name']}: hay_venta_antes={hay_venta_antes} "
                f"hay_venta_ahora={hay_venta_ahora} (formatos='{formatos}')"
            )

            if hay_venta_ahora and not hay_venta_antes:
                send_telegram(
                    f"🎬 ¡Ya hay funciones/horarios disponibles para comprar!\n\n"
                    f"{movie['name']}\n{movie['url']}"
                )
                changed_any = True

            state[key] = {"hay_venta": hay_venta_ahora, "formatos": formatos}

        browser.close()

    save_state(state)

    if changed_any:
        print("Se detectaron cambios y se enviaron avisos.")
    else:
        print("Sin cambios.")


if __name__ == "__main__":
    main()
