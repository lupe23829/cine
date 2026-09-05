import json
import os
import re
import sys
import requests

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

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}


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


def get_formatos_disponibles(html):
    """
    Devuelve el texto que aparece entre el encabezado 'Formatos disponibles'
    y el siguiente encabezado ('Duración'). Si está vacío -> todavía no hay
    funciones/horarios cargados. Si tiene contenido -> ya se puede comprar.
    """
    # Sacamos tags para trabajar sobre texto plano, preservando saltos de línea
    text = re.sub(r"<script.*?</script>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", "\n", text)
    text = re.sub(r"\n+", "\n", text)

    match = re.search(
        r"Formatos disponibles\s*\n(.*?)\n\s*Duraci[oó]n",
        text,
        re.S | re.I,
    )
    if not match:
        # No encontramos la sección esperada -> devolvemos None para
        # poder detectarlo como "estructura cambió" y no romper en silencio
        return None

    contenido = match.group(1).strip()
    return contenido


def check_movie(movie):
    resp = requests.get(movie["url"], headers=HEADERS, timeout=30)
    resp.raise_for_status()
    formatos = get_formatos_disponibles(resp.text)
    return formatos


def main():
    state = load_state()
    changed_any = False

    for movie in MOVIES:
        key = movie["url"]
        try:
            formatos = check_movie(movie)
        except Exception as e:
            print(f"Error chequeando {movie['name']}: {e}")
            continue

        if formatos is None:
            print(f"[AVISO] No pude encontrar la sección 'Formatos disponibles' en {movie['name']}. "
                  f"Puede que la página haya cambiado de estructura.")
            continue

        hay_venta_ahora = len(formatos) > 0
        hay_venta_antes = state.get(key, {}).get("hay_venta", False)

        print(f"{movie['name']}: hay_venta_antes={hay_venta_antes} hay_venta_ahora={hay_venta_ahora}")

        if hay_venta_ahora and not hay_venta_antes:
            send_telegram(
                f"🎬 ¡Ya hay funciones/horarios disponibles para comprar!\n\n"
                f"{movie['name']}\n{movie['url']}"
            )
            changed_any = True

        state[key] = {"hay_venta": hay_venta_ahora, "formatos": formatos}

    save_state(state)

    # Código de salida informativo para los logs de Actions (no afecta nada)
    if changed_any:
        print("Se detectaron cambios y se enviaron avisos.")
    else:
        print("Sin cambios.")


if __name__ == "__main__":
    main()
