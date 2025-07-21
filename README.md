# Excel NLP Query POC

Este proyecto es una prueba de concepto para consultar archivos Excel mediante lenguaje natural usando LLMs, con gestión segura de archivos y frontend elegante.

## Características
- Subida, renombrado y borrado de archivos Excel/CSV.
- Consulta por chat con historial por archivo.
- Prompt personalizado por archivo.
- Backend FastAPI + pandas + RestrictedPython (sandbox seguro).
- Frontend vanilla JS + CSS adaptativo.
- Cabeceras normalizadas (sin tildes, minúsculas, sin espacios).
- Eliminación completa de archivos (original, procesado, metadata).
- `.gitignore` robusto para evitar subir datos y secretos.

## Instalación
```bash
# Clona el repositorio
https://github.com/Husky34Dev/excel_nlp_query_poc.git
cd excel_nlp_query_poc

# Crea y activa entorno virtual
python -m venv .venv
.venv\Scripts\activate

# Instala dependencias
pip install -r requirements.txt

# Configura tu archivo .env si usas claves o endpoints privados
```

## Uso
```bash
# Ejecuta el backend
uvicorn app.main:app --reload

# Accede a la app en tu navegador
http://localhost:8000
```

## Notas
- No subas archivos de datos reales al repositorio.
- Las cabeceras de los archivos se normalizan automáticamente.
- El sistema es "a prueba de bombas" para encoding y formatos.

## Autor
Husky34Dev
