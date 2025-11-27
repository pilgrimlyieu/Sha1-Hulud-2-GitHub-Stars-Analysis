"""Top-level CLI wrapper for extraction and encryption tasks."""

import argparse
import sys
from pathlib import Path

# ensure `src` is on sys.path so `from attack import ...` works when running from repo root
sys.path.insert(0, str(Path(__file__).parent.joinpath("src")))

from attack import extract_main, encrypt_file, load_config


def main():
    parser = argparse.ArgumentParser(
        description="Extract or encrypt GitHub star attack data"
    )
    parser.add_argument(
        "--extract", action="store_true", help="Run data extraction from GitHub"
    )
    parser.add_argument(
        "--encrypt", action="store_true", help="Encrypt existing unencrypted CSV"
    )
    parser.add_argument("--config", type=str, default=None, help="Path to config.json")
    args = parser.parse_args()

    load_config(args.config)

    if args.extract:
        extract_main(args.config)

    if args.encrypt:
        encrypt_file(config_path=args.config)


if __name__ == "__main__":
    main()
