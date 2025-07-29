# file_storage.py
# Funciones y clase para gestión de archivos y metadatos

from pathlib import Path
import pandas as pd
import json
import hashlib
import unicodedata
import numpy as np
class FileStorage:

    def _process_columns(self, df: pd.DataFrame, columns_cfg: list) -> tuple:
        """
        Procesa el DataFrame según columns_cfg: filtra, renombra, normaliza y cambia tipos.
        Devuelve df_proc, preview, errors, columns, dtypes
        """
        
        # 1. Filtrar columnas habilitadas
        enabled_cols = [c for c in columns_cfg if c.get('enabled', True)]
        col_map = {c['name']: c.get('new_name') or c['name'] for c in enabled_cols}
        dtype_map = {c['name']: c['dtype'] for c in enabled_cols}
        # 2. Subset y renombrado
        df_proc = df[[c['name'] for c in enabled_cols]].copy()
        df_proc.rename(columns=col_map, inplace=True)
        # 3. Normalizar nombres
        def normalize_col(col):
            col = str(col)
            col = unicodedata.normalize('NFKD', col).encode('ASCII', 'ignore').decode('ASCII')
            col = col.lower().replace(' ', '_')
            return col
        df_proc.columns = [normalize_col(c) for c in df_proc.columns]
        # 4. Cambiar tipos y recolectar errores
        errors = []
        for col, dtype in zip(df_proc.columns, [dtype_map[c['name']] for c in enabled_cols]):
            try:
                if dtype == 'int':
                    df_proc[col] = pd.to_numeric(df_proc[col], errors='raise').astype('Int64')
                elif dtype == 'float':
                    df_proc[col] = pd.to_numeric(df_proc[col], errors='raise').astype('float64')
                elif dtype == 'str':
                    df_proc[col] = df_proc[col].astype(str)
                elif dtype == 'bool':
                    df_proc[col] = df_proc[col].astype('boolean')
                elif dtype == 'datetime':
                    df_proc[col] = pd.to_datetime(df_proc[col], errors='raise')
                elif dtype == 'object':
                    pass
                else:
                    raise ValueError(f"Tipo no soportado: {dtype}")
            except Exception as e:
                errors.append({"column": col, "error": str(e)})
        preview = df_proc.head(5).replace({np.nan: None, np.inf: None, -np.inf: None}).to_dict(orient="records")
        columns_utf8 = [str(col) for col in df_proc.columns]
        dtypes_utf8 = {str(col): str(df_proc.dtypes[col]) for col in df_proc.columns}
        return df_proc, preview, errors, columns_utf8, dtypes_utf8

    def process_and_save(self, df: pd.DataFrame, columns_cfg: list, base_file_id: str = None, name: str = None) -> dict: # type: ignore
        """
        Aplica eliminación, renombrado, cambio de tipo y normalización de columnas según columns_cfg.
        Guarda el archivo procesado y los metadatos. Devuelve file_id, metadatos, preview y errores.
        """
        import uuid
        df_proc, preview, errors, columns_utf8, dtypes_utf8 = self._process_columns(df, columns_cfg)
        if errors:
            return {
                "success": False,
                "file_id": None,
                "columns": [{"name": c, "dtype": str(df_proc[c].dtype)} for c in df_proc.columns],
                "preview": preview,
                "errors": errors
            }
        file_id = base_file_id or uuid.uuid4().hex
        dest_parquet = self.processed_dir / f"{file_id}.parquet"
        df_proc.to_parquet(dest_parquet, index=False)
        metadata = {
            "columns": columns_utf8,
            "dtypes": dtypes_utf8,
            "n_rows": len(df_proc),
            "source_ext": ".parquet",
        }
        if name:
            metadata["name"] = name
        dest_json = self.metadata_dir / f"{file_id}.json"
        with open(dest_json, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        return {
            "success": True,
            "file_id": file_id,
            "columns": [{"name": c, "dtype": str(df_proc[c].dtype)} for c in df_proc.columns],
            "preview": preview,
            "errors": []
        }
    def delete_file(self, file_id: str, ext: str = None) -> None: # type: ignore
        """
        Elimina el archivo original (uploads), el procesado (processed: .pkl y .parquet) y el metadata (metadata) asociados al file_id.
        Si ext no se proporciona, intenta borrar .xlsx, .xls y .csv.
        """
        # Borrar metadata
        meta_path = self.metadata_dir / f"{file_id}.json"
        if meta_path.exists():
            meta_path.unlink()
        # Borrar procesados (.pkl y .parquet)
        pkl_path = self.processed_dir / f"{file_id}.pkl"
        if pkl_path.exists():
            pkl_path.unlink()
        parquet_path = self.processed_dir / f"{file_id}.parquet"
        if parquet_path.exists():
            parquet_path.unlink()
        # Borrar original
        exts = [ext] if ext else [".xlsx", ".xls", ".csv"]
        for e in exts:
            orig_path = self.upload_dir / f"{file_id}{e}"
            if orig_path.exists():
                orig_path.unlink()
    # Si se implementa un método rename_file, también debe renombrar .parquet además de .pkl y metadatos.
    def __init__(self, base_dir="data_files"):
        self.base_dir = Path(base_dir)
        self.upload_dir = self.base_dir / "uploads"
        self.processed_dir = self.base_dir / "processed"
        self.metadata_dir = self.base_dir / "metadata"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def generate_file_id(self, filename: str) -> str:
        return hashlib.md5(filename.encode()).hexdigest()

    def save_file(self, file_path: str | Path, name: str = None) -> str: # type: ignore
        import unicodedata
        def normalize_col(col):
            col = str(col)
            col = unicodedata.normalize('NFKD', col).encode('ASCII', 'ignore').decode('ASCII')
            col = col.lower().replace(' ', '_')
            return col
        file_id = self.generate_file_id(Path(file_path).name)
        ext = Path(file_path).suffix.lower()

        # 1. Cargar archivo
        df = None
        if ext in [".xlsx", ".xls"]:
            try:
                df = pd.read_excel(file_path)
            except Exception as e:
                print(f"[LOG] Error al leer Excel: {e}")
        elif ext == ".csv":
            encodings = ["utf-8-sig", "utf-8", "latin1", "cp1252"]
            for enc in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=enc)
                    print(f"[LOG] CSV leído con encoding: {enc}")
                    break
                except Exception as e:
                    print(f"[LOG] Fallo con encoding {enc}: {e}")
        else:
            print(f"[LOG] Extensión no soportada: {ext}")

        if df is None:
            raise ValueError("No se pudo cargar el archivo. Abortando procesamiento.")
        # Normalizo las cabeceras
        df.columns = [normalize_col(col) for col in df.columns]
        print(f"[LOG] 1. Nombres de columnas normalizadas: {list(df.columns)}")

        # 2. Guardar original
        dest_original = self.upload_dir / f"{file_id}{ext}"
        df.to_csv(dest_original, index=False) if ext == ".csv" else df.to_excel(dest_original, index=False)

        # 3. Guardar como .pkl
        dest_pkl = self.processed_dir / f"{file_id}.pkl"
        df.to_pickle(dest_pkl)

        # 4. Guardar metadata
        # Reconstruyo los nombres de columna y dtypes usando df.columns para evitar errores de codificación
        columns_utf8 = [str(col) for col in df.columns]
        dtypes_utf8 = {str(col): str(df.dtypes[col]) for col in df.columns}
        metadata = {
            "columns": columns_utf8,
            "dtypes": dtypes_utf8,
            "n_rows": len(df),
            "source_ext": ext,
        }
        if name:
            metadata["name"] = name
        dest_json = self.metadata_dir / f"{file_id}.json"
        with open(dest_json, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f"[LOG] 2. Metadata a guardar: {json.dumps(metadata, ensure_ascii=False)}")

        return file_id

    def load_dataframe(self, file_id: str) -> pd.DataFrame:
        pkl_path = self.processed_dir / f"{file_id}.pkl"
        parquet_path = self.processed_dir / f"{file_id}.parquet"
        if pkl_path.exists():
            return pd.read_pickle(pkl_path)
        elif parquet_path.exists():
            return pd.read_parquet(parquet_path)
        else:
            raise FileNotFoundError(f"No se encontró archivo procesado para file_id: {file_id}")

    def load_metadata(self, file_id: str) -> dict:
        with open(self.metadata_dir / f"{file_id}.json", "r") as f:
            return json.load(f)

    def create_subset(self, parent_file_id: str, columns_cfg: list, name: str = None) -> dict: # type: ignore
        """
        Crea y guarda un subconjunto hijo a partir de un archivo padre procesado.
        Valida duplicados, normaliza nombres, guarda Parquet y metadatos.
        """
        import unicodedata
        import numpy as np
        import uuid
        # 1. Cargar padre
        df_parent = self.load_dataframe(parent_file_id)
        meta_parent = self.load_metadata(parent_file_id)
        # 2. Procesar columnas (reutiliza lógica)
        df_subset, preview, errors, columns_utf8, dtypes_utf8 = self._process_columns(df_parent, columns_cfg)
        if errors:
            return {
                "success": False,
                "file_id": None,
                "columns": [{"name": c, "dtype": str(df_subset[c].dtype)} for c in df_subset.columns],
                "preview": preview,
                "errors": errors
            }
        # 4. Validar duplicados (subconjunto idéntico ya existe)
        # Se busca en los hijos del padre si existe uno con las mismas columnas
        parent_meta_path = self.metadata_dir / f"{parent_file_id}.json"
        hijos = []
        if parent_meta_path.exists():
            with open(parent_meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                hijos = meta.get("children", [])
        # Usar columns_utf8 (ya normalizadas) para comparar
        subset_cols_norm = columns_utf8
        for hijo_id in hijos:
            hijo_meta_path = self.metadata_dir / f"{hijo_id}.json"
            if hijo_meta_path.exists():
                with open(hijo_meta_path, "r", encoding="utf-8") as f:
                    hijo_meta = json.load(f)
                    if hijo_meta.get("columns", []) == subset_cols_norm:
                        return {
                            "success": False,
                            "file_id": None,
                            "columns": [{"name": c, "dtype": str(df_subset[c].dtype)} for c in df_subset.columns],
                            "preview": preview,
                            "errors": [{"error": "Ya existe un subconjunto idéntico."}]
                        }
        # 5. Guardar subset y metadatos
        file_id = uuid.uuid4().hex
        dest_parquet = self.processed_dir / f"{file_id}.parquet"
        df_subset.to_parquet(dest_parquet, index=False)
        columns_utf8 = [str(col) for col in df_subset.columns]
        dtypes_utf8 = {str(col): str(df_subset.dtypes[col]) for col in df_subset.columns}
        metadata = {
            "columns": columns_utf8,
            "dtypes": dtypes_utf8,
            "n_rows": len(df_subset),
            "source_ext": ".parquet",
            "parent_id": parent_file_id
        }
        if name:
            metadata["name"] = name
        dest_json = self.metadata_dir / f"{file_id}.json"
        with open(dest_json, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        # 6. Actualizar metadatos del padre para añadir el hijo
        if parent_meta_path.exists():
            with open(parent_meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            meta.setdefault("children", []).append(file_id)
            with open(parent_meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
        return {
            "success": True,
            "file_id": file_id,
            "columns": [{"name": c, "dtype": str(df_subset[c].dtype)} for c in df_subset.columns],
            "preview": preview,
            "errors": []
        }
