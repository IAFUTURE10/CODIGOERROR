from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
BASE_PATH = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))["base_path"].rstrip("/")


def relative_root(html_path: Path, target: Path) -> str:
    parent = html_path.parent
    parts = parent.relative_to(target).parts
    if not parts:
        return "."
    return "/".join(".." for _ in parts)


def patch_html(target: Path) -> None:
    for html_path in target.rglob("*.html"):
        root = relative_root(html_path, target)
        text = html_path.read_text(encoding="utf-8")
        text = text.replace(f'data-base-path="{BASE_PATH}"', f'data-base-path="{root}"')
        text = text.replace(f'="{BASE_PATH}/', f'="{root}/')
        text = text.replace(f"='{BASE_PATH}/", f"='{root}/")
        html_path.write_text(text, encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/make_desktop_copy.py <target-folder>")
    target = Path(sys.argv[1]).resolve()
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(DOCS, target)
    patch_html(target)
    print(f"Desktop-ready copy created at {target}")


if __name__ == "__main__":
    main()
