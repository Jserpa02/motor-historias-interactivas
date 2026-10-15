import json
import sys
from engine import StoryEngine
from validator import ValidationError

def jugar(filepath):
    try:
        engine = StoryEngine(filepath)
    except (ValidationError, ValueError, OSError) as e:
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
            opcion = input("\n¿Desea reiniciar la partida? (s/n): ").strip().lower()
            if opcion == 's':
                engine.reiniciar()
                continue
            else:
                break

        opciones = engine.obtener_opciones_disponibles()
        if not opciones:
            print("\n[BLOQUEO] No hay opciones disponibles en esta escena no final.")
            opcion = input("¿Desea reiniciar la partida? (s/n): ").strip().lower()
            if opcion == 's':
                engine.reiniciar()
                continue
            else:
                break

        print("\nOpciones disponibles:")
        for idx, op in enumerate(opciones, 1):
            print(f"  {idx}. {op['texto']} (id: {op['id']})")

        eleccion = input("\nSeleccione el número de la opción (o 'r' para reiniciar, 'q' para salir): ").strip().lower()
        
        if eleccion == 'q':
            break
        if eleccion == 'r':
            engine.reiniciar()
            print("\n--- Partida reiniciada ---")
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
    
    jugar(archivo)
