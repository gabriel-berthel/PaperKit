import pickle
import hashlib
from pathlib import Path
from p6t.persistance.conf import DB_CONFIG

def _ensure_init():
    for loc in DB_CONFIG["locations"].values():
        (DB_CONFIG["base_dir"] / loc).mkdir(parents=True, exist_ok=True)

def _resolve_location(location: str) -> tuple[Path, str]:
    """
    Returns:
        (folder_path, version)
    """
    if location not in DB_CONFIG["locations"]:
        raise ValueError(f"Unknown location: {location}")

    folder = DB_CONFIG["base_dir"] / DB_CONFIG["locations"][location]
    version = DB_CONFIG["versions"][location]
    return folder, version

def db_push(hash: str, location: str, value):

    print(f"Pushing {hash} to {location}")

    _ensure_init()
    folder, version = _resolve_location(location)

    key = hash
    filename = f"{key}:{version}.pkl"
    path = folder / filename

    data = {
        "name": hash,
        "location": location,
        "version": version,
        "data": value,
    }

    with open(path, "wb") as f:
        pickle.dump(data, f)

    return path  # optional, useful for debugging

def hash_doc(path):
    with open(path, "rb") as f:
        pdf_bytes = f.read()
        
    return hashlib.sha256(pdf_bytes).hexdigest()

def db_get(pdf_path, location: str):
    _ensure_init()
    folder, version = _resolve_location(location)

    key = hash_doc(pdf_path)
    path = folder / f"{key}:{version}.pkl"

    if not path.exists():
        return None

    with open(path, "rb") as f:
        return pickle.load(f)


def list_all(location: str):
    _ensure_init()
    folder, _ = _resolve_location(location)

    if not folder.exists():
        return []

    out = []
    for file in folder.glob("*.pkl"):
        with open(file, "rb") as f:
            out.append(pickle.load(f))
    return out