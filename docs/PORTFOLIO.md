# Alpha50 IA — Entrenador personal automático con Garmin (report técnico / portfolio)

Proyecto personal en producción diaria: un **coach de entrenamiento autónomo** que cada
mañana lee los datos biométricos de un reloj **Garmin**, los guarda en una base de datos,
**construye el entreno del día** a partir de un plan de 12 semanas ajustándolo a la
recuperación real del usuario y, si toca correr, **sube el entrenamiento al reloj**. Todo
por Telegram.

---

## 1. Resumen ejecutivo
Alpha50 IA convierte un plan de entrenamiento en PDF (Método Fitness Alpha50, 12 semanas
a peso corporal) en un **entrenador que se adapta cada día**. A las 07:00 descarga de
**Garmin Connect** Body Battery, puntuación de sueño, VFC, FC en reposo, estrés y SpO2,
calcula un **índice de disposición 0-100** con semáforo 🟢🟡🟠🔴, lo persiste en
**SQLite** y genera el entreno de hoy recortando series, ciclos o minutos según el
semáforo. Lo manda por **Telegram**; si el usuario elige carrera, construye un
**workout estructurado** (calentamiento, tramo continuo, series con recuperación, vuelta
a la calma) y lo **sube y agenda en el reloj**. Al día siguiente compara lo planificado
con las actividades reales de Garmin, registra el día solo y le dice al usuario
honestamente si cumplió. Corre como servicio Windows integrado en mi asistente
[Jarvis](https://github.com/gienini2/Jarvis_v3).

---

## 2. Qué es y qué resuelve
- **El problema**: un plan de entrenamiento en PDF es fijo. No sabe si has dormido mal,
  si tienes la batería baja o si ayer no entrenaste. Seguirlo a ciegas lleva a
  sobreentrenar o a abandonar. Además hay que copiar los datos del reloj a mano y apuntar
  lo que se hace.
- **La solución**: un sistema que **lee el reloj solo**, decide **cuánto** entrenar hoy
  con reglas explícitas y auditables, te da la sesión ya calculada y te la **pone en el
  reloj**. Lleva la cronología del plan sin intervención: si un día no entrenas, la
  semana se repite.
- **Para quién**: uso personal (yo soy el usuario cero). El objetivo era preparar unas
  pruebas físicas, donde **no forzar en días malos** (fatiga, mal sueño, molestias) era
  tan importante como no saltarse los buenos.
- **Evolución**: v0 (enero 2026) era un prototipo *serverless* con **Firebase + GitHub
  Actions** y datos introducidos a mano (2.182 ejecuciones programadas antes de
  retirarse). La v1 (julio 2026 en adelante) se rehízo desde cero: Garmin automático,
  SQLite local, cuatro agentes y servicio Windows. La v0 se conserva en
  `legacy/v0-firebase/`.

---

## 3. Funcionalidades

### Lectura automática del reloj (Garmin Connect)
- Descarga diaria de **Body Battery al despertar** (valor de despertar o pico del día,
  nunca el valor "actual", que arrastra el residuo de ayer), **puntuación de sueño**
  (con horas, fases profunda/REM), **VFC** (valor nocturno y *estado* relativo a tu
  línea base), **FC en reposo**, **estrés medio**, **SpO2 nocturno**, pasos y calorías
  activas.
- **Detección de noche sin sincronizar**: si aún no hay puntuación de sueño, descarta
  también el Body Battery para no usar un valor viejo.
- **Datos parciales**: si a Garmin le falta alguna métrica, pide por Telegram **solo
  las que faltan**, en orden (`80 / bajo / 54`), y las fusiona con lo descargado
  (fuente `garmin+manual`).
- **Modo manual completo** si Garmin está caído y no hay caché utilizable.

### Índice de disposición y semáforo
- Índice ponderado 0-100: **Body Battery 35 % · sueño 25 % · VFC 20 % · FC reposo 10 % ·
  estrés 10 %**, con valores neutros cuando falta un dato.
- Prioriza el **estado VFC** de Garmin (relativo a la persona) sobre el valor absoluto en
  ms, que no es comparable entre personas.
- Semáforo: 🟢 ≥75 completo · 🟡 50-74 reducido · 🟠 30-49 muy suave · 🔴 <30 descanso
  activo.

### Base de datos (todo queda guardado)
- **SQLite con 7 tablas**: `metricas_diarias` (biometría + índice + semáforo + fuente),
  `historial_dias` (qué tocaba y qué se hizo), `estado_programa` (nivel, semana, inicio),
  `garmin_actividades` (cada actividad con su **JSON crudo completo** y columnas
  parseadas: distancia, FC media/máx., VO2max, *training effect*), `garmin_sets` (series
  y repeticiones de las sesiones de fuerza), `alpha50_sesion` (estado del diálogo) y
  `matutino_runs` (marcador de ejecución diaria).
- Deduplicación por `activityId` y migraciones de esquema en caliente (`ALTER TABLE`
  si falta una columna).

### Construcción del entreno del día
- **Cronología del plan**: semana y día actuales, calendario semanal por nivel
  (p. ej. L/X/S cardio · M/V fuerza · J/D descanso; calendarios propios para
  PrePrincipiante y Avanzado), progresión automática de semana y de **nivel** (6 niveles
  definidos, de PrePrincipiante a Gladiador).
- **Regla de repetición**: una semana solo avanza si **todos** sus días de entreno
  constan como hechos; un día sin registrar cuenta como no hecho y la semana se repite.
- **Según toque carrera o no**:
  - **Día de cardio** → tres opciones: **A) carrera · B) bici · C) HIIT** (o *power
    walking* en Principiante). En 🟡 quita 2 series por bloque, recorta el tramo continuo
    un 20 %, quita 1 ciclo de HIIT y suma 10" de descanso. En 🟠 elimina el segundo bloque
    de series o lo cambia por 20' suaves.
  - **Día de fuerza** → superseries torso + pierna; en 🟡 quita 1 serie por ejercicio
    (`3x10, antes 4`), en 🟠 deja 2 series y solo las primeras superseries.
  - **Sesiones por bloques** (anaeróbico, dominadas) para niveles avanzados.
  - **Descanso planificado** o **descanso forzado** en 🔴, aunque toque entrenar.
- El recorte se mantiene coherente entre el resumen y el detalle de la opción elegida.

### Subida del entreno al reloj
- Al responder **"A" (carrera)**, convierte la sesión del plan (`10'`, `5x100m // 5x20"`,
  `1'30"`) en un **workout de Garmin estructurado**: calentamiento, intervalo continuo,
  **grupo de repetición** (trabajo + recuperación) con el nº de series **ya recortado por
  el semáforo**, y vuelta a la calma. Lo **sube y lo agenda para hoy** en Garmin Connect,
  así aparece en el reloj.
- Reutiliza la sesión Garmin ya autenticada (sin login extra) y nunca rompe el flujo: si
  falla, avisa y el plan sigue.

### Seguimiento real y "la bronca"
- **Ingesta diaria de actividades** (14 días) con series y repeticiones de fuerza.
- **Auto-registro con modelo de 3 estados**: actividad que encaja con el tipo de día →
  `completado`; actividad de otro tipo (correr en día de fuerza) → `otro`, que **no**
  completa la semana; sin actividad → sin registrar. Nunca pisa un registro manual.
- **"La bronca"**: mensaje del día siguiente que compara lo que tocaba con lo que hiciste
  ("tocaba fuerza y en su lugar hiciste correr 5.2 km…").
- **Repaso semanal**: km, FC media, VO2max, *training effect*, series activas y volumen,
  comparando el periodo actual con el anterior.

### Conversación por Telegram
- Comandos sin barra: `alpha50 ahora · estado · semana · tendencia · nivel <Nivel>
  [semana] · hecho · parcial [detalle] · no pude · debug`.
- **Lenguaje natural**: "¿qué entreno toca hoy?", "¿cómo va la semana?", "¿en qué nivel
  estoy?".
- **Máquina de estados del diálogo** (esperando métricas / opción de cardio /
  confirmación) **persistida en BD**, para responder desde otro proceso.
- Tendencia de 7 días: disposición media, Body Battery medio, FC reposo y variación de
  peso.

### Generación de documentos
- **Parser de PDF → JSON** del plan semanal (`pypdf` + regex), que normaliza la fuerza a
  pares torso/pierna.
- **PDF con ReportLab**: hoja imprimible de rutina sin material (para entrenar fuera de
  casa).

### Operación y fiabilidad
- Servicio Windows (**NSSM**) con **catch-up**: si el PC arranca después de las 07:00,
  lanza el flujo del día; si el envío falla (red o VPN aún no levantadas), reintenta cada
  30 s hasta conseguirlo, sin duplicar.
- **Caché de la última lectura válida** (≤3 días) como respaldo si Garmin no responde.
- Integrado en **Jarvis**: los mensajes de Telegram pasan primero por
  `alpha50_intent_handler`, el agente LLM de Jarvis puede consultar el historial
  (`query_alpha50_history`) y la UI web tiene una pestaña con el estado y el historial
  (`GET /results/alpha50`).

---

## 4. Cómo funciona (arquitectura)
```
                ⌚ Garmin Forerunner 165
                        │ sync
                        ▼
                 Garmin Connect (API no oficial, garminconnect)
                  ▲                     │ métricas + actividades + series
     workout      │                     ▼
     estructurado │      ┌───────────────────────────────────────────────┐
     + agenda     │      │  Alpha50Scheduler (servicio NSSM, PC Windows) │
                  │      │  07:00 + catch-up cada 30 s                   │
                  │      │                                               │
                  │      │  agente_metrica ──► índice 0-100 + semáforo   │
                  │      │        │                                      │
                  │      │        ▼                                      │
                  │      │  SQLite alpha50_cronologia.db  (7 tablas, WAL)│
                  │      │        ▲            │                         │
                  │      │  agente_cronologia  │  agente_plan (plan JSON)│
                  │      │  (semana/día/nivel) ▼                         │
                  │      │           agente_decisor                      │
                  │      │   (recorta series/ciclos/minutos y redacta)   │
                  │      │        │                  garmin_actividades  │
                  │      │        │                  (auto-registro +    │
                  │      │        │                   bronca diaria)     │
                  └──────┼── connectors/garmin_workouts ◄── "A" carrera  │
                         └────────┼──────────────────────────────────────┘
                                  │ POST /notify (X-Relay-Key)
                                  ▼
                 Relay Telegram (servidor Debian, systemd) ◄──── Tailscale
                                  │                                │
                                  ▼                                │
                             📱 Telegram ── respuestas ──► Jarvis API (FastAPI :3000)
                                                         └► alpha50_intent_handler
```
- **Arquitectura de agentes especializados** (métrica, cronología, plan y decisor),
  cada uno con su responsabilidad, su CLI de pruebas y sus tablas.
- **Reglas deterministas** en vez de un LLM para la decisión: el ajuste de cada semáforo
  es una tabla explícita (`AJUSTES`), auditable y reproducible.
- **Dos procesos, un estado**: el scheduler y la API de Jarvis comparten la misma
  SQLite en modo **WAL** con `busy_timeout`. El estado del diálogo vive en la BD, no en
  memoria.

---

## 5. Stack tecnológico

**Lenguajes:** Python 3.11, SQL (SQLite), PowerShell, YAML (GitHub Actions), JSON.

**Backend / servicios:** procesos Python de larga duración, `schedule` (planificación
diaria), `threading` (decisor asíncrono para no bloquear la respuesta), `argparse`
(CLIs de prueba por agente), integración como módulo en una API **FastAPI** (Jarvis:
endpoint `/results/alpha50` e *intent handler*).

**IA / lógica de decisión:** motor de **reglas deterministas** y **puntuación ponderada
multivariable** (índice de disposición). **No usa LLMs** para decidir el entreno. Se
integra en un asistente con agente LLM de *tool-calling* (Jarvis), que lo consulta como
herramienta. *(El nombre "IA" se refiere al sistema adaptativo, no a un modelo de ML.)*

**Datos:** **SQLite** (7 tablas, modo WAL, `busy_timeout`, `INSERT OR REPLACE`,
migración de esquema en caliente), almacenamiento del **JSON crudo** de Garmin para no
perder métricas, plan de entrenamiento como **JSON jerárquico** nivel → semana → día.
v0: **Firebase Realtime Database** (`firebase-admin`).

**Integraciones / APIs externas:**
- **Garmin Connect** vía `garminconnect` (API no oficial): estadísticas diarias, Body
  Battery, sueño, VFC, SpO2, actividades, series de fuerza, **creación, subida y agenda
  de workouts** (`RunningWorkout`, `create_repeat_group`, `schedule_workout`), sesión
  OAuth persistida (*tokenstore*).
- **Telegram Bot API** (a través de un relay propio con `/notify` autenticado; en v0,
  `sendMessage` + `getUpdates` con offset).
- `requests` (HTTP), `python-dotenv` (configuración).

**Documentos:** `pypdf` (extracción de texto del PDF del plan + regex), **ReportLab**
(generación de PDF maquetado: tablas, estilos, plantilla de página).

**Infra / DevOps:** Windows 11 + **NSSM** (servicio `Alpha50Scheduler`), **Tailscale**
(VPN mesh PC ↔ servidor), servidor **Debian** con **systemd** para el relay de Telegram,
**GitHub Actions** (v0: cron *serverless*; v1: CI de tests), **Flask** (webhook de la
v0, preparado para Cloud Run), **git**.

**Seguridad:** secretos fuera del repo (`.env`, `.gitignore` para BD, plan y sesión de
Garmin), autenticación del relay por cabecera `X-Relay-Key`, persistencia de tokens OAuth
en lugar de credenciales en cada arranque, GitHub Secrets (v0).

**Calidad:** `unittest` (27 tests de la lógica pura: índice, recortes, parseo de
workouts y cronología sobre BD temporal) y CI en GitHub Actions.

**Otras libs (stdlib):** `sqlite3`, `re`, `datetime`, `json`, `threading`, `argparse`,
`tempfile`.

---

## 6. Retos técnicos resueltos
- **Rate-limit 429 de Garmin**: el login completo en cada arranque hacía que Garmin
  bloqueara la IP. Lo resolví **persistiendo la sesión OAuth** (*tokenstore*) y
  reanudándola sin volver a autenticar, con **reintentos y *backoff* exponencial**
  (20 s, 40 s, 80 s) solo ante 429 y una **caché de la última lectura válida** como
  último recurso.
- **Datos fiables de una API no oficial**: el Body Battery "más reciente" daba 17 en vez
  de 78 cuando la noche no había sincronizado (arrastraba la batería gastada de ayer).
  Ahora solo uso valores de despertar o el pico del día e invalido el Body Battery si aún
  no hay puntuación de sueño. Así el sistema **pregunta en vez de inventar**.
- **Del plan al reloj**: traducir cadenas humanas del PDF (`5x100m // 5x20"`, `1'30"`)
  a un **workout estructurado de Garmin** con grupos de repetición, aplicando el recorte
  del semáforo antes de subirlo.
- **Lógica de calendario correcta**: un bug hacía avanzar la semana aunque no se
  entrenara (solo se miraban los días marcados como "saltado"). Lo reescribí para que un
  día de entreno **sin registro** cuente como no hecho. El estado `otro` (entrenar algo
  distinto a lo planificado) también queda fuera para no maquillar el progreso.
- **Concurrencia entre procesos**: scheduler y API escriben en la misma SQLite. Lo
  resolví con **WAL + `busy_timeout`** y moviendo la máquina de estados del diálogo a la
  BD, para que una pregunta lanzada por un proceso se pueda responder desde otro.
- **Robustez operativa en un PC doméstico**: *catch-up* si el PC enciende tarde,
  reintento hasta que la VPN esté lista sin duplicar envíos (marcador diario) y salida
  UTF-8 forzada para que los emojis no tumben el servicio con la consola cp1252 de NSSM.

---

## 7. Escala del proyecto
- **v1**: 10 módulos Python + 1 conector · **~3.900 líneas** · **120 funciones** ·
  **7 tablas** SQLite · 15 commits específicos dentro del monorepo de Jarvis
  (julio–septiembre 2026).
- **Datos por día**: ~12 métricas biométricas + actividades con JSON crudo completo y
  series de fuerza.
- **Plan**: estructura de 6 niveles × 12 semanas (8 en PrePrincipiante) × 7 días, con 3
  calendarios semanales distintos.
- **Interfaz**: 9 comandos de Telegram + intenciones en lenguaje natural; 5 estados de
  diálogo.
- **Calidad**: 27 tests automatizados y CI.
- **v0**: 35 commits y **2.182 ejecuciones** programadas en GitHub Actions
  (enero–marzo 2026).
- **Usuarios**: 1 (uso personal diario desde julio de 2026).

---

## 8. Bullets listos para el CV
- **Diseñé y construí un entrenador personal autónomo** en Python que cada mañana
  **lee los datos biométricos de un reloj Garmin**, calcula un índice de recuperación
  ponderado (0-100) y **adapta automáticamente** un plan de 12 semanas (series, ciclos y
  minutos) según un semáforo de 4 niveles.
- **Integré la API de Garmin Connect en los dos sentidos**: descarga diaria de 12
  métricas y de actividades (con series de fuerza) a **SQLite**, y **generación,
  subida y agenda de workouts estructurados** directamente en el reloj del usuario.
- **Resolví el bloqueo por *rate-limit* (429)** de Garmin persistiendo la sesión OAuth,
  con *backoff* exponencial y caché de respaldo, y corregí lecturas erróneas de la API
  no oficial validando la sincronización nocturna.
- **Implementé una arquitectura de 4 agentes especializados** con estado compartido en
  SQLite (WAL) entre dos procesos, una **máquina de estados conversacional por Telegram**
  y **auto-registro del cumplimiento** (planificado frente a real) sin intervención
  manual.
- **Migré un prototipo *serverless*** (Firebase + GitHub Actions, 2.182 ejecuciones) a un
  **servicio Windows autoalojado** (NSSM + Tailscale + relay en Debian) integrado en mi
  asistente de IA, con *catch-up*, reintentos y 27 tests en CI.

**Tecnologías (una línea):** Python · SQLite · Garmin Connect API (garminconnect) ·
Telegram Bot API · schedule · threading · pypdf · ReportLab · requests · python-dotenv ·
NSSM · Windows services · Tailscale · Debian/systemd · FastAPI (integración) · Firebase
Realtime Database · Flask · GitHub Actions · unittest · PowerShell · git.
