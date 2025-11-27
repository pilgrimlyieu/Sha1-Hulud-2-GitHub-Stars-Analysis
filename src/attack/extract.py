"""
Data extraction module. Fetches stargazers and recent starred repos for suspicious users.
Produces a CSV with columns: victim_user, target_repo, starred_at
"""

import asyncio
from datetime import datetime
from typing import List

import httpx
import polars as pl
from tqdm.asyncio import tqdm

from .config import load_config


def _parse_iso(s: str) -> datetime:
    if s is None:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


async def fetch_stargazers(
    client: httpx.AsyncClient, repo: str, attack_start: datetime, exclude_users: set
) -> List[str]:
    stargazers = []
    url = f"https://api.github.com/repos/{repo}/stargazers"
    page = 1
    while True:
        try:
            resp = await client.get(url, params={"per_page": 100, "page": page})
            resp.raise_for_status()
            data = resp.json()
            if not data:
                break

            for item in data:
                user = item.get("user", {}).get("login")
                starred_at = item.get("starred_at")
                if not user or not starred_at:
                    continue
                starred_dt = _parse_iso(starred_at)
                if starred_dt > attack_start and user not in exclude_users:
                    stargazers.append(user)

            page += 1
        except Exception:
            break

    return stargazers


async def fetch_user_recent_stars(
    client: httpx.AsyncClient, username: str, attack_start: datetime
) -> List[dict]:
    user_stars = []
    url = f"https://api.github.com/users/{username}/starred"
    page = 1
    while True:
        try:
            resp = await client.get(
                url,
                params={
                    "per_page": 100,
                    "page": page,
                    "sort": "created",
                    "direction": "desc",
                },
            )
            if resp.status_code in (404, 403):
                break
            data = resp.json()
            if not data:
                break

            stop = False
            for item in data:
                starred_at = item.get("starred_at")
                if not starred_at:
                    continue
                starred_dt = _parse_iso(starred_at)
                if starred_dt < attack_start:
                    stop = True
                    break

                repo_name = item.get("repo", {}).get("full_name")
                if not repo_name:
                    continue

                user_stars.append({
                    "victim_user": username,
                    "target_repo": repo_name,
                    "starred_at": starred_dt,
                })

            if stop:
                break
            page += 1
        except Exception:
            break

    return user_stars


async def main_async(cfg: dict) -> pl.DataFrame:
    token = cfg.get("github_token")
    headers = {
        "Accept": "application/vnd.github.v3.star+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    attack_start = datetime.fromisoformat(
        cfg.get("attack_start_date").replace("Z", "+00:00")
    )
    exclude = set(cfg.get("exclude_users", []))
    repo = cfg.get("target_repo")

    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        suspicious_users = await fetch_stargazers(client, repo, attack_start, exclude)
        sem = asyncio.Semaphore(cfg.get("concurrency", 10))

        all_data = []

        async def safe_fetch(user):
            async with sem:
                return await fetch_user_recent_stars(client, user, attack_start)

        tasks = [safe_fetch(u) for u in suspicious_users]
        results = await tqdm.gather(*tasks, desc="fetching user stars")
        for res in results:
            all_data.extend(res)

    if not all_data:
        return pl.DataFrame([])

    df = pl.DataFrame(all_data)
    out_path = cfg.get("unencrypted_input", "attack_data.csv")
    df.write_csv(out_path)
    return df


def main(config_path: str | None = None):
    cfg = load_config(config_path)
    return asyncio.run(main_async(cfg))


if __name__ == "__main__":
    main()
