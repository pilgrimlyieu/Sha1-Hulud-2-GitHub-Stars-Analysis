# Sha1-Hulud 2.0 Attack on GitHub Stars Analysis Toolkit

This repository contains a forensic toolkit and analysis report regarding the **Sha1-Hulud 2.0** supply chain attack (observed late Nov 2025). 

By collecting data from 101 compromised victim accounts (anonymized), we identified specific targeting patterns, rate limits, and the use of "Awesome" lists as attack vectors.

Key points
- The canonical input to analysis is `attack_data_encrypted.csv` with columns:
	`victim_user` (anonymized), `target_repo`, `starred_at`.
- Raw (unencrypted) extraction output is written to `attack_data.csv` by
	the extractor. Use the encryption utility to produce the anonymized CSV.
- Configuration is in `config.json`; secrets are read from environment or `.env`.

Quick tasks

Activate virtual environment first (assuming uv):

```bash
$ uv venv --python 3.13
$ source .venv/bin/activate
$ uv sync
```

Encrypt existing unencrypted data (does not call network):

```bash
$ python -m main --encrypt
```
Run extraction (requires `GITHUB_TOKEN` in env/.env):

```bash
$ python -m main --extract
```

Run analysis (reads `attack_data_encrypted.csv` by default):

```bash
$ python -m analysis
```

Files
- `config.json` — main configuration (target repo, exclusion list, file names)
- `.env` — environment placeholders (GITHUB_TOKEN, ENCRYPTION_KEY)
- `src/attack` — package with `extract`, `encrypt`, `analyze`, and `config` modules

Notes
- The anonymization is deterministic HMAC-SHA256 using `ENCRYPTION_KEY` so the
	same victim maps to the same pseudonym across runs. Set a secure key before
	processing real data.
- The analysis uses Polars and Plotly to create CSV summaries and HTML charts
	(stored in the configured `output_dir`).
