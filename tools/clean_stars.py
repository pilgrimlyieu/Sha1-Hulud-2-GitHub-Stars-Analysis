import requests
import time

# GitHub Token
GITHUB_TOKEN = "your_github_token_here"

# Your repo (the one you want to clean)
MY_REPO = "your-username/your-repo"

# The reference repo (the other victimized repo)
REF_REPOS = [
    "some-username/some-repo",
    # Add more repos if needed
]

# API Headers
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
# =================================================


def get_stargazers(repo):
    """Fetch all usernames who starred the given repo."""
    stargazers = set()
    page = 1
    print(f"[*] Fetching stargazers for {repo}...")

    while True:
        # Fetch 100 items per page for efficiency
        url = f"https://api.github.com/repos/{repo}/stargazers?per_page=100&page={page}"
        response = requests.get(url, headers=HEADERS)

        if response.status_code != 200:
            print(f"[!] Error fetching {repo}: {response.json().get('message')}")
            break

        data = response.json()
        if not data:
            break

        for user in data:
            stargazers.add(user["login"])

        print(f"    - Page {page} loaded ({len(stargazers)} users so far)")
        page += 1
        # Optional: Sleep to respect rate limits if repo is huge
        time.sleep(0.1)

    return stargazers


def block_user(username):
    """Block the user to force-remove their star."""
    url = f"https://api.github.com/user/blocks/{username}"
    res = requests.put(url, headers=HEADERS)
    return res.status_code == 204


def unblock_user(username):
    """Unblock the user immediately."""
    url = f"https://api.github.com/user/blocks/{username}"
    res = requests.delete(url, headers=HEADERS)
    return res.status_code == 204


def main():
    # Step 1: Get stargazers from both repos
    my_stars = get_stargazers(MY_REPO)
    ref_stars = set()
    for repo in REF_REPOS:
        ref_stars.update(get_stargazers(repo))

    # Step 2: Identify common users (The malicious ones)
    target_users = my_stars.intersection(ref_stars)
    print(f"\n[+] Identification complete.")
    print(f"    - Your repo stars: {len(my_stars)}")
    print(f"    - Reference repo stars: {len(ref_stars)}")
    print(f"    - Overlapping users to be removed: {len(target_users)}")

    if not target_users:
        print("[!] No common stargazers found. Exiting.")
        return

    confirm = input(
        f"\n[?] Proceed to block/unblock {len(target_users)} users? (y/n): "
    )
    if confirm.lower() != "y":
        print("[!] Operation cancelled.")
        return

    # Step 3: Process Block -> Unblock loop
    success_count = 0
    for i, username in enumerate(target_users, 1):
        print(f"[{i}/{len(target_users)}] Processing: {username}", end="\r")

        if block_user(username):
            if unblock_user(username):
                success_count += 1
            else:
                print(f"\n[!] Failed to unblock {username}")
        else:
            print(f"\n[!] Failed to block {username}")

        # Small delay to avoid hitting secondary rate limits
        time.sleep(0.2)

    print(f"\n\n[OK] Task finished. Successfully cleaned {success_count} stars.")


if __name__ == "__main__":
    main()
