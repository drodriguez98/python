# ⚽ Value Bets Bot

Bot automático de **detección de value bets en fútbol** que scrapea cuotas desde **Pinnacle**, **OddsPortal (Bet365)** y **Oddschecker (Bet365 corners)**, las compara mediante desmarginización y notifica por **Telegram** cuando detecta apuestas con valor esperado positivo.

---

## 🧠 Cómo funciona

El bot usa **Pinnacle** como referencia de probabilidad real, ya que tiene el margen más bajo del mercado (~4–5%) y acepta apuestas de apostadores profesionales. Las cuotas de Pinnacle se **desmarginalizan** para obtener la probabilidad real de cada outcome, y se comparan contra las cuotas de **Bet365**:

```
prob_real_i = (1 / cuota_pinnacle_i) / Σ(1 / cuota_pinnacle_j)
value       = prob_real_i × cuota_bet365_i − 1
```

Si `value ≥ threshold` → value bet. El método de desmarginización es el **multiplicativo** (proporcional), estándar en el sector.

El flujo por iteración es:

1. Detecta los **partidos del día** en Pinnacle y OddsPortal
2. **Empareja** los partidos entre ambas fuentes mediante fuzzy matching
3. Extrae las cuotas de cada mercado activo
4. Para corners, navega a **Oddschecker** para obtener las cuotas de Bet365
5. Desmarginiza Pinnacle, calcula el value y filtra por threshold
6. Guarda resultados en **JSON** y envía notificaciones por **Telegram**

---

## 📊 Mercados soportados

| Key | Mercado | Fuente retail | Por defecto | Threshold |
|---|---|---|---|---|
| `1x2` | Money Line | OddsPortal / Bet365 | ✅ | 3% |
| `dc` | Double Chance | OddsPortal / Bet365 | ✅ | 4% |
| `bts` | Both Teams to Score | OddsPortal / Bet365 | ✅ | 5% |
| `dnb` | Draw No Bet | OddsPortal / Bet365 | ✅ | 4% |
| `ou_goals` | Over/Under goles (1.5–4.5) | OddsPortal / Bet365 | ✅ | 4% |
| `ou_corners` | Over/Under córneres (7.5–11.5) | Oddschecker / Bet365 | ✅ | 5% |
| `ht_ft` | Descanso / Resultado final | OddsPortal / Bet365 | ❌ | 8% |

En todos los mercados, **Pinnacle** actúa como fuente sharp (probabilidad real).

> `ht_ft` no se activa por defecto. Ver sección [Filtrar mercados](#filtrar-mercados).

### Criterio de Kelly

Para cada value bet detectada el bot calcula el tamaño óptimo de apuesta según el **criterio de Kelly**:

```
f* = (p·b − q) / b
```

- `p` = probabilidad real (Pinnacle desmarginizado)
- `b` = beneficio neto por unidad = `cuota_bet365 − 1`
- `q` = `1 − p`

Se reportan dos variantes:

- **Kelly completo** — máximo crecimiento teórico a largo plazo
- **Half-Kelly** — recomendado en la práctica: reduce la varianza a la mitad con una pérdida de crecimiento esperado de solo ~13%

El valor está limitado a un máximo del 25% del bankroll.

### Tratamiento especial de HT/FT

Antes de desmarginalizar el mercado HT/FT se validan dos condiciones:

- Al menos **6 de los 9 outcomes** deben estar disponibles en Pinnacle
- El **margen resultante no puede superar el 15%**

Si no se cumplen ambas, el mercado se descarta para ese partido. Esto evita probabilidades artificialmente infladas cuando Pinnacle no publica los outcomes menos probables.

---

## 🏆 Competiciones soportadas

### Ligas nacionales

**Europa**
- Premier League · La Liga · Serie A · Bundesliga · Ligue 1
- Eredivisie · Primeira Liga · Super Lig · Russia Premier League
- Belgium Pro League · Poland Ekstraklasa · Scottish Premiership
- Austrian Bundesliga · Swiss Super League · Greek Super League
- Danish Superliga · Norway Eliteserien · Swedish Allsvenskan
- Romanian Liga 1 · Czech First League

**América**
- MLS · Liga MX · Argentina Liga Pro · Brasileirao
- Liga de Primera (Chile) · Primera A (Colombia)

**Asia / Oceanía**
- J League · K League · Chinese Super League · A League

### Copas y competiciones continentales

- **Copas domésticas:** FA Cup · Copa del Rey · Coppa Italia · Coupe de France · DFB Pokal · Kings Cup
- **Continentales:** Champions League · Europa League · Conference League · Concacaf · Copa Libertadores · Copa Sudamericana

> Las competiciones sin URL de Oddschecker configurada en `competitions.py` no tendrán corners scrapeados. La URL se añade como tercer elemento opcional de la tupla de cada competición.

---

## 📦 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu_usuario/value-bets-bot.git
cd value-bets-bot
```

### 2. Crear entorno virtual e instalar dependencias

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

pip install playwright beautifulsoup4 lxml requests python-dotenv
playwright install chromium
```

### 3. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```dotenv
TELEGRAM_BOT_TOKEN=<token de @BotFather>
TELEGRAM_CHAT_ID=<tu chat_id>
```

- Token: habla con [@BotFather](https://t.me/BotFather) en Telegram → `/newbot`
- Chat ID: habla con [@userinfobot](https://t.me/userinfobot) en Telegram

> Si no configuras Telegram, el bot funciona igualmente — simplemente omite las notificaciones.

---

## 🚀 Uso

### Modos de ejecución

El bot admite dos modos:

**Ejecución única** — realiza un ciclo completo y termina. Genera un JSON puntual en `output/odds_YYYYMMDD_HHMMSS.json`. Ideal para cron.

```bash
python scraper.py
```

**Bucle continuo** — con `--loop` el bot arranca de nuevo inmediatamente al terminar cada ciclo. Cada iteración queda identificada en los logs. Para detenerlo usa **Ctrl+C**.

```bash
python scraper.py --loop
```

### Seleccionar competiciones

```bash
# Todas las competiciones (por defecto)
python scraper.py

# Una o varias competiciones concretas
python scraper.py -c "La Liga"
python scraper.py -c "La Liga" "Serie A" "Bundesliga"

# Por categoría
python scraper.py --category league_europe
python scraper.py --category domestic_cup continental
```

Categorías disponibles:

| Categoría | Contenido |
|---|---|
| `league_europe` | Ligas nacionales europeas (20) |
| `league_americas` | Ligas nacionales americanas (6) |
| `league_asia` | Ligas nacionales Asia / Oceanía (5) |
| `domestic_cup` | Copas domésticas (6) |
| `continental` | Competiciones continentales UEFA / CONMEBOL (6) |
| `leagues` | Alias — las tres categorías de ligas combinadas (31) |

> `-c` / `--competition` y `--category` son mutuamente excluyentes.

### Filtrar mercados

Por defecto se analizan `1x2`, `dc`, `bts`, `dnb`, `ou_goals` y `ou_corners`. Con `--markets` puedes cambiar la selección:

```bash
python scraper.py --markets 1x2                     # Solo Money Line
python scraper.py --markets 1x2 ou_goals            # Money Line + Over/Under goles
python scraper.py --markets ou_corners              # Solo córneres
python scraper.py --markets ht_ft                   # Defaults + HT/FT
python scraper.py --markets 1x2 ou_goals ht_ft     # Exactamente esa selección
```

> `ht_ft` tiene un comportamiento especial: si se pasa **solo**, se añade a los mercados por defecto. Si se pasa **junto a otros**, se usa exactamente esa selección.
>
> `ou_goals` agrupa Over/Under goles 1.5, 2.5, 3.5 y 4.5. `ou_corners` agrupa Over/Under córneres 7.5, 8.5, 9.5, 10.5 y 11.5. No es posible seleccionarlos individualmente.

### Umbral de value

Por defecto cada mercado tiene su propio threshold (ver tabla de mercados). Con `--threshold` puedes sobreescribirlos todos con un único valor:

```bash
python scraper.py --threshold 0.00   # Ver todas las comparaciones (útil para debug)
python scraper.py --threshold 0.02   # Umbral más permisivo
python scraper.py --threshold 0.05   # Umbral más estricto
```

Para modificar los thresholds por mercado de forma permanente, edita `MARKET_THRESHOLDS` en `src/core/analysis.py`.

### Filtrar por rango de cuota

Con `--min-odd` y `--max-odd` puedes limitar las value bets reportadas a un rango de cuota de Pinnacle:

```bash
python scraper.py --min-odd 1.5                     # Solo cuotas Pinnacle ≥ 1.5
python scraper.py --max-odd 3.0                     # Solo cuotas Pinnacle ≤ 3.0
python scraper.py --min-odd 1.5 --max-odd 3.0       # Rango cerrado
```

> El filtro se aplica sobre la cuota de **Pinnacle**, no sobre la de Bet365. Ten en cuenta que en mercados con cuotas estructuralmente altas como HT/FT, un `--max-odd` bajo puede descartar outcomes válidos.

### Otros flags

```bash
python scraper.py --debug                # Logs detallados
python scraper.py --no-headless         # Mostrar el navegador durante el scraping
python scraper.py --output-dir data     # Carpeta de salida personalizada
python scraper.py --list-competitions   # Listar todas las competiciones disponibles
python scraper.py --list-categories     # Listar categorías y sus competiciones
python scraper.py --list-markets        # Listar mercados disponibles
```

---

## 📁 Formato de salida

### Modo bucle — `session_YYYYMMDD.json`

En modo `--loop` se genera un único archivo JSON por día en `output/`. Si el bot se reinicia durante el mismo día, carga el archivo existente y continúa acumulando desde donde lo dejó.

```json
{
  "date": "2026-03-20",
  "iterations": 4,
  "odds": [ ... ],
  "value_bets": [ ... ],
  "seen_bets": { ... }
}
```

- **`odds`** — última lectura de cuotas por partido y fuente. Se actualiza en cada iteración mediante merge: los campos de la iteración actual se sobreescriben, y los de iteraciones anteriores no presentes en la actual se preservan.
- **`value_bets`** — value bets notificadas durante la sesión. Una entrada por outcome, sobreescrita cuando mejora el EV o la cuota de Bet365.
- **`seen_bets`** — registro de deduplicación. Clave `competition|home|away|market|outcome` con `bet365_odds`, `value`, `first_seen` y `last_seen`.

### Modo ejecución única — `odds_YYYYMMDD_HHMMSS.json`

Genera un JSON puntual con todos los registros de odds de esa ejecución. No hay sesión ni deduplicación.

### Registros por partido

Cada partido genera entre 2 y 3 registros según los mercados activos:

| Fuente | Campos incluidos |
|---|---|
| `pinnacle` | Todos los mercados scrapeados: `m_1x2`, `m_dc`, `m_bts`, `m_dnb`, `m_ou_goals_*`, `m_ou_corners_*`, `m_ht_ft` (si activo) |
| `oddsportal_bet365` | Mercados de goles: `m_1x2`, `m_dc`, `m_bts`, `m_dnb`, `m_ou_goals_*`, `m_ht_ft` (si activo) |
| `oddschecker` | Solo corners: `m_ou_corners_*` |

Los campos que no aplican a cada fuente se omiten del JSON.

### Deduplicación entre iteraciones

En modo `--loop`, una value bet ya notificada solo genera una nueva notificación si ha mejorado de forma significativa respecto a la última vez. Los umbrales mínimos de mejora son:

- **Cuota Bet365**: debe subir al menos **0.05** (ej. de 5.00 a 5.05)
- **EV**: debe subir al menos **1 punto porcentual** (ej. de 8.0% a 9.0%)

Si ninguno supera su umbral, la bet se suprime silenciosamente. Los umbrales se pueden ajustar en `src/core/dedup.py` → `MIN_ODDS_DELTA` y `MIN_VALUE_DELTA`.

### Notificación Telegram

Cada value bet genera un mensaje individual:

```
🔥 Osasuna - Girona
🏆 La Liga · 21:00
📋 Mercado: OU_CORNERS95 → OVER
📌 Pinnacle: 2.10 (prob real: 48.2%)
💰 Bet365: 2.25 (prob impl: 44.4%)
📈 EV: +8.5%
📐 Kelly: 7.8% bankroll (½Kelly: 3.9%)
```

El emoji cambia según el EV: 🔥 para EV ≥ 5%, ✅ para EV < 5%.

---

## ⏰ Automatización

### Bucle continuo (recomendado)

Usa `--loop` y gestiona el proceso con `nohup`, `screen`, `tmux` o un servicio systemd:

```bash
# Segundo plano con nohup
nohup python scraper.py --loop >> logs/bot.log 2>&1 &

# Con salida en pantalla y log simultáneamente
mkdir -p logs && python scraper.py --loop 2>&1 | tee -a logs/bot.log
```

Para detenerlo: `Ctrl+C` si estás en la terminal, o `kill <PID>` si corre en segundo plano.

### Cron (ejecución puntual)

```bash
# Iniciar el demonio cron si no está corriendo
service cron start

# Editar las tareas
crontab -e
```

Ejemplos de configuración:

```bash
# Producción — cada hora, thresholds por mercado por defecto
0 * * * * cd /ruta/value-bets-bot && flock -n /tmp/valuebets.lock venv/bin/python scraper.py >> logs/cron.log 2>&1

# Exploración — cada 10 minutos, threshold 0
*/10 * * * * cd /ruta/value-bets-bot && flock -n /tmp/valuebets.lock venv/bin/python scraper.py --threshold 0.00 >> logs/cron.log 2>&1
```

> El `cd` debe apuntar al directorio raíz del proyecto (donde está `scraper.py`). `flock` evita ejecuciones solapadas si el scraping tarda más de un intervalo. El directorio `logs/` debe existir previamente (`mkdir -p logs`).

---

## 🗂 Estructura del proyecto

```
value-bets-bot/
├── scraper.py                          # Orquestador y entrada CLI
├── requirements.txt
├── .env                                # Credenciales (no subir a git)
├── .env.example                        # Plantilla de variables de entorno
│
├── src/
│   ├── config/
│   │   ├── competitions.py             # Registro de competiciones, URLs y categorías
│   │   └── team_aliases.py             # Aliases de equipos y sufijos a eliminar
│   │
│   ├── core/
│   │   ├── models.py                   # Dataclasses: Odds1x2, OddsDC, OddsBTS, OddsDNB, OddsOU, HtFtSet, MatchOdds, ValueBet
│   │   ├── analysis.py                 # Detección de value bets y MARKET_THRESHOLDS
│   │   ├── dedup.py                    # Deduplicación de value bets entre iteraciones
│   │   ├── telegram.py                 # Formateo y envío de notificaciones Telegram
│   │   └── output.py                   # SessionStore y persistencia JSON
│   │
│   ├── scrapers/
│   │   ├── pinnacle.py                 # Scraping de Pinnacle
│   │   ├── oddsportal.py               # Scraping de OddsPortal / Bet365
│   │   └── oddschecker.py              # Scraping de Oddschecker / Bet365 (corners)
│   │
│   └── utils/
│       ├── parsers.py                  # parse_float
│       ├── matching.py                 # Normalización, fuzzy matching y emparejamiento
│       └── browser.py                  # Helpers de Playwright (contexto, cookies, config)
│
└── output/
    ├── session_20260320.json           # Sesión diaria (loop mode)
    └── odds_20260320_090000.json       # JSON puntual (single run)
```

### Dónde tocar cada cosa

| Necesidad | Archivo |
|---|---|
| Añadir / eliminar una competición | `src/config/competitions.py` |
| Añadir URL de Oddschecker a una competición | `src/config/competitions.py` — tercer elemento de la tupla |
| Añadir o modificar una categoría | `src/config/competitions.py` → `CATEGORIES` |
| Añadir un alias de equipo o sufijo | `src/config/team_aliases.py` |
| Cambiar los thresholds por mercado | `src/core/analysis.py` → `MARKET_THRESHOLDS` |
| Cambiar la lógica de detección de value bets | `src/core/analysis.py` |
| Cambiar la lógica de deduplicación | `src/core/dedup.py` |
| Cambiar el formato o envío de notificaciones Telegram | `src/core/telegram.py` |
| Cambiar el formato de salida JSON | `src/core/output.py` |
| Ajustar selectores rotos de Pinnacle | `src/scrapers/pinnacle.py` |
| Ajustar selectores rotos de OddsPortal | `src/scrapers/oddsportal.py` |
| Ajustar selectores rotos de Oddschecker | `src/scrapers/oddschecker.py` |
| Modificar el fuzzy matching o emparejamiento | `src/utils/matching.py` |
| Modificar la configuración del navegador | `src/utils/browser.py` |

---

## ⚠️ Consideraciones

- **Cambios en el HTML**: las páginas de apuestas actualizan su estructura con frecuencia. Si el scraper deja de funcionar, lo más probable es que haya que actualizar selectores en `src/scrapers/`.
- **Nombres de equipos**: algunos equipos tienen nombres distintos entre fuentes (ej. `Athletic Bilbao` vs `Ath Bilbao`). El bot incluye fuzzy matching y un diccionario de aliases en `src/config/team_aliases.py` que se puede ampliar cuando aparezcan nuevos casos.
- **Corners en Oddschecker**: las URLs de los partidos se construyen automáticamente a partir de los nombres de equipo de Pinnacle. Si un equipo tiene un nombre muy distinto en Oddschecker, la URL puede no encontrar el partido — en ese caso aparecerá un warning en los logs con la URL construida.
- **Reintentos automáticos**: todos los puntos de fallo (carga de liga, carga de partido, cuotas Bet365) incluyen hasta 2 reintentos con 3 segundos de espera entre intentos.
- **Contexto de browser separado**: Oddschecker usa un contexto de Playwright independiente del de Pinnacle/OddsPortal para evitar que Cloudflare detecte el patrón de navegación cross-site.
- Proyecto con fines **educativos y de investigación**. Antes de realizar scraping, revisa los términos de uso de los sitios web.

---

## 🛠 Tecnologías

- **Python 3.9+**
- **Playwright** — automatización del navegador
- **BeautifulSoup + lxml** — parsing HTML
- **Asyncio** — ejecución asíncrona
- **requests** — notificaciones Telegram
- **python-dotenv** — gestión de variables de entorno
