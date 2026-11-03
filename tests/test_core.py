"""
Tests de la lógica pura de Alpha50 (sin red, sin Garmin, sin Telegram).

Ejecutar desde la raíz del repo:
    python -m unittest discover -s tests -v

Solo usa la librería estándar: los módulos probados no importan dependencias
externas a nivel de módulo (garminconnect se importa dentro de las funciones).
"""
import os
import sqlite3
import sys
import tempfile
import unittest
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "alpha50"))   # imports planos entre agentes
sys.path.insert(0, ROOT)                            # connectors.*, alpha50.*

import agente_cronologia as cron          # noqa: E402
import agente_decisor as decisor          # noqa: E402
import agente_metrica as metrica          # noqa: E402
from connectors import garmin_workouts as gw  # noqa: E402


class TestIndiceDisposicion(unittest.TestCase):
    def test_pesos_suman_100(self):
        self.assertEqual(sum(metrica.PESOS.values()), 100)

    def test_dia_excelente_es_verde(self):
        r = metrica.calcular_indice({
            "body_battery": 95, "sueno_score": 90, "hrv_status": "balanced",
            "fc_reposo": 52, "estres_promedio": 20,
        })
        self.assertEqual(r["semaforo"], "verde")
        self.assertGreaterEqual(r["indice"], metrica.UMBRALES["verde"])

    def test_dia_malo_es_rojo(self):
        r = metrica.calcular_indice({
            "body_battery": 10, "sueno_score": 15, "hrv_status": "poor",
            "fc_reposo": 98, "estres_promedio": 80,
        })
        self.assertEqual(r["semaforo"], "rojo")
        self.assertLess(r["indice"], metrica.UMBRALES["naranja"])

    def test_sin_datos_no_revienta_y_da_neutro(self):
        # Claves presentes con None (Garmin parcial) -> valores neutros, sin TypeError
        r = metrica.calcular_indice({"body_battery": None, "horas_sueno": None,
                                     "fc_reposo": None, "estres_promedio": None})
        self.assertIn(r["semaforo"], ("amarillo", "naranja"))
        self.assertTrue(0 <= r["indice"] <= 100)

    def test_estado_vfc_manda_sobre_valor_absoluto(self):
        base = {"body_battery": 70, "sueno_score": 70, "fc_reposo": 60, "estres_promedio": 30}
        con_estado = metrica.calcular_indice({**base, "hrv_status": "poor", "hrv_valor": 90})
        self.assertEqual(con_estado["puntos"]["hrv"], 20)

    def test_campos_faltantes(self):
        faltan = metrica._campos_faltantes({"body_battery": 80, "sueno_score": 75})
        self.assertEqual(faltan, ["hrv", "fc_reposo", "peso"])


class TestAjustesDecisor(unittest.TestCase):
    def test_series_musculacion(self):
        self.assertEqual(decisor._ajustar_series_muscu("Flexión (4x10)", 1),
                         "Flexión (3x10, antes 4)")
        self.assertEqual(decisor._ajustar_series_muscu("Flexión (4x10)", 0),
                         "Flexión (4x10)")
        # Nunca baja de 1 serie
        self.assertEqual(decisor._ajustar_series_muscu("Flexión (2x10)", 5),
                         "Flexión (1x10, antes 2)")

    def test_series_cardio(self):
        self.assertEqual(decisor._ajustar_series_cardio('6x200m // 6x50"', 2),
                         '4x200m // 4x50"')

    def test_ratio_hiit(self):
        self.assertEqual(decisor._ajustar_ratio_hiit('40" / 30"', 10), '40" / 40"')

    def test_tabla_ajustes_coherente(self):
        for sem in ("verde", "amarillo", "naranja"):
            self.assertIn(sem, decisor.AJUSTES)
        self.assertGreater(decisor.AJUSTES["verde"]["factor_tiempo"],
                           decisor.AJUSTES["naranja"]["factor_tiempo"])


class TestParseoGarminWorkout(unittest.TestCase):
    def test_a_segundos(self):
        self.assertEqual(gw._a_segundos("10'"), 600)
        self.assertEqual(gw._a_segundos("1'30\""), 90)
        self.assertEqual(gw._a_segundos('20"'), 20)
        self.assertEqual(gw._a_segundos("", 45), 45)

    def test_parse_series(self):
        self.assertEqual(gw._parse_series('5x100m // 5x20"'), (5, 20))
        self.assertIsNone(gw._parse_series(""))


class TestCronologia(unittest.TestCase):
    """Calendario, registro de días y regla de 'semana incompleta se repite'."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._orig = cron.DB_PATH
        cron.DB_PATH = os.path.join(self.tmp.name, "test.db")
        cron.init_db()
        # Lunes de hace dos semanas como inicio del programa
        hoy = date.today()
        self.lunes = hoy - timedelta(days=hoy.weekday()) - timedelta(weeks=2)
        cron.iniciar_programa("Intermedio", 1, self.lunes)

    def tearDown(self):
        cron.DB_PATH = self._orig
        self.tmp.cleanup()

    def _dias_entreno(self):
        return [dow for dow, m in cron.SEMANA_ALPHA50.items() if m["tipo"] != "descanso"]

    def test_estado_hoy_basico(self):
        est = cron.get_estado_hoy(self.lunes)
        self.assertEqual(est["nivel"], "Intermedio")
        self.assertEqual(est["semana_plan"], 1)
        self.assertEqual(est["tipo"], "cardio")      # lunes = cardio
        self.assertFalse(est["ya_registrado"])

    def test_semana_sin_entrenar_se_repite(self):
        # Nada registrado en la semana 1 -> el lunes siguiente sigue siendo semana 1
        est = cron.get_estado_hoy(self.lunes + timedelta(weeks=1))
        self.assertEqual(est["semana_plan"], 1)

    def test_semana_completa_avanza(self):
        for dow in self._dias_entreno():
            cron.registrar_dia("completado", hoy=self.lunes + timedelta(days=dow))
        est = cron.get_estado_hoy(self.lunes + timedelta(weeks=1))
        self.assertEqual(est["semana_plan"], 2)

    def test_estado_otro_no_completa_semana(self):
        dias = self._dias_entreno()
        for dow in dias[:-1]:
            cron.registrar_dia("completado", hoy=self.lunes + timedelta(days=dow))
        cron.registrar_dia("otro", hoy=self.lunes + timedelta(days=dias[-1]))
        est = cron.get_estado_hoy(self.lunes + timedelta(weeks=1))
        self.assertEqual(est["semana_plan"], 1)

    def test_estado_invalido(self):
        self.assertIn("error", cron.registrar_dia("inventado", hoy=self.lunes))

    def test_cambio_de_nivel(self):
        self.assertIn("error", cron.cambiar_nivel("NoExiste"))
        r = cron.cambiar_nivel("Avanzado", 1, self.lunes)
        self.assertTrue(r["ok"])
        self.assertEqual(cron.get_estado_hoy(self.lunes)["tipo"], "musculacion")

    def test_tablas_creadas(self):
        con = sqlite3.connect(cron.DB_PATH)
        tablas = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        con.close()
        self.assertTrue({"estado_programa", "historial_dias"} <= tablas)


if __name__ == "__main__":
    unittest.main()
