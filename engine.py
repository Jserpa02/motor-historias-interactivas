import json
from validator import validar_historia

class StoryEngine:
    def __init__(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        validar_historia(data)
        
        self.titulo = data["titulo"]
        self.inicio = data["inicio"]
        self.variables_iniciales = data["variables"]
        self.escenas = {escena["id"]: escena for escena in data["escenas"]}
        
        self.reiniciar()

    def reiniciar(self):
        self.escena_actual_id = self.inicio
        self.variables = dict(self.variables_iniciales)

    def obtener_escena_actual(self):
        return self.escenas[self.escena_actual_id]

    def evaluar_condiciones(self, condiciones):
        for var, valor_esperado in condiciones.items():
            if self.variables.get(var) != valor_esperado:
                return False
        return True

    def obtener_opciones_disponibles(self):
        escena = self.obtener_escena_actual()
        if escena["final"]:
            return []
        
        disponibles = []
        for op in escena["opciones"]:
            if self.evaluar_condiciones(op["condiciones"]):
                disponibles.append(op)
        return disponibles

    def tomar_opcion(self, opcion_id):
        opciones = self.obtener_opciones_disponibles()
        opcion_elegida = None
        for op in opciones:
            if op["id"] == opcion_id:
                opcion_elegida = op
                break
        
        if not opcion_elegida:
            raise ValueError(f"La opción '{opcion_id}' no existe o no está habilitada en la escena actual.")

        # Aplicar efectos
        for var, nuevo_valor in opcion_elegida["efectos"].items():
            self.variables[var] = nuevo_valor

        # Avanzar destino
        self.escena_actual_id = opcion_elegida["destino"]
        return self.obtener_escena_actual()
