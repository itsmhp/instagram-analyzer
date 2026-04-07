from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_gui() -> None:
    from ui.dashboard import Dashboard
    Dashboard().mainloop()


def run_cli(export_path: Path) -> None:
    from core.analyzer import run_analysis

    result = run_analysis(export_path)

    print(f"\n{'═' * 60}")
    print(f"  Instagram Analyzer  —  Analysis Report")
    print(f"{'═' * 60}")
    print(f"  Followers:           {result.follower_count:>6,}")
    print(f"  Following:           {result.following_count:>6,}")
    print(f"  Follow Ratio:        {result.ratio:>9.2f}")
    print(f"  Not Following Back:  {len(result.not_following_back):>6,}")
    print(f"  Fans (one-way):      {len(result.fans):>6,}")
    print(f"  Mutual:              {len(result.mutual):>6,}")
    print(f"  Blocked:             {len(result.blocked):>6,}")
    print(f"{'═' * 60}\n")

    if result.not_following_back:
        print(f"── NOT FOLLOWING BACK ({len(result.not_following_back)}) ──")
        for i, r in enumerate(result.not_following_back, 1):
            ts = r.timestamp.strftime("%Y-%m-%d") if r.timestamp else "unknown date"
            print(f"  {i:4}.  {r.username:<32}  followed on {ts}")

    if result.skipped_entries:
        print(f"\n[!] {result.skipped_entries} malformed entries were skipped during parsing.")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Instagram Analyzer — analyze your Instagram data export.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py                              # Launch GUI dashboard\n"
            "  python main.py -e ./instagram-export/      # CLI report\n"
        ),
    )
    ap.add_argument(
        "--export-path", "-e",
        type=Path, default=None,
        help="Path to the Instagram export folder. Omit to launch the GUI.",
    )
    args = ap.parse_args()

    if args.export_path is not None:
        if not args.export_path.is_dir():
            print(f"Error: '{args.export_path}' is not a directory.", file=sys.stderr)
            sys.exit(1)
        run_cli(args.export_path)
    else:
        run_gui()


if __name__ == "__main__":
    main()
