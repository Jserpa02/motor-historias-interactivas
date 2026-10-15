# Motor de Historias Interactivas - La Última Transmisión

Parcial Práctico de Ingeniería de Software.

## Integrantes
- **Integrante 1:** Daniel Sanchez
- **Integrante 2:** Juan Diego Serpa

---

## Descripción del Proyecto
Este proyecto implementa un **motor de historias interactivas** basado en reglas booleanas y lectura de archivos estructurados en formato JSON. El motor es completamente independiente del contenido, lo que permite cargar y ejecutar relatos interactivos (como *La última transmisión* o cualquier otra historia compatible con el contrato) sin modificar el código fuente.

---

## Requisitos del Sistema
- **Python:** Versión 3.8 o superior (probado en Python 3.14).
- No requiere dependencias externas adicionales (`json`, `unittest` y `os` forman parte de la biblioteca estándar de Python).

---

## Estructura de Archivos
- `engine.py`: Núcleo del motor de historias (gestión de estado, evaluación de condiciones y efectos).
- `validator.py`: Módulo de validación estricta y control de errores de contenido.
- `main.py`: Interfaz de usuario por consola (CLI) para jugar las historias.
- `test_engine.py`: Suite de pruebas automatizadas (cobertura U1-U5, I1 y validación de errores).
- `la_ultima_transmision.json`: Archivo de datos de la historia principal (6 escenas, 3 finales).
- `segunda_historia.json`: Segunda historia de prueba (mínimo 3 escenas, condición y efecto).
- `README.md`: Este archivo con instrucciones de uso.

---

## Instrucciones de Instalación y Ejecución

### 1. Clonar o descargar el repositorio
Asegúrate de tener todos los archivos en la misma carpeta local.

### 2. Ejecutar la historia principal
Para jugar la historia principal (*La última transmisión*), ejecuta:
```bash
python main.py la_ultima_transmision.json
```

### 3. Ejecutar la segunda historia
Para verificar que el motor funciona con una segunda historia sin modificar el código, ejecuta:
```bash
python main.py segunda_historia.json
```

---

## Ejecución de Pruebas Automatizadas
Para correr la suite de pruebas unitarias y de integración (U1 a U5, I1 y validación de errores):
```bash
python -m unittest test_engine -v
```
Última ejecución verificada: 18 pruebas, OK (U1, U2, U3, U4 con `subTest` por categoría de error y comprobación de mensajes, U5, I1 con los tres finales, segunda historia, bloqueo, CA03 y RNF02 < 1 s). El registro está en `resultados_pruebas.txt`.

---

## Rutas para demostrar cada final (historia principal)

Estado inicial: `E1`, `conoce_origen=false`, `confia_en_la_voz=false`.

- **Final E4 (Rescate):** E1 `revisar` → E2 `investigar` (pone `conoce_origen=true`) → E3 muestra `activar_codigo` + `cortar` → `activar_codigo` → **E4**.
- **Final E5 (El eco):** E1 `revisar` → E2 `continuar` (`conoce_origen=false`) → E3 muestra `activar_sin_verificar` + `cortar` → `activar_sin_verificar` → **E5**.
- **Final E6 (Silencio):** Desde E3 (cualquiera de las dos rutas anteriores) → `cortar` → **E6**.

En E3 siempre se ven exactamente 2 opciones: `cortar` + la activación correspondiente a `conoce_origen`.

---

## Limitaciones conocidas
- Sin persistencia entre ejecuciones, sin cuentas ni red (según límites del ejercicio).
- Sin función de retroceso (acuerdo provisional documentado en el informe).
- Solo condiciones de igualdad sobre booleanos y efectos de asignación true/false.
- No se analizan automáticamente todos los caminos posibles; el bloqueo en escena no final se informa en tiempo de juego y permite reiniciar.

---

## Formato de Contrato JSON
Cada archivo de historia sigue este contrato estricto:
- `titulo`: Texto descriptivo del relato.
- `inicio`: ID de la escena inicial.
- `variables`: Diccionario de variables booleanas iniciales.
- `escenas`: Lista de escenas, donde cada escena contiene `id`, `texto`, `final` (booleano) y `opciones`.
- `opciones`: Cada opción contiene `id`, `texto`, `destino`, `condiciones` (mapa de igualdades booleanas) y `efectos` (mapa de asignaciones).
