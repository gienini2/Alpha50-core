# Alpha50 v0 — prototipo serverless (enero–marzo 2026)

Primera versión de Alpha50, **retirada**. Se conserva como histórico de la evolución
del proyecto. La versión actual (v1) está en la raíz del repo.

## Qué hacía
- **GitHub Actions como scheduler** (`workflow/agent.yml`): cron a las 07:30, a las
  20:00 y cada 5 min para leer Telegram. **2.182 ejecuciones** registradas entre
  enero y marzo de 2026.
- `src/agent.py`: saludo matutino por Telegram pidiendo *peso / Body Battery / sueño*
  (entrada **manual**), long-polling con `getUpdates` y offset persistido, parseo con
  regex y clasificación del estado fisiológico (ÓPTIMO / MEDIO / BAJO) → "entrenar" o
  "descanso" según el día.
- **Firebase Realtime Database** (`firebase-admin`) como almacén: `estado`,
  `fisiologia/<fecha>`, `sistema/control`, `sistema/telegram`.
- `main.py`: webhook mínimo en **Flask** pensado para Cloud Run (`PORT` por entorno).
- `data/src/registrar_sensaciones.py`: registro por consola de sensaciones y dolor por
  zona a JSON.

## Por qué se sustituyó
Datos introducidos a mano, sin lectura del reloj, sin plan de entreno real detrás
(solo "entrena / descansa") y un cron cada 5 min para simular un chat. La v1 lee
Garmin directamente, guarda todo en SQLite, construye el entreno del día desde el plan
y lo ajusta según tu recuperación.

> El workflow se movió a `workflow/agent.yml` (fuera de `.github/`) para que no vuelva
> a ejecutarse.
