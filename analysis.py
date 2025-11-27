"""Thin CLI wrapper for the analysis module."""

import argparse
import sys
from pathlib import Path

# ensure `src` is on sys.path so `from attack import ...` works when running from repo root
sys.path.insert(0, str(Path(__file__).parent.joinpath("src")))

from attack import analyze_attack_data, load_config


def main():
    parser = argparse.ArgumentParser(description="Analyze encrypted attack data")
    parser.add_argument("--config", type=str, default=None, help="Path to config.json")
    parser.add_argument(
        "--csv", type=str, default=None, help="Path to encrypted CSV (overrides config)"
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    analyze_attack_data(
        main_csv_path=(args.csv or cfg.get("encrypted_output")),
        awesome_files=cfg.get("awesome_files"),
        output_dir=cfg.get("output_dir"),
        config_path=args.config,
    )


if __name__ == "__main__":
    main()