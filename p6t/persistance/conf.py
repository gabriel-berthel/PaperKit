# Central config / registry
from pathlib import Path


DB_CONFIG = {
    "base_dir": Path("./db"),
    "locations": {
        # logical name -> folder name
        "parsing": "parsing",
        "normalizing": "normalizing",
    },
    "versions": {
        "parsing": "v0",
        "normalizing": "0",
    }
}
