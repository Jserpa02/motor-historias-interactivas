import unittest
import json
import copy
from engine import StoryEngine
from validator import validar_historia, ValidationError

class TestStoryEngine(unittest.TestCase):

    def setUp(self):
        self.engine = StoryEngine("la_ultima_transmision.json")

    def test_u1_u2_i1_flujo_completo(self):
        # U1 & U2 & I1: Partida nueva en E1 -> E2 -> E3 con conoce_origen = true
        self.assertEqual(self.engine.escena_actual_id, "E1")
        self.assertFalse(self.engine.variables["conoce_origen"])

        # Elegir revisar señal -> E2
        escena = self.engine.tomar_opcion("revisar")
        self.assertEqual(escena["id"], "E2")

        # En E2, elegir investigar archivo -> E3 (efecto conoce_origen = true)
        escena = self.engine.tomar_opcion("investigar")
        self.assertEqual(escena["id"], "E3")
        self.assertTrue(self.engine.variables["conoce_origen"])

        # U1: En E3 con conoce_origen = true, deben verse activar_codigo y cortar (activar_sin_verificar no debe estar)
        opciones = self.engine.obtener_opciones_disponibles()
        ids_opciones = [op["id"] for op in opciones]
        self.assertIn("activar_codigo", ids_opciones)
        self.assertIn("cortar", ids_opciones)
        self.assertNotIn("activar_sin_verificar", ids_opciones)

        # U2: Elegir activar_codigo -> E4 (Rescate)
        escena = self.engine.tomar_opcion("activar_codigo")
        self.assertEqual(escena["id"], "E4")
        self.assertTrue(escena["final"])
        self.assertTrue(self.engine.variables["confia_en_la_voz"])

    def test_u3_opcion_no_habilitada(self):
        # En E1, intentar tomar una opción que no pertenece a E1 o no está habilitada
        estado_antes = (self.engine.escena_actual_id, dict(self.engine.variables))
        with self.assertRaises(ValueError):
            self.engine.tomar_opcion("investigar") # No existe en E1
        # U3 exige estado intacto
        self.assertEqual(self.engine.escena_actual_id, estado_antes[0])
        self.assertEqual(self.engine.variables, estado_antes[1])

    def test_u3_ca02_opcion_deshabilitada_rechazada(self):
        # CA02: En E3 sin conocer origen, activar_codigo debe rechazarse aunque se envíe su ID directamente
        self.engine.tomar_opcion("revisar")
        self.engine.tomar_opcion("continuar")  # llega a E3 con conoce_origen=False
        self.assertEqual(self.engine.escena_actual_id, "E3")
        self.assertFalse(self.engine.variables["conoce_origen"])
        estado_antes = (self.engine.escena_actual_id, dict(self.engine.variables))
        with self.assertRaises(ValueError):
            self.engine.tomar_opcion("activar_codigo")
        self.assertEqual(self.engine.escena_actual_id, estado_antes[0])
        self.assertEqual(self.engine.variables, estado_antes[1])
        # Ruta válida alternativa sí funciona: activar_sin_verificar -> E5
        escena = self.engine.tomar_opcion("activar_sin_verificar")
        self.assertEqual(escena["id"], "E5")
        self.assertTrue(escena["final"])

    def test_u5_reiniciar(self):
        self.engine.tomar_opcion("revisar")
        self.engine.tomar_opcion("investigar")
        self.assertTrue(self.engine.variables["conoce_origen"])
        
        self.engine.reiniciar()
        self.assertEqual(self.engine.escena_actual_id, "E1")
        self.assertFalse(self.engine.variables["conoce_origen"])

    def test_segunda_historia(self):
        # Verificar que la segunda historia funciona sin modificar el motor
        engine2 = StoryEngine("segunda_historia.json")
        self.assertEqual(engine2.titulo, "El Laboratorio Subterráneo")
        self.assertEqual(engine2.escena_actual_id, "L1")
        
        escena = engine2.tomar_opcion("buscar")
        self.assertEqual(escena["id"], "L2")
        self.assertTrue(engine2.variables["tiene_llave"])

        escena = engine2.tomar_opcion("abrir_con_llave")
        self.assertEqual(escena["id"], "L4")
        self.assertTrue(escena["final"])

    def test_u4_validacion_errores(self):
        with open("la_ultima_transmision.json", "r", encoding="utf-8") as f:
            base = json.load(f)

        def clonar():
            return copy.deepcopy(base)

        # 1. Campos obligatorios ausentes (raíz)
        with self.assertRaises(ValidationError):
            validar_historia({"titulo": "Incompleta"})

        # 2. Inicio inexistente
        d = clonar(); d["inicio"] = "E99"
        with self.assertRaises(ValidationError):
            validar_historia(d)

        # 3. IDs de escenas duplicados
        d = clonar(); d["escenas"].append(copy.deepcopy(d["escenas"][0]))
        with self.assertRaises(ValidationError):
            validar_historia(d)

        # 4. IDs de opciones duplicados dentro de su escena (E2)
        d = clonar()
        d["escenas"][1]["opciones"].append(copy.deepcopy(d["escenas"][1]["opciones"][0]))
        with self.assertRaises(ValidationError):
            validar_historia(d)

        # 5. Destino inexistente (CA03)
        d = clonar()
        d["escenas"][0]["opciones"][0]["destino"] = "E99"
        with self.assertRaises(ValidationError):
            validar_historia(d)

        # 6. Variable no declarada en condiciones
        d = clonar()
        d["escenas"][2]["opciones"][0]["condiciones"] = {"variable_fantasma": True}
        with self.assertRaises(ValidationError):
            validar_historia(d)

        # 7. Variable no declarada en efectos
        d = clonar()
        d["escenas"][1]["opciones"][0]["efectos"] = {"otra_fantasma": True}
        with self.assertRaises(ValidationError):
            validar_historia(d)

        # 8. Valor no booleano en condición / efecto / variables iniciales
        d = clonar()
        d["escenas"][2]["opciones"][0]["condiciones"] = {"conoce_origen": "si"}
        with self.assertRaises(ValidationError):
            validar_historia(d)
        d = clonar()
        d["escenas"][1]["opciones"][0]["efectos"] = {"conoce_origen": 1}
        with self.assertRaises(ValidationError):
            validar_historia(d)
        d = clonar(); d["variables"]["conoce_origen"] = "falso"
        with self.assertRaises(ValidationError):
            validar_historia(d)

        # 9a. Final con opciones (>0) incompatible
        d = clonar()
        d["escenas"][3]["opciones"] = [
            {"id": "x", "texto": "X", "destino": "E4",
             "condiciones": {}, "efectos": {}}
        ]
        with self.assertRaises(ValidationError):
            validar_historia(d)

        # 9b. No final con cero opciones incompatible
        d = clonar(); d["escenas"][0]["opciones"] = []
        with self.assertRaises(ValidationError):
            validar_historia(d)

        # 10. Archivo ilegible / estructura incorrecta (no dict)
        with self.assertRaises(ValidationError):
            validar_historia(["no", "es", "dict"])
        with self.assertRaises(ValidationError):
            validar_historia(None)

    def test_bloqueo_sin_opciones_habilitadas(self):
        # Escena no final donde ninguna opción queda habilitada -> bloqueo controlado
        data = {
            "titulo": "Bloqueo",
            "inicio": "B1",
            "variables": {"flag": False},
            "escenas": [
                {"id": "B1", "texto": "Inicio", "final": False,
                 "opciones": [
                     {"id": "ir", "texto": "Ir", "destino": "B2",
                      "condiciones": {}, "efectos": {}}
                 ]},
                {"id": "B2", "texto": "Sin salida", "final": False,
                 "opciones": [
                     {"id": "salir", "texto": "Salir", "destino": "B3",
                      "condiciones": {"flag": True}, "efectos": {}},
                     {"id": "salir2", "texto": "Salir2", "destino": "B3",
                      "condiciones": {"flag": True}, "efectos": {}}
                 ]},
                {"id": "B3", "texto": "Fin", "final": True, "opciones": []}
            ]
        }
        validar_historia(data)
        import tempfile, os
        with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False, encoding="utf-8") as tf:
            json.dump(data, tf)
            ruta = tf.name
        try:
            eng = StoryEngine(ruta)
            eng.tomar_opcion("ir")
            self.assertEqual(eng.escena_actual_id, "B2")
            self.assertEqual(eng.obtener_opciones_disponibles(), [])
            # Intentar avanzar debe fallar sin alterar estado
            with self.assertRaises(ValueError):
                eng.tomar_opcion("salir")
            self.assertEqual(eng.escena_actual_id, "B2")
        finally:
            os.unlink(ruta)

if __name__ == "__main__":
    unittest.main()
