from __future__ import annotations

import argparse
from pathlib import Path
from datetime import date

from backend.curator_agent import run


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Curatorial Opportunity Memo from signals."
    )
    parser.add_argument(
        "signals",
        type=Path,
        help="Path to JSON file containing signals.",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Path to write the Markdown memo.",
    )
    parser.add_argument(
        "--today",
        type=date.fromisoformat,
        default=None,
        help="Override today's date (ISO format).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(args.signals, args.output, today=args.today)


if __name__ == "__main__":
    main()
