# Utility to load and cache ESB program data for all agents
import os
import json
from functools import lru_cache

ESB_JSON_PATH = os.path.join(os.path.dirname(__file__), '../../esb.json')

def get_esb_data():
    """Load and cache ESB program data from esb.json."""
    return _load_esb_json()

@lru_cache(maxsize=1)
def _load_esb_json():
    try:
        with open(ESB_JSON_PATH, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []
