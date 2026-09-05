name: Check Cinemark

on:
  schedule:
    # Cada 15 minutos. GitHub puede demorarlo un poco en horas pico, es normal.
    - cron: "*/15 * * * *"
  workflow_dispatch: {}   # permite tirarlo a mano desde la pestaña "Actions"

permissions:
  contents: write   # necesario para poder commitear el archivo state.json

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Cachear navegadores de Playwright
        uses: actions/cache@v4
        with:
          path: ~/.cache/ms-playwright
          key: playwright-${{ runner.os }}-chromium

      - name: Instalar dependencias
        run: |
          pip install requests playwright
          playwright install --with-deps chromium

      - name: Ejecutar chequeo
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python check_cinemark.py

      - name: Guardar estado (commit si cambió)
        run: |
          git config user.name "cinemark-watcher-bot"
          git config user.email "actions@users.noreply.github.com"
          if ! git diff --quiet -- state.json; then
            git add state.json
            git commit -m "Actualiza estado [skip ci]"
            git push
          else
            echo "state.json sin cambios, no hay nada que commitear."
          fi
