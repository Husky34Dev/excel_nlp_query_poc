
# endpoints.py
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from app.storage.file_storage import FileStorage
import tempfile
from pathlib import Path
from pydantic import BaseModel
from app.services.llm import GroqLLM
from app.services.processor import build_prompt,execute_code
import os
import json
from typing import Optional


router = APIRouter()
fs = FileStorage(base_dir="data_files")

from fastapi import Form

# Endpoint para subir archivos

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), name: str = Form(None)):
    # Crear archivo temporal
    filename = file.filename if file.filename is not None else ""
    suffix = Path(filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        file_id = fs.save_file(tmp_path)
        metadata = fs.load_metadata(file_id)
        # Guardar el nombre personalizado en los metadatos si se proporciona
        if name:
            metadata["name"] = name
            meta_path = os.path.join("data_files", "metadata", f"{file_id}.json")
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        return {"file_id": file_id, "metadata": metadata}
    except Exception as e:
        return {"error": str(e)}
    
@router.post("/preview_file")
async def preview_file(file: UploadFile = File(...)):
    """
    Devuelve una previsualización del archivo subido: cabeceras, tipos y primeras filas.
    No guarda el archivo ni los metadatos.
    """
    import pandas as pd
    filename = file.filename if file.filename is not None else ""
    suffix = Path(filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        # Detectar tipo de archivo y leer solo las primeras filas con pandas
        if suffix.lower() in [".csv", ".txt"]:
            df_preview = pd.read_csv(tmp_path, nrows=5)
            # Para obtener solo las cabeceras y tipos, leemos solo la cabecera
            df_header = pd.read_csv(tmp_path, nrows=0)
        elif suffix.lower() in [".xls", ".xlsx"]:
            df_preview = pd.read_excel(tmp_path, nrows=5)
            df_header = pd.read_excel(tmp_path, nrows=0)
        else:
            return {"error": f"Tipo de archivo no soportado: {suffix}"}

        columns = list(df_header.columns)
        dtypes = {col: str(df_preview[col].dtype) for col in columns}
        # Reemplazar NaN/inf por None para compatibilidad JSON
        import numpy as np
        df_preview_clean = df_preview.replace({np.nan: None, np.inf: None, -np.inf: None})
        preview_rows = df_preview_clean.to_dict(orient="records")

        # Intentar contar el número total de filas de forma eficiente
        n_rows = None
        try:
            if suffix.lower() in [".csv", ".txt"]:
                with open(tmp_path, "r", encoding="utf-8") as f:
                    n_rows = sum(1 for _ in f) - 1  # menos la cabecera
            elif suffix.lower() in [".xls", ".xlsx"]:
                # Para Excel, solo si openpyxl está disponible y el archivo no es enorme
                import openpyxl
                wb = openpyxl.load_workbook(tmp_path, read_only=True)
                ws = wb.active
                if ws is not None:
                    n_rows = ws.max_row - 1  # menos la cabecera
                else:
                    n_rows = None
        except Exception:
            n_rows = None

        return {
            "columns": columns,
            "dtypes": dtypes,
            "n_rows": n_rows,
            "preview": preview_rows
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

class QueryRequest(BaseModel):
    file_id: str
    question: str

@router.post("/query")
async def query_llm(data: QueryRequest):
    try:
        df = fs.load_dataframe(data.file_id)
        metadata = fs.load_metadata(data.file_id)

        system, user = build_prompt(metadata, data.question)
        llm = GroqLLM()
        code = llm.ask(system, user)

        result = execute_code(df, code)

        # Serialización numpy/int64/float64
        import numpy as np
        def to_native(val):
            if isinstance(val, np.generic):
                return val.item()
            if hasattr(val, 'to_dict'):
                return val.to_dict()
            if hasattr(val, 'tolist'):
                return val.tolist()
            if isinstance(val, dict):
                return {k: to_native(v) for k, v in val.items()}
            if isinstance(val, list):
                return [to_native(v) for v in val]
            return val

        return {
            "code": code,
            "result": to_native(result)
        }

    except Exception as e:
        return {"error": str(e)}

@router.get("/files")
async def list_files():
    metadata_dir = os.path.join("data_files", "metadata")
    files = []
    for fname in os.listdir(metadata_dir):
        if fname.endswith(".json"):
            file_id = fname.replace(".json", "")
            with open(os.path.join(metadata_dir, fname), "r", encoding="utf-8") as f:
                meta = json.load(f)
            # Si hay nombre personalizado, úsalo; si no, usa el file_id
            name = meta.get("name", file_id)
            files.append({
                "file_id": file_id,
                "name": name,
                "columns": meta["columns"],
                "dtypes": meta.get("dtypes", {}),
                "n_rows": meta["n_rows"],
                "custom_prompt": meta.get("custom_prompt", "")
            })
    return files


# Endpoint para borrar archivo
class DeleteRequest(BaseModel):
    file_id: str

@router.post("/delete_file")
async def delete_file(data: DeleteRequest):
    file_id = data.file_id
    try:
        from app.storage.file_storage import FileStorage
        storage = FileStorage()
        storage.delete_file(file_id)
        return {"success": True}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


# Endpoint para renombrar archivo

class RenameRequest(BaseModel):
    file_id: str
    name: str
    prompt: str = None # type: ignore


@router.post("/rename_file")
async def rename_file(data: RenameRequest):
    metadata_path = os.path.join("data_files", "metadata", f"{data.file_id}.json")
    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        meta["name"] = data.name
        if data.prompt is not None:
            meta["custom_prompt"] = data.prompt
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        return {"success": True}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
    
class ProcessColumnConfig(BaseModel):
    name: str  # nombre original
    new_name: Optional[str] = None  # nombre destino (puede ser igual al original)
    dtype: str  # tipo destino
    enabled: Optional[bool] = True  # si la columna se incluye o no

@router.post("/process_file")
async def process_file(
    file: UploadFile = File(None),
    file_id: str = Form(None),
    columns: str = Form(...),
    name: str = Form(None)
):
    """
    Procesa el archivo aplicando cambios de columnas (eliminación, renombrado, tipo).
    Recibe archivo o file_id + configuración de columnas (JSON string).
    Devuelve file_id, metadatos, preview y errores de conversión si los hay.
    """
    import pandas as pd
    import json
    fs = FileStorage(base_dir="data_files")

    # Parsear configuración de columnas
    try:
        columns_cfg = json.loads(columns)
        columns_cfg = [ProcessColumnConfig(**col) for col in columns_cfg]
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Error en el formato de columnas: {e}"})

    # Cargar archivo: si file_id, cargar de disco; si file, guardar temporalmente
    if file_id:
        # Cargar DataFrame desde file_id
        try:
            df = fs.load_dataframe(file_id)
        except Exception as e:
            return JSONResponse(status_code=400, content={"error": f"No se pudo cargar el archivo: {e}"})
    elif file:
        # Guardar archivo temporal y cargar
        import tempfile
        from pathlib import Path
        suffix = Path(file.filename).suffix if file.filename else ".csv"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
        try:
            df = pd.read_csv(tmp_path) if suffix.lower() == ".csv" else pd.read_excel(tmp_path)
        except Exception as e:
            return JSONResponse(status_code=400, content={"error": f"No se pudo leer el archivo: {e}"})
        finally:
            import os
            try:
                os.remove(tmp_path)
            except Exception:
                pass
    else:
        return JSONResponse(status_code=400, content={"error": "Debe enviar un archivo o un file_id."})

    # Procesar y guardar usando FileStorage
    result = fs.process_and_save(
        df,
        [c.dict() for c in columns_cfg],
        base_file_id=file_id,
        name=name
    )
    return result