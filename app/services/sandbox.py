from RestrictedPython import compile_restricted
from RestrictedPython.Guards import safe_builtins, guarded_unpack_sequence
import pandas as pd

def run_in_sandbox(code: str, df: pd.DataFrame) -> any: # type: ignore
    """
    Ejecuta código generado por LLM en un entorno seguro.
    Solo expone 'df' y espera que el resultado esté en 'result'.

    :param code: código Python generado por el LLM.
    :param df: DataFrame preprocesado.
    :return: valor de la variable 'result' generada por el código, o error.
    """
    print("[SANDBOX] Compilando código restringido...")
    try:
        byte_code = compile_restricted(code, filename="<sandbox>", mode="exec")
    except SyntaxError as e:
        print(f"[SANDBOX] Error de sintaxis: {e}")
        return f"❌ Syntax error: {e}"

    # Entorno seguro para la ejecución
    print("[SANDBOX] Preparando entorno seguro...")
    from RestrictedPython.Eval import default_guarded_getitem, default_guarded_getattr
    from RestrictedPython.Eval import default_guarded_getiter
    exec_globals = {
        "__builtins__": safe_builtins,
        "_getitem_": default_guarded_getitem,
        "_getattr_": default_guarded_getattr,
        "_getiter_": default_guarded_getiter,
        "_write_": lambda x: x,  # Dummy para evitar error de salida estándar
        "_iter_unpack_sequence_": guarded_unpack_sequence  # Esto habilita for a, b in ...
    }
    exec_locals = {
        "df": df,
        "pd": pd,
    }
    print("[SANDBOX] Ejecutando código en sandbox...")
    try:
        exec(byte_code, exec_globals, exec_locals)
    except Exception as e:
        print(f"[SANDBOX] Error de ejecución: {e}")
        return f"❌ Runtime error: {e}"
    print("[SANDBOX] Código ejecutado. Extrayendo resultado...")
    # Utilidad para convertir cualquier resultado en tipos nativos serializables
    def to_native(val):
        import numpy as np
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
        if isinstance(val, (str, int, float, bool)):
            return val
        return str(val)

    # Extraer resultado y convertirlo
    if "result" in exec_locals:
        print("[SANDBOX] Resultado encontrado.")
        return to_native(exec_locals["result"])
    else:
        print("[SANDBOX] No se definió la variable 'result'.")
        return "⚠️ El código no definió la variable 'result'."
