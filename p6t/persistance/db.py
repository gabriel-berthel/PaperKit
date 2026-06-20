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


def _hash_key(name: str) -> str:
    return hashlib.sha256(name.encode("utf-8")).hexdigest()[:16]


def push(name: str, location: str, value):

    print(f"Pushing {name} to {location}")

    _ensure_init()
    folder, version = _resolve_location(location)

    key = _hash_key(name)
    filename = f"{key}:{version}.pkl"
    path = folder / filename

    data = {
        "name": name,
        "location": location,
        "version": version,
        "data": value,
    }

    with open(path, "wb") as f:
        pickle.dump(data, f)

    return path  # optional, useful for debugging


def get(name: str, location: str):
    _ensure_init()
    folder, version = _resolve_location(location)

    key = _hash_key(name)
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