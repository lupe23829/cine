# Cinemark Watcher

Avisa por Telegram cuando una película de Cinemark Argentina habilita
sus funciones/horarios para la venta de entradas.

## Cómo funciona

`check_cinemark.py` entra a la(s) URL(s) configuradas, busca la sección
"Formatos disponibles" de la página. Cuando está vacía, todavía no hay
funciones cargadas; cuando tiene contenido, ya se puede comprar. El estado
anterior se guarda en `state.json` para comparar y avisar solo en el
momento en que pasa de "sin venta" a "con venta".

## Pasos para dejarlo andando

1. **Subí esta carpeta a un repo de GitHub** (puede ser público, así no
   consume minutos de Actions).

2. **Cargá los secrets** en el repo:
   - Andá a `Settings` → `Secrets and variables` → `Actions` → `New repository secret`.
   - Creá `TELEGRAM_BOT_TOKEN` con el token que te dio @BotFather.
   - Creá `TELEGRAM_CHAT_ID` con tu chat ID (el que ya conseguiste).

3. **Habilitá permisos de escritura para Actions**:
   - `Settings` → `Actions` → `General` → `Workflow permissions` →
     elegí **"Read and write permissions"** y guardá.
     (Esto es necesario para que el workflow pueda commitear `state.json`).

4. **Agregá las películas que quieras vigilar** editando la lista `MOVIES`
   dentro de `check_cinemark.py`.

5. Probalo manualmente: pestaña **Actions** → **Check Cinemark** →
   **Run workflow**. Mirá los logs para confirmar que detecta bien
   "Formatos disponibles" (si dice que no encuentra la sección, avisame
   y ajustamos el patrón de búsqueda).

6. Una vez que ande bien manual, el cron (`*/15 * * * *`) lo va a correr
   solo cada 15 minutos.

## Si la página cambia de estructura

Si en algún momento el script empieza a decir en los logs
"No pude encontrar la sección 'Formatos disponibles'...", probablemente
Cinemark cambió el HTML de la página. Pasame el error y ajustamos el
regex en `get_formatos_disponibles`.
