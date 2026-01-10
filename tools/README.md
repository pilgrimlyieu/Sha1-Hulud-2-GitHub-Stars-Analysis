# Star Cleanup Tool

This tool helps repository owners remove malicious stars from the Sha1-Hulud 2.0 attack by identifying and cleaning up compromised accounts that have starred your repository.

## How It Works

The tool uses a cross-reference approach to identify malicious stargazers:

1. **Fetch stargazers** from your repository (the one you want to clean)
2. **Fetch stargazers** from known victimized reference repositories
3. **Identify overlap** - users who starred both repos are likely compromised accounts
4. **Remove stars** by temporarily blocking and immediately unblocking each identified user

When you block a user on GitHub, their star is automatically removed from your repository. By immediately unblocking them, you restore their account access while keeping the star removed.

## Prerequisites

### GitHub Token

You need a GitHub **Fine-grained Personal Access Token** with the following permissions:

- **Read access to starring** - to fetch stargazer lists
- **Read and Write access to blocking** - to block/unblock users

#### Creating a Fine-grained Token:

1. Go to [GitHub Settings > Developer settings > Personal access tokens > Fine-grained tokens](https://github.com/settings/tokens?type=beta)
2. Click "Generate new token"
3. Configure:
   - **Token name**: e.g., "Star Cleanup Tool"
   - **Expiration**: Choose appropriate duration, e.g., 7 days
   - **Repository access**: Select "All repositories" or specific repos
   - **Permissions**:
     - Under "Account permissions":
       - **Starring**: Read access
       - **Blocking**: Read and Write access
4. Click "Generate token" and copy it immediately

### Python Dependencies

```bash
pip install requests
```

## Configuration

Edit the script `clean_stars.py` and configure the following variables:

```python
# Your GitHub Personal Access Token
GITHUB_TOKEN = "github_pat_11AXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

# Your repository that needs cleaning (format: "owner/repo")
MY_REPO = "your-username/your-repo"

# Reference repositories (other victimized repos)
# The tool will identify users who starred both your repo AND these reference repos
REF_REPOS = [
    "some-username/some-repo",
    "another-username/another-repo",
    # Add more known victimized repos for better accuracy
]
```

**Important Configuration Tips:**

- **Reference repos**: Choose repositories that were confirmed victims of the Sha1-Hulud 2.0 attack. The more reference repos you add, the more accurate the identification.
- **Token security**: Never commit your token to version control. Consider using environment variables for production use.

## Usage

1. Configure the script with your token and repository information
2. Run the script:

```bash
python clean_stars.py
```

3. The tool will:
   - Fetch all stargazers from your repository
   - Fetch all stargazers from reference repositories
   - Calculate the overlap and show statistics
   - Ask for confirmation before proceeding
   - Process each identified user with block/unblock operations

### Example Output

```
[*] Fetching stargazers for pilgrimlyieu/Focust...
    - Page 1 loaded (92 users so far)
[*] Fetching stargazers for Hrishikesh332/Weather-Analysis-Jupyter...
    - Page 1 loaded (75 users so far)

[+] Identification complete.
    - Your repo stars: 92
    - Reference repo stars: 75
    - Overlapping users to be removed: 74

[?] Proceed to block/unblock 74 users? (y/n): y
[74/74] Processing: ******

[OK] Task finished. Successfully cleaned 74 stars.
```

## Safety Notes

⚠️ **Important Considerations:**

1. **Irreversible**: Once stars are removed, users won't be automatically re-starred even if they were legitimate
2. **False positives**: Legitimate users who coincidentally starred both repositories will also lose their star
3. **Backup**: Consider exporting your stargazer list before running the cleanup