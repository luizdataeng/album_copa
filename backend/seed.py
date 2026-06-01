import json
from pathlib import Path

import db

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_LIST = BASE_DIR / "data" / "selections.json"


def load_selections(path: Path) -> list:
    if not path.exists():
        raise FileNotFoundError(f"Missing selections file: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("Selections JSON must be a list")

    selections = []
    for item in data:
        if isinstance(item, str):
            name = item.strip()
            group = "Sem grupo"
        elif isinstance(item, dict):
            name = str(item.get("name", "")).strip()
            group = str(item.get("group", "Sem grupo")).strip() or "Sem grupo"
        else:
            continue

        if name:
            selections.append({"name": name, "group": group})

    return selections


def main() -> None:
    selections = load_selections(DEFAULT_LIST)
    if not selections:
        raise ValueError("Selections list is empty")
    db.init_db()
    names = [item["name"] for item in selections]
    removed = db.prune_selections(names)
    total = db.seed_db(selections)
    print(f"Removed {removed} rows")
    print(f"Seeded {total} rows")


if __name__ == "__main__":
    main()
