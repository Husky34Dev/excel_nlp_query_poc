# processor.py
# Funciones de procesamiento de datos y ejecución de código

import pandas as pd
from .sandbox import run_in_sandbox

def load_excel_schema(path: str):
    df = pd.read_excel(path)
    schema = {
        "columns": list(df.columns),
        "dtypes": df.dtypes.apply(lambda t: str(t)).to_dict()
    }
    return df, schema

def build_prompt(schema: dict, question: str) -> str:
    custom = schema.get("custom_prompt", "").strip()
    with open("prompts/base_prompt.txt", "r") as f:
        template = f.read()
    # system: instrucciones, definiciones, ejemplos
    if custom:
        system = custom + "\n\n" + template
    else:
        system = template
    system = system.format(
        columns=schema["columns"],
        dtypes=schema["dtypes"],
        question=""
    )
    # user: solo la pregunta
    user = question
    return system, user # type: ignore

def execute_code(df, code: str):
    print(f"[LOG] Código generado por LLM:\n{code}")
    code_clean = code.replace('```python', '').replace('```', '').strip()
    return run_in_sandbox(code_clean, df)
