"""
Encryption utilities: deterministic anonymization of victim usernames.
"""

import hmac
import hashlib
from pathlib import Path
import polars as pl
from .config import load_config


def _hash_username(username: str, key: str) -> str | None:
    if username is None:
        return None
    return hmac.new(
        key.encode("utf-8"), str(username).encode("utf-8"), hashlib.sha256
    ).hexdigest()


def encrypt_file(
    input_csv: str | None = None,
    output_csv: str | None = None,
    key: str | None = None,
    config_path: str | None = None,
) -> pl.DataFrame:
    cfg = load_config(config_path)
    input_csv = input_csv or cfg.get("unencrypted_input", "attack_data.csv")
    output_csv = output_csv or cfg.get("encrypted_output", "attack_data_encrypted.csv")
    key = key or cfg.get("encryption_key")

    if not key:
        raise ValueError("Encryption key not set. Set ENCRYPTION_KEY in env or config.")

    df = pl.read_csv(input_csv, try_parse_dates=True)
    # normalize column names
    df.columns = [c.strip().lower() for c in df.columns]

    required = {"victim_user", "target_repo", "starred_at"}
    if not required.issubset(set(df.columns)):
        missing = required - set(df.columns)
        raise ValueError(f"Missing required columns: {missing}")

    key_local = key
    enc_series = df["victim_user"].map_elements(lambda v: _hash_username(v, key_local), return_dtype=pl.String)

    out = pl.DataFrame({
        "victim_user": enc_series,
        "target_repo": df["target_repo"],
        "starred_at": df["starred_at"],
    })

    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    out.write_csv(output_csv)
    return out
