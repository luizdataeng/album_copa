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
            size = None
        elif isinstance(item, dict):
            name = str(item.get("name", "")).strip()
            group = str(item.get("group", "Sem grupo")).strip() or "Sem grupo"
            size = item.get("size")
        else:
            continue

        if name:
            lower_name = name.lower()
            prefix = name.split("|", 1)[0].strip()
            entry_start = None
            entry_end = None
            if "[cc]" in lower_name:
                entry_start = 1
                entry_end = 14
            if "[fwc]" in lower_name:
                if prefix.isdigit() and int(prefix) == 1:
                    entry_start = 1
                    entry_end = 8
                elif prefix.isdigit() and int(prefix) == 106:
                    entry_start = 9
                    entry_end = 19
            entry = {"name": name, "group": group}
            if entry_start is not None and entry_end is not None:
                entry["start"] = entry_start
                entry["end"] = entry_end
            if size:
                entry["size"] = size
            selections.append(entry)

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
