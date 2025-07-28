# dev.md
---
## 🟡 Endpoint `/api/process_file` y Preprocesamiento Interactivo (Julio 2025)

### Resumen del flujo
- El usuario sube un archivo y visualiza una preview (cabeceras, tipos, primeras filas).
- Puede quitar columnas, renombrarlas y cambiar su tipo antes de procesar definitivamente.
- El frontend valida en tiempo real y muestra feedback visual inmediato (errores de tipo, advertencias al deshabilitar columnas).
- Al confirmar, se envía la configuración final al backend (`/api/process_file`).
- El backend aplica los cambios, valida tipos, normaliza nombres y guarda solo el archivo procesado (no el original).
- Se devuelven metadatos y file_id del archivo procesado.

### Requisitos clave
- **Tipos permitidos:** solo tipos estándar de pandas (int, float, str, bool, datetime, object).
- **Feedback visual:**
    - Si falla la conversión de tipo, la columna se resalta en rojo y se muestra mensaje claro.
    - Al deshabilitar una columna, advertencia: “Cuidado: deshabilitar una columna durante el procesamiento es definitivo y no se puede deshacer.”
- **Guardado:** nunca se guarda el archivo original, solo el archivo procesado según la configuración final del usuario. Los subconjuntos hijos siempre partirán de este archivo procesado.
- **Normalización de nombres:** todos los nombres de columna se guardan en minúsculas y sin acentos ni caracteres especiales, aunque el usuario escriba tildes o mayúsculas.
- **Código backend:** debe ser abstracto y mantenible, separando funciones para validación, transformación, guardado, etc. Evitar funciones largas y monolíticas.

### Resumen de pasos para implementación
1. Definir modelo de request/response para `/api/process_file`.
2. Implementar validación de tipos y feedback estructurado de errores.
3. Aplicar normalización de nombres y transformación de tipos.
4. Guardar archivo procesado (Parquet) y metadatos.
5. Devolver file_id y metadatos al frontend.

---

## Cambios próximos en la aplicación

### 1. Nueva lógica de carga y pre-procesamiento
- Al cargar un archivo Excel o CSV, se abrirá una ventana modal de pre-procesamiento.
- En esta ventana, el usuario podrá:
  - Cambiar el nombre de las cabeceras (columnas).
  - Ver el tipo de dato detectado por columna.
  - Cambiar el tipo de dato de cada columna para limpiar y ordenar los datos antes de procesar.

### 2. Edición y selección de columnas
- Una vez procesado el DataFrame, el usuario podrá seleccionar y deseleccionar columnas desde el menú de edición.
- Al modificar la selección de columnas:
  - Se generará un archivo .pkl temporal con solo las columnas seleccionadas.
  - Todas las consultas en código pandas se aplicarán sobre este archivo reducido.
  - El usuario podrá rehabilitar/deshabilitar columnas en cualquier momento.

### 3. Gestión de archivos
- Siempre se mantendrán únicamente dos archivos:
  - El archivo original (completo, sin modificaciones).
  - El archivo de trabajo (temporal, con las columnas seleccionadas y pre-procesadas).
- El usuario podrá alternar la selección de columnas, pero la lógica y las consultas se aplicarán solo sobre el archivo de trabajo.

### 4. Migración de Pickle a Parquet
- Se migrará el almacenamiento de los DataFrames de formato pickle (.pkl) a formato Parquet (.parquet), siempre y cuando esto no rompa la compatibilidad ni el funcionamiento del proyecto.
- Parquet ofrece mayor eficiencia, compatibilidad y portabilidad para el manejo de datos tabulares.
- Se mantendrá la lógica de solo dos archivos: el original y el de trabajo, pero ahora en formato Parquet.


Esta nueva lógica permitirá mantener los datos limpios y ordenados, ofrecer mayor flexibilidad al usuario para trabajar con subconjuntos de datos sin perder el original, y mejorar la eficiencia y compatibilidad del almacenamiento de datos.

---

## Plan de desarrollo por fases iterativas

---

## Flujo completo y gestión de archivos para el procesamiento definitivo

### 1. Arrastre y carga inicial (preview)
- El usuario arrastra un archivo (CSV/Excel).
- El frontend lo sube al backend para preview.
- El backend guarda el archivo temporalmente (en `/tmp` o similar), extrae las primeras 5 filas y detecta tipos.
- El backend responde con la preview y tipos detectados.
- **El archivo temporal solo se mantiene mientras el usuario decide.**

### 2. Edición y confirmación
- El usuario edita nombres y tipos en el modal.
- Al confirmar, el frontend envía:
  - El archivo original (puede ser el mismo temporal, o se vuelve a subir si el frontend no lo retiene).
  - La lista de columnas y tipos definitivos.

### 3. Procesamiento definitivo
- El backend:
  1. Lee el archivo completo (desde el temporal o el nuevo upload).
  2. Aplica los cambios de nombres y tipos.
  3. Valida y reporta errores de conversión si los hay.
  4. Guarda:
     - El archivo original (en `/uploads`).
     - El archivo de trabajo procesado (en `/processed`).
     - Los metadatos (en `/metadata`).
  5. Borra el archivo temporal usado para preview.
- **Solo se guardan los archivos definitivos, no los temporales.**

### 4. Consideraciones de memoria y limpieza
- El archivo temporal debe borrarse siempre tras el preview o tras el procesamiento definitivo.
- Si el usuario cancela, se borra el temporal inmediatamente.
- No se deben mantener archivos grandes en memoria: siempre trabajar con rutas y streams, no con el DataFrame entero en RAM más tiempo del necesario.
- Si el archivo es muy grande, considerar procesar por chunks (en el futuro).

### 5. Resumen de archivos en disco
- `/uploads/`: solo el archivo original definitivo.
- `/processed/`: solo el archivo de trabajo (con nombres/tipos editados).
- `/metadata/`: JSON con columnas, tipos, y cambios aplicados.
- **No quedan archivos temporales tras la confirmación o cancelación.**

---

### Siguiente funcionalidad: Endpoint y lógica para procesar el archivo definitivo

**Objetivo:**  
Cuando el usuario edite y confirme los nombres y tipos de columnas en el modal, el frontend debe enviar esa información al backend, que procesará el archivo completo aplicando los cambios y lo guardará como archivo de trabajo.

**Pasos clave:**
1. Definir el endpoint `/process_file` (POST) que reciba:
   - El archivo original (o un identificador si ya está subido).
   - La lista de nombres y tipos de columnas editados por el usuario.
2. El backend debe:
   - Leer el archivo completo.
   - Renombrar columnas y convertir tipos según lo recibido.
   - Validar y manejar errores de conversión.
   - Guardar el archivo de trabajo y los metadatos actualizados.
3. Devolver al frontend un resumen del resultado (éxito, errores, preview, etc).

**Archivos afectados:**
- `app/api/endpoints.py` (nuevo endpoint)
- `app/storage/file_storage.py` (lógica de procesamiento y guardado)
- Documentar el flujo y el payload esperado en `dev.md`.

---

### Detalle del endpoint `/process_file`

**Objetivo:**
Procesar el archivo completo aplicando los cambios de nombres y tipos de columnas elegidos por el usuario, y guardar el archivo definitivo y los metadatos.

**Request (POST, multipart/form-data):**
Debe soportar dos modos:
1. El archivo original se vuelve a subir:
   - `file`: archivo CSV o Excel
   - `columns`: JSON string con la lista de columnas y tipos elegidos por el usuario
2. O bien, si el archivo ya está subido, solo se manda el identificador:
   - `file_id`: string (opcional, si el archivo ya está en uploads)
   - `columns`: JSON string con la lista de columnas y tipos elegidos por el usuario

**Ejemplo de `columns`:**
```json
[
  {"name": "sepal_length", "new_name": "largo_sepalo", "dtype": "float64"},
  {"name": "sepal_width", "new_name": "ancho_sepalo", "dtype": "float64"},
  {"name": "species", "new_name": "especie", "dtype": "category"}
]
```

**Response (application/json):**
```json
{
  "success": true,
  "file_id": "abc123...",
  "columns": [
    {"name": "largo_sepalo", "dtype": "float64"},
    {"name": "ancho_sepalo", "dtype": "float64"},
    {"name": "especie", "dtype": "category"}
  ],
  "preview": [
    {"largo_sepalo": 5.1, "ancho_sepalo": 3.5, "especie": "setosa"},
    ...
  ],
  "errors": []
}
```

**Notas:**
- Si hay errores de conversión de tipo, se deben reportar en el campo `errors` y no guardar el archivo de trabajo hasta que el usuario corrija.
- Si todo va bien, se guarda el archivo original, el de trabajo y los metadatos, y se devuelve una preview de las primeras filas.
- El backend debe borrar cualquier archivo temporal usado para el procesamiento.


### Fase 1: Pre-procesamiento interactivo al cargar archivos

#### Objetivo
Permitir al usuario editar los nombres de las cabeceras y los tipos de datos de cada columna antes de procesar el archivo, asegurando limpieza y control desde el primer momento.

#### Flujo detallado
1. El usuario arrastra un archivo (CSV o Excel) en la interfaz.
2. El frontend envía el archivo al backend mediante un endpoint de "preview".
3. El backend (pandas) extrae las primeras 5 filas y detecta los tipos de datos de cada columna.
4. El backend responde con:
   - Nombres de columnas detectados
   - Tipos de datos detectados
   - Primeras 5 filas para vista previa
5. El frontend muestra un modal editable donde el usuario puede:
   - Cambiar el nombre de cada columna
   - Cambiar el tipo de dato sugerido (con validación)
6. Si el usuario confirma, el frontend envía los cambios al backend para procesar el archivo completo y guardarlo como archivo de trabajo.
7. Si el usuario cancela, se borra el archivo temporal/subido.

#### Endpoints involucrados (ubicados en `app/api/endpoints.py`)
- `/api/preview_file` (POST):
  - Recibe el archivo subido.
  - Devuelve cabeceras, tipos detectados y primeras 5 filas.
- `/api/process_file` (POST):
  - Recibe el archivo original + cambios de cabeceras/tipos.
  - Procesa el archivo completo y lo guarda como archivo de trabajo.
- `/api/cancel_upload` (POST):
  - Limpia archivos temporales si el usuario cancela.

#### Archivos afectados
- `frontend/index.html`: Estructura del modal de pre-procesamiento.
- `frontend/app.js`: Lógica de UI, eventos, comunicación con backend.
- `frontend/style.css`: Estilos del modal.
- `app/api/endpoints.py`: Implementación de endpoints.
- `app/storage/file_storage.py`: Lógica de preview, procesamiento y limpieza.

#### Sugerencias y consideraciones técnicas
- La detección de tipos debe ser robusta (pandas).
- Validar que los tipos elegidos por el usuario sean compatibles.
- Guardar los cambios de cabeceras/tipos en un JSON asociado al archivo para trazabilidad.
- El modal debe mostrar advertencias si el tipo elegido no es compatible.
- Si el usuario elimina columnas en el modal, se reflejará en el archivo de trabajo.

---

### Detalle del endpoint `/api/preview_file`

**Objetivo:**
Permitir al frontend obtener una muestra de las primeras filas del archivo subido, junto con los nombres de columna y tipos de datos detectados, antes de procesar el archivo completo.

**Request (POST, multipart/form-data):**
```
file: <archivo_csv_o_excel>
```

**Response (application/json):**
```
{
  "columns": [
    { "name": "sepal_length", "dtype": "float64" },
    { "name": "sepal_width", "dtype": "float64" },
    { "name": "species", "dtype": "object" }
  ],
  "preview": [
    { "sepal_length": 5.1, "sepal_width": 3.5, "species": "setosa" },
    { "sepal_length": 4.9, "sepal_width": 3.0, "species": "setosa" },
    { "sepal_length": 4.7, "sepal_width": 3.2, "species": "setosa" },
    { "sepal_length": 4.6, "sepal_width": 3.1, "species": "setosa" },
    { "sepal_length": 5.0, "sepal_width": 3.6, "species": "setosa" }
  ]
}
```

**Notas:**
- El backend debe detectar automáticamente el tipo de archivo (csv/xlsx) y usar pandas para extraer la muestra y los tipos.
- Si hay error de formato, devolver un error claro.
- El frontend usará esta respuesta para construir el modal editable.

---

### Siguiente paso: Implementación del endpoint `/api/preview_file`

**Checklist de tareas:**
- [ ] Crear función auxiliar en `app/storage/file_storage.py` para:
    - Detectar tipo de archivo (csv/xlsx)
    - Leer primeras 5 filas con pandas
    - Detectar nombres y tipos de columnas
    - Devolver muestra y metadatos
- [ ] Crear endpoint en `app/api/endpoints.py` que reciba el archivo, llame a la función auxiliar y devuelva la respuesta esperada.
- [ ] Manejar errores de formato y devolver mensajes claros.
- [ ] Probar el endpoint con curl o Postman usando archivos de ejemplo.
- [ ] Documentar en este archivo (dev.md) el resultado de la prueba y cualquier decisión tomada.

**Cómo probar:**
1. Lanzar el backend.
2. Hacer una petición POST a `/api/preview_file` con un archivo csv/xlsx.
3. Comprobar que la respuesta tiene la estructura documentada arriba.
4. Probar con archivos mal formateados para validar los errores.

**Ejemplo de prueba con curl:**

```bash
curl -X POST "http://localhost:8000/api/preview_file" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@ruta/a/tu/archivo.csv"
```


**Qué esperar:**
- Si el archivo es válido, la respuesta será un JSON con las columnas detectadas y las primeras 5 filas, como en el ejemplo documentado.
- Si el archivo está mal formateado o la extensión no es soportada, la respuesta será un error 400 con un mensaje claro en el campo `detail`.

**Siguiente paso:**

**Resultado de la prueba (Postman):**
- El endpoint funciona correctamente usando la ruta `/preview_file`.
- Se subió un archivo CSV de ejemplo (`iris.csv`) y la respuesta fue un JSON con las columnas detectadas y las primeras 5 filas, tal como se esperaba.
- Ejemplo de respuesta recibida:
  ```json
  {
    "columns": [
      {"name": "sepal.length", "dtype": "float64"},
      {"name": "sepal.width", "dtype": "float64"},
      {"name": "petal.length", "dtype": "float64"},
      {"name": "petal.width", "dtype": "float64"},
      {"name": "variety", "dtype": "object"}
    ],
    "preview": [
      {"sepal.length": 5.1, "sepal.width": 3.5, "petal.length": 1.4, "petal.width": 0.2, "variety": "Setosa"},
      {"sepal.length": 4.9, "sepal.width": 3.0, "petal.length": 1.4, "petal.width": 0.2, "variety": "Setosa"},
      {"sepal.length": 4.7, "sepal.width": 3.2, "petal.length": 1.3, "petal.width": 0.2, "variety": "Setosa"},
      {"sepal.length": 4.6, "sepal.width": 3.1, "petal.length": 1.5, "petal.width": 0.2, "variety": "Setosa"},
      {"sepal.length": 5.0, "sepal.width": 3.6, "petal.length": 1.4, "petal.width": 0.2, "variety": "Setosa"}
    ]
  }
  ```

---

---
- Guardar los cambios de cabeceras/tipos en un JSON asociado al archivo para trazabilidad.
- El modal debe mostrar advertencias si el tipo elegido no es compatible.
- Si el usuario elimina columnas en el modal, se reflejará en el archivo de trabajo.

---

#### Subconjuntos y "sub-excels" (para fases posteriores)
- El usuario podrá crear subconjuntos de columnas ("sub-excels") desde el menú de edición.
- Cada subconjunto se guarda como un archivo de trabajo independiente, con el nombre elegido por el usuario (ej: `iris_no_length`).
- El usuario puede alternar entre el archivo original y los subconjuntos creados.
- Los metadatos de subconjuntos se guardan en JSON para trazabilidad.

---

### Fase 2: Selección dinámica de columnas y archivo de trabajo
- Permitir seleccionar/deseleccionar columnas desde el menú de edición.
- Generar archivo de trabajo temporal con solo las columnas seleccionadas.
- Archivos afectados:
  - `frontend/app.js` (UI de selección de columnas, lógica de generación de archivo de trabajo)
  - `app/storage/file_storage.py` (gestión de archivo temporal y lógica de selección)

### Fase 3: Migración de Pickle a Parquet
- Migrar el almacenamiento de DataFrames de .pkl a .parquet.
- Validar compatibilidad y funcionamiento en todo el flujo.
- Archivos afectados:
  - `app/storage/file_storage.py` (cambio de serialización/deserialización)
  - `requirements.txt` (agregar dependencias si es necesario, ej. pyarrow)

### Fase 4: Mejoras de UI y experiencia de usuario
- Mejorar la visualización de tipos de datos y cabeceras en el modal.
- Añadir validaciones y mensajes de ayuda.
- Archivos afectados:
  - `frontend/app.js`
  - `frontend/style.css`

### Fase 5: Refactor y documentación
- Actualizar documentación técnica y de usuario.
- Refactorizar código para mayor mantenibilidad.
- Archivos afectados:
  - `dev.md` (documentación de cambios y decisiones)
  - `README.md` (guía de uso y nuevas funcionalidades)
