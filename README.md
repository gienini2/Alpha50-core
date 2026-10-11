# Alpha50 IA

[![tests](https://github.com/gienini2/Alpha50-core/actions/workflows/tests.yml/badge.svg)](https://github.com/gienini2/Alpha50-core/actions/workflows/tests.yml)

**Entrenador personal automático que cada mañana lee tu reloj Garmin, decide cuánto
puedes entrenar hoy y, si toca correr, te sube el entreno al reloj.**

Combina un plan de entrenamiento de 12 semanas (Método Fitness Alpha50, peso corporal)
con los datos biométricos de un **Garmin Forerunner 165**. Guarda todo en una base de
datos y habla contigo por **Telegram**.

> 📄 Report técnico / portfolio: [`docs/PORTFOLIO.md`](docs/PORTFOLIO.md)

---

## Qué hace cada día

```
07:00  ⌚ Lee el reloj (Garmin Connect): Body Battery, sueño, VFC, FC reposo, estrés, SpO2, pasos
         │   (si falta algo, te pregunta SOLO eso por Telegram)
         ▼
       🧮 Índice de disposición 0-100  →  semáforo 🟢🟡🟠🔴
         │
         ▼
       💾 Guarda todo en SQLite (métricas, día del plan, actividades, series)
         │
         ▼
       📋 Construye el entreno de hoy según el plan y el semáforo:
            · día de cardio  → 3 opciones (A carrera · B bici · C HIIT) recortadas
            · día de fuerza  → superseries con series recortadas
            · día de descanso / semáforo rojo → descanso
         │
         ▼
       💬 Telegram  →  tú eliges "A"  →  ⌚ sube el workout de carrera a tu Garmin
                                          (calentamiento · tramo continuo · series
                                           con recuperación · vuelta a la calma) y
                                          lo agenda hoy
         │
         ▼
       🔁 Al día siguiente compara lo que tocaba con lo que hiciste de verdad
          (actividades de Garmin) → lo registra solo y te dice la verdad ("la bronca")
```

## Estructura

```
alpha50/
  scheduler.py          Orquestador: cron 07:00 + catch-up, estado de diálogo, comandos Telegram
  agente_metrica.py     Garmin Connect → métricas → índice de disposición → SQLite
  agente_cronologia.py  Semana/día del plan, registro de días, repetición de semana, niveles
  agente_plan.py        Lee el plan (JSON) y devuelve el entreno del día
  agente_decisor.py     Cruza plan + semáforo, recorta el entreno y redacta el mensaje
  garmin_actividades.py Ingesta de actividades/series de Garmin, auto-registro y "bronca"
  history_reader.py     Lectura del historial (solo SELECT) para la API / el agente de Jarvis
  parse_alpha50_pdf.py  PDF del plan semanal → JSON
  gen_hoja_asturias.py  Hoja imprimible de rutina sin material (ReportLab)
  check_fecha.py        Utilidad: ver el registro de un día
connectors/
  garmin_workouts.py    Construye el workout de carrera y lo sube + agenda en Garmin
tests/                  19 tests de la lógica pura (unittest, sin red)
docs/                   Portfolio + esquema de ejemplo del plan
legacy/v0-firebase/     Prototipo serverless de enero 2026 (Firebase + GitHub Actions)
```

## Ejecutar

Alpha50 vive dentro de [Jarvis](https://github.com/gienini2/Jarvis_v3), mi asistente
personal. Allí corre como servicio Windows (**NSSM** `Alpha50Scheduler`) y Jarvis le pasa
los mensajes de Telegram (`alpha50_intent_handler`). También funciona por separado:

```powershell
python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt
copy .env.example .env            # credenciales Garmin + relay de Telegram
# alpha50\alpha50_plan.json: el plan (no se publica; ver docs\alpha50_plan.example.json)

python alpha50\agente_cronologia.py init 1          # arrancar el programa en semana 1
python alpha50\scheduler.py --test                  # simulación con métricas de ejemplo
python alpha50\scheduler.py --comando "alpha50 estado"
python alpha50\scheduler.py                         # modo servicio (07:00 + catch-up)
```

Comandos por Telegram (sin barra): `alpha50 ahora · estado · semana · tendencia ·
nivel <Nivel> [semana] · hecho · parcial [detalle] · no pude`. También entiende
lenguaje natural ("¿qué entreno toca hoy?", "¿cómo va la semana?").

```bash
python -m unittest discover -s tests -v
```

## Datos y privacidad
El repo contiene **solo código**. La base de datos (`alpha50_cronologia.db`), el plan
(`alpha50_plan.json`), la sesión de Garmin (`.garmin_session/`) y el `.env` están en
`.gitignore` y se quedan en el PC.

## Mantenimiento
El código se desarrolla en Jarvis y se copia aquí con
[`scripts/sync_from_jarvis.ps1`](scripts/sync_from_jarvis.ps1), que solo copia código
y pasa los tests.
