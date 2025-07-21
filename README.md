# Excel NLP Query PoC

Este proyecto es una prueba de concepto para responder preguntas en lenguaje natural sobre datos de un archivo Excel usando Python, Pandas y un modelo LLM (Groq).

## Estructura
- `src/`: Código principal
  - `main.py`: Script principal. Recibe la ruta al archivo Excel y la pregunta.
  - `utils.py`: Funciones para cargar el Excel, construir el prompt y ejecutar el código generado.
  - `groq_client.py`: Cliente para interactuar con el modelo LLM de Groq.
  - `config.py`: Configuración (si aplica).
- `prompts/`: Plantillas de prompt para el LLM
  - `base_prompt.txt`: Prompt base para generar código Python a partir de la pregunta y el esquema del DataFrame.
- `data/`: Archivos de datos de ejemplo
  - `ejemplo.xlsx`: Archivo Excel de muestra.
- `requirements.txt`: Dependencias del proyecto.

## Uso
1. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Configura la variable de entorno `GROQ_API_KEY`.
3. Ejecuta el script principal:
   ```bash
   python -m src.main data/ejemplo.xlsx "¿Cuál es la región con más ingresos?"
   ```

## Funcionamiento
- El script carga el archivo Excel y extrae el esquema del DataFrame.
- Construye un prompt para el LLM, que genera un bloque de código Python para responder la pregunta.
- El código generado se ejecuta de forma segura sobre el DataFrame y se muestra el resultado.

## Seguridad
- El código generado se ejecuta en un entorno restringido, sin acceso a funciones peligrosas.
- Se recomienda revisar y sandboxear el código antes de usar en producción.

## Ejemplo de prompt
```
Eres un experto en análisis de datos con Python y Pandas.
...
Usa `result = ...` como línea final para que pueda capturarse automáticamente.
```

## Estado
- Fase 1 completada: flujo funcional, logging básico, ejecución segura, prompt ajustado.

---
GitHub Copilot
