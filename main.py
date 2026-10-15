import json
import sys
import os
from engine import StoryEngine
from validator import ValidationError

def _menu_cierre(engine):
    """Menu para finales y bloqueos. Devuelve True si la partida continua."""
    while True:
        extra = ", 'u' deshacer" if engine.puede_deshacer() else ""
        opcion = input(f"¿Qué desea hacer? ('s' reiniciar{extra}, 'n' salir): ").strip().lower()
        if opcion == 's':
            engine.reiniciar()
            return True
        if opcion == 'u' and engine.puede_deshacer():
            engine.deshacer()
            print("\n--- Última decisión deshecha ---")
            return True
        if opcion == 'n':
            return False
        print("Opción no válida.")

def jugar(filepath):
    try:
        engine = StoryEngine(filepath)
    except (ValidationError, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error al cargar la historia: {e}")
        return

    print(f"\n========================================")
    print(f" HISTORIA: {engine.titulo}")
    print(f"========================================")

    while True:
        escena = engine.obtener_escena_actual()
        print(f"\n[{escena['id']}] {escena['texto']}")
        print(f"Variables actuales: {engine.variables}")

        if escena["final"]:
            print("\n*** FIN DE LA HISTORIA ***")
            if not _menu_cierre(engine):
                break
            continue

        opciones = engine.obtener_opciones_disponibles()
        if not opciones:
            print("\n[BLOQUEO] No hay opciones disponibles en esta escena no final.")
            if not _menu_cierre(engine):
                break
            continue

        print("\nOpciones disponibles:")
        for idx, op in enumerate(opciones, 1):
            print(f"  {idx}. {op['texto']} (id: {op['id']})")

        extra = ", 'u' para deshacer" if engine.puede_deshacer() else ""
        eleccion = input(f"\nSeleccione el número de la opción (o 'r' para reiniciar{extra}, 'q' para salir): ").strip().lower()

        if eleccion == 'q':
            break
        if eleccion == 'r':
            engine.reiniciar()
            print("\n--- Partida reiniciada ---")
            continue
        if eleccion == 'u':
            if engine.puede_deshacer():
                engine.deshacer()
                print("\n--- Última decisión deshecha ---")
            else:
                print("No hay ninguna decisión para deshacer.")
            continue

        try:
            idx_opcion = int(eleccion) - 1
            if 0 <= idx_opcion < len(opciones):
                op_elegida = opciones[idx_opcion]
                engine.tomar_opcion(op_elegida["id"])
            else:
                print("Número de opción inválido.")
        except ValueError:
            print("Por favor, ingrese un número válido.")

if __name__ == "__main__":
    archivo = "la_ultima_transmision.json"
    if len(sys.argv) > 1:
        archivo = sys.argv[1]
    
    if not os.path.exists(archivo):
        print(f"No se encontró el archivo '{archivo}'. Usando 'la_ultima_transmision.json'.")
        archivo = "la_ultima_transmision.json"
        
    jugar(archivo)