"""Still-capture runner for the Donggu wake-word demo."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("PYTHONWARNINGS", "ignore")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from rich.console import Console

from demo.video_demo_runner import SCENES, _render_vertical_card
from src.router.router import Router


def main() -> None:
    console = Console(width=96)
    router = Router(privacy_mode=True)
    scenes = [scene for scene in SCENES if scene.scene_id in {"01", "04"}]

    for index, scene in enumerate(scenes):
        _render_vertical_card(console, router, scene, header=False)
        if index < len(scenes) - 1:
            console.print()
            time.sleep(0.4)


if __name__ == "__main__":
    main()
