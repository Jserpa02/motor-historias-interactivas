import copy
import json
import os
import tempfile
import time
import unittest

from engine import StoryEngine
from validator import validar_historia, ValidationError

HISTORIA = "la_ultima_transmision.json"
SEGUNDA = "segunda_historia.json"


def cargar_base():
    with open(HISTORIA, "r", encoding="utf-8") as f:
        return json.load(f)


def motor_desde_datos(data):
    """Escribe los datos en un archivo temporal y devuelve el motor cargado."""
    with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8") as tf:
        json.dump(data, tf)
        ruta = tf.name
    try:
        return StoryEngine(ruta)
    finally:
        os.unlink(ruta)


def ids(opciones):
    return [op["id"] for op in opciones]


class TestStoryEngine(unittest.TestCase):

    def setUp(self):
        self.engine = StoryEngine(HISTORIA)

    def estado(self):
        return (self.engine.escena_actual_id, dict(self.engine.variables))

    # ---------- U1: condiciones cumplidas / no cumplidas ----------
    def test_u1_condicion_cumplida_en_e3(self):
        self.engine.tomar_opcion("revisar")
        self.engine.tomar_opcion("investigar")
        self.assertEqual(self.engine.escena_actual_id, "E3")
        self.assertTrue(self.engine.variables["conoce_origen"])
        self.assertCountEqual(
            ids(self.engine.obtener_opciones_disponibles()),
            ["activar_codigo", "cortar"])

    def test_u1_condicion_no_cumplida_en_e3(self):
        self.engine.tomar_opcion("revisar")
        self.engine.tomar_opcion("continuar")
        self.assertEqual(self.engine.escena_actual_id, "E3")
        self.assertFalse(self.engine.variables["conoce_origen"])
        self.assertCountEqual(
            ids(self.engine.obtener_opciones_disponibles()),
            ["activar_sin_verificar", "cortar"])

    def test_u1_mapa_vacio_habilita(self):
        self.assertEqual(ids(self.engine.obtener_opciones_disponibles()), ["revisar"])

    # ---------- U2: elección válida aplica efectos y avanza ----------
    def test_u2_efectos_y_destino(self):
        escena = self.engine.tomar_opcion("revisar")
        self.assertEqual(escena["id"], "E2")
        self.assertFalse(self.engine.variables["conoce_origen"])
        escena = self.engine.tomar_opcion("investigar")
        self.assertEqual(escena["id"], "E3")
        self.assertTrue(self.engine.variables["conoce_origen"])
        escena = self.engine.tomar_opcion("activar_codigo")
        self.assertEqual(escena["id"], "E4")
        self.assertTrue(escena["final"])
        self.assertTrue(self.engine.variables["confia_en_la_voz"])

    def test_u2_efecto_falso_en_cortar(self):
        self.engine.tomar_opcion("revisar")
        self.engine.tomar_opcion("investigar")
        escena = self.engine.tomar_opcion("cortar")
        self.assertEqual(escena["id"], "E6")
        self.assertFalse(self.engine.variables["confia_en_la_voz"])

    # ---------- U3: entrada inválida deja el estado intacto ----------
    def test_u3_opcion_inexistente(self):
        antes = self.estado()
        for oid in ("investigar", "no_existe", "", "revisar_senal"):
            with self.subTest(opcion=oid):
                with self.assertRaises(ValueError):
                    self.engine.tomar_opcion(oid)
                self.assertEqual(self.estado(), antes)

    def test_u3_ca02_opcion_deshabilitada(self):
        self.engine.tomar_opcion("revisar")
        self.engine.tomar_opcion("continuar")
        antes = self.estado()
        self.assertEqual(antes[0], "E3")
        with self.assertRaises(ValueError):
            self.engine.tomar_opcion("activar_codigo")
        self.assertEqual(self.estado(), antes)
        escena = self.engine.tomar_opcion("activar_sin_verificar")
        self.assertEqual(escena["id"], "E5")
        self.assertTrue(escena["final"])

    # ---------- U5: reinicio ----------
    def test_u5_reiniciar(self):
        inicial = self.estado()
        self.engine.tomar_opcion("revisar")
        self.engine.tomar_opcion("investigar")
        self.engine.tomar_opcion("activar_codigo")
        self.assertNotEqual(self.estado(), inicial)
        self.engine.reiniciar()
        self.assertEqual(self.estado(), inicial)
        self.assertEqual(self.engine.escena_actual_id, "E1")
        self.assertFalse(self.engine.variables["conoce_origen"])
        self.assertFalse(self.engine.variables["confia_en_la_voz"])

    # ---------- I1: archivo real + motor hasta un final ----------
    def test_i1_tres_finales(self):
        rutas = {
            "E4": ["revisar", "investigar", "activar_codigo"],
            "E5": ["revisar", "continuar", "activar_sin_verificar"],
            "E6": ["revisar", "continuar", "cortar"],
        }
        for final, ruta in rutas.items():
            with self.subTest(final=final):
                motor = StoryEngine(HISTORIA)
                for oid in ruta:
                    motor.tomar_opcion(oid)
                self.assertEqual(motor.escena_actual_id, final)
                self.assertTrue(motor.obtener_escena_actual()["final"])
                self.assertEqual(motor.obtener_opciones_disponibles(), [])

    # ---------- RNF01: segunda historia sin tocar el motor ----------
    def test_rnf01_segunda_historia(self):
        motor = StoryEngine(SEGUNDA)
        self.assertEqual(motor.escena_actual_id, "L1")
        escena = motor.tomar_opcion("buscar")
        self.assertEqual(escena["id"], "L2")
        self.assertTrue(motor.variables["tiene_llave"])
        escena = motor.tomar_opcion("abrir_con_llave")
        self.assertEqual(escena["id"], "L4")
        self.assertTrue(escena["final"])

    def test_rnf01_condicion_segunda_historia(self):
        motor = StoryEngine(SEGUNDA)
        motor.tomar_opcion("forzar")
        self.assertEqual(motor.escena_actual_id, "L3")
        motor = StoryEngine(SEGUNDA)
        with self.assertRaises(ValueError):
            motor.tomar_opcion("abrir_con_llave")
        self.assertEqual(motor.escena_actual_id, "L1")

    # ---------- Bloqueo en partida ----------
    def test_bloqueo_sin_opciones_habilitadas(self):
        data = {
            "titulo": "Bloqueo",
            "inicio": "B1",
            "variables": {"flag": False},
            "escenas": [
                {"id": "B1", "texto": "Inicio", "final": False,
                 "opciones": [{"id": "ir", "texto": "Ir", "destino": "B2",
                               "condiciones": {}, "efectos": {}}]},
                {"id": "B2", "texto": "Sin salida", "final": False,
                 "opciones": [{"id": "salir", "texto": "Salir", "destino": "B3",
                               "condiciones": {"flag": True}, "efectos": {}}]},
                {"id": "B3", "texto": "Fin", "final": True, "opciones": []},
            ],
        }
        motor = motor_desde_datos(data)
        motor.tomar_opcion("ir")
        self.assertEqual(motor.escena_actual_id, "B2")
        self.assertFalse(motor.obtener_escena_actual()["final"])
        self.assertEqual(motor.obtener_opciones_disponibles(), [])
        with self.assertRaises(ValueError):
            motor.tomar_opcion("salir")
        self.assertEqual(motor.escena_actual_id, "B2")
        motor.reiniciar()
        self.assertEqual(motor.escena_actual_id, "B1")


class TestValidacion(unittest.TestCase):
    """U4: cada caso indica (modificación, texto esperado en el mensaje)."""

    def casos(self):
        def mod(fn):
            d = cargar_base()
            fn(d)
            return d

        def raiz_sin_escenas(d): del d["escenas"]
        def inicio_inexistente(d): d["inicio"] = "E99"
        def inicio_no_texto(d): d["inicio"] = ["E1"]
        def escena_duplicada(d): d["escenas"].append(copy.deepcopy(d["escenas"][0]))
        def opcion_duplicada(d):
            d["escenas"][1]["opciones"].append(copy.deepcopy(d["escenas"][1]["opciones"][0]))
        def destino_inexistente(d): d["escenas"][0]["opciones"][0]["destino"] = "E99"
        def destino_no_texto(d): d["escenas"][0]["opciones"][0]["destino"] = ["E2"]
        def cond_no_declarada(d):
            d["escenas"][2]["opciones"][0]["condiciones"] = {"variable_fantasma": True}
        def efecto_no_declarado(d):
            d["escenas"][1]["opciones"][0]["efectos"] = {"otra_fantasma": True}
        def cond_no_bool(d):
            d["escenas"][2]["opciones"][0]["condiciones"] = {"conoce_origen": "si"}
        def efecto_no_bool(d):
            d["escenas"][1]["opciones"][0]["efectos"] = {"conoce_origen": 1}
        def variable_no_bool(d): d["variables"]["conoce_origen"] = "falso"
        def final_con_opciones(d):
            d["escenas"][3]["opciones"] = [{"id": "x", "texto": "X", "destino": "E4",
                                            "condiciones": {}, "efectos": {}}]
        def no_final_sin_opciones(d): d["escenas"][0]["opciones"] = []
        def escena_sin_texto(d): del d["escenas"][0]["texto"]
        def opcion_sin_destino(d): del d["escenas"][0]["opciones"][0]["destino"]

        return [
            ("raiz sin escenas", mod(raiz_sin_escenas), "escenas"),
            ("inicio inexistente", mod(inicio_inexistente), "E99"),
            ("inicio no texto", mod(inicio_no_texto), "inicio"),
            ("escena duplicada", mod(escena_duplicada), "E1"),
            ("opcion duplicada", mod(opcion_duplicada), "investigar"),
            ("destino inexistente", mod(destino_inexistente), "E99"),
            ("destino no texto", mod(destino_no_texto), "revisar"),
            ("condicion no declarada", mod(cond_no_declarada), "variable_fantasma"),
            ("efecto no declarado", mod(efecto_no_declarado), "otra_fantasma"),
            ("condicion no booleana", mod(cond_no_bool), "conoce_origen"),
            ("efecto no booleano", mod(efecto_no_bool), "conoce_origen"),
            ("variable inicial no booleana", mod(variable_no_bool), "conoce_origen"),
            ("final con opciones", mod(final_con_opciones), "E4"),
            ("no final sin opciones", mod(no_final_sin_opciones), "E1"),
            ("escena sin texto", mod(escena_sin_texto), "texto"),
            ("opcion sin destino", mod(opcion_sin_destino), "destino"),
            ("raiz no objeto (lista)", ["no", "es", "dict"], "objeto"),
            ("raiz nula", None, "objeto"),
            ("raiz incompleta", {"titulo": "Incompleta"}, "inicio"),
        ]

    def test_u4_rechazo_con_causa_e_id(self):
        for nombre, datos, esperado in self.casos():
            with self.subTest(caso=nombre):
                with self.assertRaises(ValidationError) as ctx:
                    validar_historia(datos)
                self.assertIn(esperado, str(ctx.exception))

    def test_u4_historias_validas(self):
        self.assertTrue(validar_historia(cargar_base()))
        with open(SEGUNDA, "r", encoding="utf-8") as f:
            self.assertTrue(validar_historia(json.load(f)))

    def test_u4_archivo_ilegible_no_abre_sesion(self):
        contenidos = {
            "json mal formado": b"{no es json",
            "no utf-8": b"\xff\xfe\x00",
            "vacio": b"",
        }
        for nombre, contenido in contenidos.items():
            with self.subTest(caso=nombre):
                with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
                    tf.write(contenido)
                    ruta = tf.name
                try:
                    with self.assertRaises(ValueError):
                        StoryEngine(ruta)
                finally:
                    os.unlink(ruta)

    def test_u4_archivo_inexistente(self):
        with self.assertRaises(OSError):
            StoryEngine("no_existe_xyz.json")

    def test_ca03_destino_e99_en_archivo_no_abre_sesion(self):
        d = cargar_base()
        d["escenas"][0]["opciones"][0]["destino"] = "E99"
        with self.assertRaises(ValidationError) as ctx:
            motor_desde_datos(d)
        mensaje = str(ctx.exception)
        self.assertIn("E99", mensaje)
        self.assertIn("revisar", mensaje)
        self.assertIn("E1", mensaje)

    def test_rnf02_rechazo_en_menos_de_un_segundo(self):
        for nombre, datos, _ in self.casos():
            with self.subTest(caso=nombre):
                inicio = time.perf_counter()
                with self.assertRaises(ValidationError):
                    validar_historia(datos)
                self.assertLess(time.perf_counter() - inicio, 1.0)


if __name__ == "__main__":
    unittest.main()
