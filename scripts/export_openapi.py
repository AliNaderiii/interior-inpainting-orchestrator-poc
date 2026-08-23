from __future__ import annotations

import json
from pathlib import Path

from inpainting_poc.api import app

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "openapi-v0.2.0.json"


def main() -> None:
    OUTPUT.write_text(
        json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"OpenAPI contract written to {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
