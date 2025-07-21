# file_storage.py
# Funciones y clase para gestión de archivos y metadatos

from pathlib import Path
import pandas as pd
import json
import hashlib

class FileStorage:
    def delete_file(self, file_id: str, ext: str = None) -> None: # type: ignore
        """
        Elimina el archivo original (uploads), el procesado (processed) y el metadata (metadata) asociados al file_id.
        Si ext no se proporciona, intenta borrar .xlsx, .xls y .csv.
        """
        # Borrar metadata
        meta_path = self.metadata_dir / f"{file_id}.json"
        if meta_path.exists():
            meta_path.unlink()
        # Borrar procesado
        pkl_path = self.processed_dir / f"{file_id}.pkl"
        if pkl_path.exists():
            pkl_path.unlink()
        # Borrar original
        exts = [ext] if ext else [".xlsx", ".xls", ".csv"]
        for e in exts:
            orig_path = self.upload_dir / f"{file_id}{e}"
            if orig_path.exists():
                orig_path.unlink()
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

    def save_file(self, file_path: str | Path) -> str:
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
        dest_json = self.metadata_dir / f"{file_id}.json"
        with open(dest_json, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f"[LOG] 2. Metadata a guardar: {json.dumps(metadata, ensure_ascii=False)}")

        return file_id

    def load_dataframe(self, file_id: str) -> pd.DataFrame:
        return pd.read_pickle(self.processed_dir / f"{file_id}.pkl")

    def load_metadata(self, file_id: str) -> dict:
        with open(self.metadata_dir / f"{file_id}.json", "r") as f:
            return json.load(f)
