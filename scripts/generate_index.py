"""Generate index.json for the Blender Extensions Repository.

Usage:
    python scripts/generate_index.py add <addon_id> <version>
    python scripts/generate_index.py backfill
"""

import hashlib
import json
import os
import sys
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = REPO_ROOT / "index.json"

# blender_manifest.toml のフィールドのうち index.json にそのままコピーするもの
COPY_FIELDS = [
    "schema_version",
    "id",
    "name",
    "tagline",
    "version",
    "type",
    "maintainer",
    "license",
    "blender_version_min",
]

# あればコピーするオプショナルフィールド
OPTIONAL_FIELDS = [
    "blender_version_max",
    "website",
    "copyright",
    "permissions",
    "tags",
    "platforms",
]


def load_index() -> dict:
    """既存の index.json を読み込む。なければ空で初期化。"""
    if INDEX_PATH.exists():
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"version": "v1", "blocklist": [], "data": []}


def save_index(index: dict) -> None:
    """index.json を書き出す。"""
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
        f.write("\n")


def extract_manifest(zip_path: Path) -> dict:
    """zip 内の blender_manifest.toml を抽出して TOML パースする。"""
    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in zf.namelist():
            if name.endswith("blender_manifest.toml"):
                data = zf.read(name)
                return tomllib.loads(data.decode("utf-8"))
    raise FileNotFoundError(f"blender_manifest.toml not found in {zip_path}")


def compute_archive_fields(zip_path: Path, addon_id: str) -> dict:
    """archive_url, archive_size, archive_hash を計算する。"""
    base_url = os.environ.get("PAGES_URL", "").rstrip("/")
    if base_url:
        archive_url = f"{base_url}/{addon_id}/{zip_path.name}"
    else:
        archive_url = f"./{addon_id}/{zip_path.name}"
    file_bytes = zip_path.read_bytes()
    return {
        "archive_url": archive_url,
        "archive_size": len(file_bytes),
        "archive_hash": "sha256:" + hashlib.sha256(file_bytes).hexdigest(),
    }


def build_entry(manifest: dict, archive_fields: dict) -> dict:
    """blender_manifest.toml と archive 情報から index.json エントリを生成する。"""
    entry = {}
    for field in COPY_FIELDS:
        entry[field] = manifest[field]
    for field in OPTIONAL_FIELDS:
        if field in manifest:
            entry[field] = manifest[field]
    entry.update(archive_fields)
    return entry


def upsert_entry(data: list, entry: dict) -> list:
    """同一 id のエントリがあれば上書き、なければ追加する。"""
    addon_id = entry["id"]
    for i, existing in enumerate(data):
        if existing["id"] == addon_id:
            data[i] = entry
            return data
    data.append(entry)
    return data


def parse_version(version_str: str) -> tuple:
    """バージョン文字列をタプルに変換して比較可能にする。"""
    return tuple(int(x) for x in version_str.split("."))


def cmd_add(addon_id: str, version: str) -> None:
    """add モード: 指定バージョンの zip から差分追加。"""
    zip_path = REPO_ROOT / addon_id / f"{addon_id}-{version}.zip"
    if not zip_path.exists():
        print(f"Error: {zip_path} not found", file=sys.stderr)
        sys.exit(1)

    manifest = extract_manifest(zip_path)
    archive_fields = compute_archive_fields(zip_path, addon_id)
    entry = build_entry(manifest, archive_fields)

    index = load_index()
    index["data"] = upsert_entry(index["data"], entry)
    save_index(index)
    print(f"Updated {addon_id} to {version}")


def cmd_backfill() -> None:
    """backfill モード: 各フォルダの最新 zip を index.json に追加。"""
    index = load_index()
    existing_ids = {e["id"] for e in index["data"]}

    for folder in sorted(REPO_ROOT.iterdir()):
        if not folder.is_dir():
            continue
        # 隠しフォルダ、scripts、.github 等をスキップ
        if folder.name.startswith(".") or folder.name in ("scripts", "ja", "en", "public"):
            continue

        zips = sorted(folder.glob("*.zip"))
        if not zips:
            continue

        # 各 zip から manifest を読み、最新バージョンを特定
        best_zip = None
        best_version = None
        for zp in zips:
            try:
                manifest = extract_manifest(zp)
            except FileNotFoundError:
                continue
            ver = parse_version(manifest["version"])
            if best_version is None or ver > best_version:
                best_version = ver
                best_zip = zp

        if best_zip is None:
            continue

        manifest = extract_manifest(best_zip)
        addon_id = manifest["id"]

        # 既存エントリがあればスキップ
        if addon_id in existing_ids:
            print(f"Skipping {addon_id} (already in index)")
            continue

        archive_fields = compute_archive_fields(best_zip, addon_id)
        entry = build_entry(manifest, archive_fields)
        index["data"].append(entry)
        existing_ids.add(addon_id)
        print(f"Added {addon_id} {manifest['version']}")

    save_index(index)


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    if command == "add":
        if len(sys.argv) != 4:
            print("Usage: generate_index.py add <addon_id> <version>", file=sys.stderr)
            sys.exit(1)
        cmd_add(sys.argv[2], sys.argv[3])
    elif command == "backfill":
        cmd_backfill()
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
