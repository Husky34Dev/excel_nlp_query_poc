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