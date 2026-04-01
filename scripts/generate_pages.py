"""Generate landing pages from index.json and addons_meta.json.

Reads index.json and scripts/addons_meta.json, then updates the marker regions
in ja/README.md and en/README.md with the current addon list.

Usage:
    python scripts/generate_pages.py
"""

import json
from pathlib import Path
from urllib.parse import quote

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = REPO_ROOT / "index.json"
META_PATH = Path(__file__).resolve().parent / "addons_meta.json"

START_MARKER = "<!-- EXTENSIONS_LIST_START -->"
END_MARKER = "<!-- EXTENSIONS_LIST_END -->"

PAID_START_MARKER = "<!-- PAID_LIST_START -->"
PAID_END_MARKER = "<!-- PAID_LIST_END -->"
PAID_PATH = Path(__file__).resolve().parent / "paid_addons.json"


def load_index() -> dict:
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_meta() -> dict:
    with open(META_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_section(entry: dict, meta: dict, lang: str) -> str:
    """1つのアドオンについてマークダウンセクションを生成する。"""
    addon_id = entry["id"]
    name = entry["name"]
    version = entry["version"]
    blender_min = entry["blender_version_min"]
    archive_url = entry["archive_url"]

    addon_meta = meta.get(addon_id, {})
    desc_key = f"description_{lang}"
    description = addon_meta.get(desc_key, entry.get("tagline", ""))
    repo_url = addon_meta.get("repo_url", "")
    booth_url = addon_meta.get("booth_url", "")

    # ドラッグ&ドロップ対応リンク
    index_url = archive_url.rsplit("/", 2)[0] + "/index.json"
    install_url = f"{archive_url}?repository={quote(index_url, safe='')}&blender_version_min={blender_min}"

    # "4.2.0" -> "4.2"
    parts = blender_min.split(".")[:2]
    blender_short = f"{parts[0]}.{parts[1]}" if len(parts) == 2 else blender_min
    blender_label = f"(Blender ver. {blender_short}+)"

    lines = [
        f"### {name}",
        "",
        description,
        "",
        f"**Version:** {version} {blender_label}",
        "",
    ]

    if lang == "ja":
        lines.append(f"[ダウンロード (v{version})]({install_url})")
    else:
        lines.append(f"[Download (v{version})]({install_url})")

    links = []
    if repo_url:
        links.append(f"[GitHub]({repo_url})")
    if booth_url:
        links.append(f"[BOOTH]({booth_url})")
    if links:
        lines.append("")
        lines.append(" | ".join(links))

    return "\n".join(lines)


def generate_list(entries: list, meta: dict, lang: str) -> str:
    """全アドオンのリストを生成する。"""
    sections = []
    for entry in entries:
        sections.append(generate_section(entry, meta, lang))
    return "\n\n".join(sections)


def update_readme(readme_path: Path, content: str, start_marker: str = START_MARKER, end_marker: str = END_MARKER) -> None:
    """README.md のマーカー間を差し替える。"""
    text = readme_path.read_text(encoding="utf-8")

    start_idx = text.find(start_marker)
    end_idx = text.find(end_marker)

    if start_idx == -1 or end_idx == -1:
        print(f"Warning: markers not found in {readme_path}, skipping")
        return

    new_text = (
        text[: start_idx + len(start_marker)]
        + "\n\n"
        + content
        + "\n\n"
        + text[end_idx:]
    )
    readme_path.write_text(new_text, encoding="utf-8")
    print(f"Updated {readme_path}")


def load_paid() -> list:
    if not PAID_PATH.exists():
        return []
    with open(PAID_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_paid_section(addon: dict, lang: str) -> str:
    """有料アドオン1つについてマークダウンセクションを生成する。"""
    name = addon["name"]
    desc_key = f"description_{lang}"
    description = addon.get(desc_key, "")
    booth_url = addon.get("booth_url", "")

    lines = [
        f"### {name}",
        "",
        description,
        "",
    ]

    if booth_url:
        if lang == "ja":
            lines.append(f"[BOOTH で購入]({booth_url})")
        else:
            lines.append(f"[Buy on BOOTH]({booth_url})")

    return "\n".join(lines)


def generate_paid_list(addons: list, lang: str) -> str:
    """有料アドオンのリストを生成する。"""
    sections = []
    for addon in addons:
        sections.append(generate_paid_section(addon, lang))
    return "\n\n".join(sections)


def main() -> None:
    index = load_index()
    meta = load_meta()
    paid = load_paid()
    entries = index.get("data", [])

    for lang in ("ja", "en"):
        readme_path = REPO_ROOT / lang / "README.md"
        if not readme_path.exists():
            print(f"Warning: {readme_path} not found, skipping")
            continue
        content = generate_list(entries, meta, lang)
        update_readme(readme_path, content)

        if paid:
            paid_content = generate_paid_list(paid, lang)
            update_readme(readme_path, paid_content, PAID_START_MARKER, PAID_END_MARKER)


if __name__ == "__main__":
    main()
