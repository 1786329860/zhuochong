import os
import json
from typing import Dict, Any

def config_path() -> str:
    base = os.getenv("APPDATA") or os.path.expanduser("~")
    d = os.path.join(base, "XiaoLingPet")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "config.json")

def load_config() -> Dict[str, Any]:
    p = config_path()
    if os.path.isfile(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_config(cfg: Dict[str, Any]) -> None:
    p = config_path()
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
