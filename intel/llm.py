# llm.py - one place to call Ollama: thinking mode OFF (much faster) + small context
import ollama
from .config import MODEL
_think_ok = None
def generate(**kw):
    global _think_ok
    kw.setdefault("options", {"num_ctx": 4096, "temperature": 0.2})
    if _think_ok is None:                       # older Ollama versions reject think=; test once
        try: ollama.generate(model=MODEL, prompt="hi", think=False, options={"num_predict": 1}); _think_ok = True
        except TypeError: _think_ok = False
        except Exception: _think_ok = True      # e.g. model doesn't think - fine
    if _think_ok: kw["think"] = False
    return ollama.generate(model=MODEL, **kw)
