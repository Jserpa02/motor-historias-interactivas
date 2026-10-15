class ValidationError(Exception):
    pass

def validar_historia(data):
    if not isinstance(data, dict):
        raise ValidationError("El archivo debe ser un objeto JSON válido.")

    campos_requeridos = ["titulo", "inicio", "variables", "escenas"]
    for campo in campos_requeridos:
        if campo not in data:
            raise ValidationError(f"Falta el campo obligatorio raíz: '{campo}'.")

    titulo = data["titulo"]
    inicio = data["inicio"]
    variables_iniciales = data["variables"]
    escenas = data["escenas"]

    if not isinstance(titulo, str):
        raise ValidationError("El campo 'titulo' debe ser un texto.")
    if not isinstance(variables_iniciales, dict):
        raise ValidationError("El campo 'variables' debe ser un diccionario de clave-valor booleano.")
    
    # Validar que las variables iniciales sean booleanas
    for var, val in variables_iniciales.items():
        if not isinstance(val, bool):
            raise ValidationError(f"La variable inicial '{var}' no tiene un valor booleano válido.")

    if not isinstance(escenas, list) or len(escenas) == 0:
        raise ValidationError("El campo 'escenas' debe ser una lista no vacía.")

    ids_escenas = set()
    escenas_map = {}

    for escena in escenas:
        if not isinstance(escena, dict):
            raise ValidationError("Cada elemento de 'escenas' debe ser un objeto.")
        
        for req in ["id", "texto", "final", "opciones"]:
            if req not in escena:
                raise ValidationError(f"Falta el campo obligatorio '{req}' en una escena.")

        eid = escena["id"]
        if not isinstance(eid, str):
            raise ValidationError(f"El ID de escena '{eid}' debe ser un texto.")
        if eid in ids_escenas:
            raise ValidationError(f"ID de escena duplicado encontrado: '{eid}'.")
        ids_escenas.add(eid)

        if not isinstance(escena["final"], bool):
            raise ValidationError(f"El campo 'final' en la escena '{eid}' debe ser booleano.")
        if not isinstance(escena["opciones"], list):
            raise ValidationError(f"El campo 'opciones' en la escena '{eid}' debe ser una lista.")

        escenas_map[eid] = escena

    # Validar escena inicial
    if inicio not in ids_escenas:
        raise ValidationError(f"La escena inicial '{inicio}' no existe en la lista de escenas.")

    # Validar opciones
    for eid, escena in escenas_map.items():
        es_final = escena["final"]
        opciones = escena["opciones"]

        if es_final and len(opciones) > 0:
            raise ValidationError(f"La escena final '{eid}' no debe tener opciones (tiene {len(opciones)}).")
        if not es_final and len(opciones) == 0:
            raise ValidationError(f"La escena no final '{eid}' debe tener al menos una opción.")

        ids_opciones = set()
        for opcion in opciones:
            if not isinstance(opcion, dict):
                raise ValidationError(f"Una opción en la escena '{eid}' no es un objeto válido.")
            
            for req in ["id", "texto", "destino", "condiciones", "efectos"]:
                if req not in opcion:
                    raise ValidationError(f"Falta el campo '{req}' en una opción de la escena '{eid}'.")

            oid = opcion["id"]
            if oid in ids_opciones:
                raise ValidationError(f"ID de opción duplicado '{oid}' dentro de la escena '{eid}'.")
            ids_opciones.add(oid)

            destino = opcion["destino"]
            if destino not in ids_escenas:
                raise ValidationError(f"La opción '{oid}' en la escena '{eid}' apunta a un destino inexistente '{destino}'.")

            condiciones = opcion["condiciones"]
            efectos = opcion["efectos"]

            if not isinstance(condiciones, dict) or not isinstance(efectos, dict):
                raise ValidationError(f"Las condiciones y efectos de la opción '{oid}' en '{eid}' deben ser diccionarios.")

            for var, val in condiciones.items():
                if var not in variables_iniciales:
                    raise ValidationError(f"La condición utiliza la variable no declarada '{var}' en la opción '{oid}' de la escena '{eid}'.")
                if not isinstance(val, bool):
                    raise ValidationError(f"El valor de la condición para '{var}' en la opción '{oid}' debe ser booleano.")

            for var, val in efectos.items():
                if var not in variables_iniciales:
                    raise ValidationError(f"El efecto modifica la variable no declarada '{var}' en la opción '{oid}' de la escena '{eid}'.")
                if not isinstance(val, bool):
                    raise ValidationError(f"El valor del efecto para '{var}' debe ser booleano en la opción '{oid}'.")

    return True
