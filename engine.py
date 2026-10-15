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
        # RF-UNDO: un solo nivel. None = no hay retroceso disponible.
        self._estado_previo = None

    def puede_deshacer(self):
        return self._estado_previo is not None

    def deshacer(self):
        """Restaura escena y variables anteriores a la ultima eleccion valida.
        Consume el retroceso: no se puede deshacer de nuevo hasta una nueva eleccion."""
        if self._estado_previo is None:
            raise ValueError("No hay ninguna decisión para deshacer.")
        escena_id, variables = self._estado_previo
        self.escena_actual_id = escena_id
        self.variables = dict(variables)
        self._estado_previo = None
        return self.obtener_escena_actual()

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

        # Guardar copia del estado SOLO cuando la opcion ya se valido como habilitada
        # (una entrada invalida no llega aqui, asi que no pisa el historial).
        self._estado_previo = (self.escena_actual_id, dict(self.variables))

        # Aplicar efectos
        for var, nuevo_valor in opcion_elegida["efectos"].items():
            self.variables[var] = nuevo_valor

        # Avanzar destino
        self.escena_actual_id = opcion_elegida["destino"]
        return self.obtener_escena_actual()