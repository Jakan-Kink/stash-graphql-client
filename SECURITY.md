# Security Policy

## Supported Versions

We actively maintain and provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |
| < Latest | :x:                |

**Recommendation:** Always use the latest released version to ensure you have the most recent security patches.

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue in stash-graphql-client, please report it responsibly.

### How to Report

You have two options for reporting security vulnerabilities:

#### Option 1: Private Email (Preferred for Severe Issues)

Send a detailed report to: **github@jakan.co**

**Include in your report:**
- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact and severity assessment
- Affected versions (if known)
- Suggested fix (if you have one)
- Your contact information for follow-up

**PGP Encryption (Optional):** For highly sensitive disclosures, request PGP key via initial unencrypted email.

#### Option 2: GitHub Security Advisories

Use GitHub's private security advisory feature:

1. Navigate to the [Security tab](https://github.com/Jakan-Kink/stash-graphql-client/security)
2. Click "Report a vulnerability"
3. Fill out the advisory form with details
4. Submit for private disclosure

**Benefits:**
- Built-in coordinated disclosure workflow
- CVE assignment
- Private collaboration with maintainers
- Automatic security advisory publication after fix

### What to Expect

- **Initial Response:** Within 7 days acknowledging receipt
- **Assessment:** Within 21 days we'll provide an initial assessment and timeline
- **Updates:** Regular updates on progress toward a fix
- **Coordinated Disclosure:** We'll work with you on disclosure timing
- **Credit:** You'll be credited in the security advisory (unless you prefer anonymity)

### Security Update Process

1. **Triage:** Assess severity and impact
2. **Fix Development:** Create and test patch
3. **Review:** Security-focused code review
4. **Testing:** Comprehensive test suite run
5. **Release:** Emergency release for critical issues, or bundled with next release for minor issues
6. **Disclosure:** Public security advisory with CVE (if applicable)
7. **Notification:** Users notified via GitHub releases and security advisories

## Security Best Practices

### For Contributors

- Never commit secrets (API keys, passwords, tokens) to the repository
- Use `.gitignore` for project-level exclusions (sensitive files all contributors should ignore)
- Use `~/.gitignore_global` for personal exclusions unique to your setup (IDE configs, OS files, personal scripts)
- Review dependencies for known vulnerabilities before adding
- Follow secure coding practices (see CONTRIBUTING.md)
- Run security checks before submitting PRs:
  ```bash
  poetry run ruff check --select S .
  ```

**Setting up global gitignore:**
```bash
# Create global gitignore
touch ~/.gitignore_global

# Configure git to use it
git config --global core.excludesfile ~/.gitignore_global

# Add personal patterns (examples)
echo ".vscode/" >> ~/.gitignore_global
echo ".idea/" >> ~/.gitignore_global
echo "*.local" >> ~/.gitignore_global
```

### Branch Protection Rules

The `main` branch has moderate security-focused protections enabled:

- **Require signed commits** - All commits must be cryptographically signed (GPG/SSH)
- **Require status checks to pass** - Specifically linting and code quality checks must pass before merge
- **Require branches to be up to date** - Feature branches must be current with `main` before merging

**Setting up commit signing:**

```bash
# For GPG signing
git config --global commit.gpgsign true
git config --global user.signingkey YOUR_GPG_KEY_ID

# For SSH signing (Git 2.34+)
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
```

See [GitHub's commit signing documentation](https://docs.github.com/en/authentication/managing-commit-signature-verification) for detailed setup instructions.

### For Users

- **Keep Updated:** Regularly update to the latest version
- **Review Changes:** Read release notes for security fixes
- **Secure Credentials:** Never hardcode Stash API keys directly in source code
- **Use Secure Configuration:** Store sensitive configuration securely (see below)
- **Audit Dependencies:** Periodically run `poetry show --outdated` to check for updates

## Security Scanning

This project uses multiple security scanning tools:

### Automated Scanning

- **Snyk:** Continuous dependency vulnerability scanning in CI/CD
- **Ruff Security Rules:** Static analysis for common security issues
- **Pre-commit Hooks:** Automated checks before commits
- **GitHub Dependabot:** Automated dependency update PRs

### Manual Review

- Security-focused code review for all PRs
- Periodic security audits of critical code paths
- Threat modeling for new features

## Vulnerability Disclosure Policy

We follow **coordinated disclosure**:

1. **Private Reporting:** Report vulnerabilities privately (not public issues)
2. **Collaboration:** We'll work with you on timeline and fix
3. **Public Disclosure:** After fix is released and users have time to update (typically 30-90 days)
4. **Credit:** Reporters are credited unless anonymity is requested

### Out of Scope

The following are generally **not** considered security vulnerabilities:

- Issues in outdated/unsupported versions
- Vulnerabilities in Stash itself (report to [stashapp/stash](https://github.com/stashapp/stash))
- Issues requiring physical access to the machine
- Social engineering attacks
- Issues in third-party dependencies (report to upstream)

## Security-Related Configuration

### Credential Management

When using this client library, you have several options for managing Stash credentials. Choose the approach that best fits your use case:

#### Option 1: Environment Variables (Recommended for Services/Scripts)

```python
# ✅ GOOD: Use environment variables
import os
from stash_graphql_client import StashClient

api_key = os.getenv("STASH_API_KEY")
stash_url = os.getenv("STASH_URL", "http://localhost:9999/graphql")

client = StashClient(url=stash_url, api_key=api_key)
```

**Advantages:**
- Credentials not in source code
- Easy to manage in containerized environments
- Different values per environment (dev/staging/prod)

#### Option 2: Configuration Files (Recommended for Applications)

```python
# ✅ GOOD: Load from configuration file
import json
from pathlib import Path
from stash_graphql_client import StashContext

# Load config from user's home directory
config_path = Path.home() / ".config" / "myapp" / "stash_config.json"
with open(config_path) as f:
    config = json.load(f)

async with StashContext(conn=config["stash"]) as client:
    # Use client
    pass
```

**Configuration file example** (`~/.config/myapp/stash_config.json`):
```json
{
  "stash": {
    "Scheme": "http",
    "Host": "localhost",
    "Port": 9999,
    "ApiKey": "your-api-key-here"
  }
}
```

**Advantages:**
- Clean separation of config from code
- Easy for users to customize
- Standard pattern for desktop/CLI applications
- Can store multiple Stash instances

**IMPORTANT Security Practices for Config Files:**
- ❌ **Never commit config files with secrets to version control**
- ✅ Add config file paths to `.gitignore` (project-level)
- ✅ Use `~/.gitignore_global` for personal config file locations unique to your setup
- ✅ Provide example config with placeholder values (e.g., `stash_config.example.json`)
- ✅ Set restrictive file permissions: `chmod 600 ~/.config/myapp/stash_config.json`
- ✅ Document config file location and format for users
- ✅ Validate and sanitize config file contents before use

#### Option 3: Interactive Prompts (For CLI Tools)

```python
# ✅ GOOD: Prompt user for credentials
import getpass
from stash_graphql_client import StashClient

stash_url = input("Stash URL: ")
api_key = getpass.getpass("API Key (optional): ") or None

client = StashClient(url=stash_url, api_key=api_key)
```

**Advantages:**
- No credentials stored on disk
- Good for one-time operations
- User controls credential exposure

#### ❌ What NOT to Do

```python
# ❌ WRONG: Hardcoded credentials in source code
client = StashClient(
    url="http://localhost:9999/graphql",
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # Never do this!
)

# ❌ WRONG: Credentials in code comments
# My API key: abc123def456...

# ❌ WRONG: Committing config files with real credentials
# Don't commit: config.json, .env, credentials.json, etc.
```

### Network Security

- **Use HTTPS:** When connecting to remote Stash instances, always use HTTPS
- **Validate Certificates:** Don't disable SSL verification in production
- **Firewall:** Restrict Stash server access to trusted networks
- **Local Development:** For local Stash instances, HTTP is acceptable (localhost only)

### Input Validation

This library performs input validation via Pydantic models. However:

- Always validate user input before passing to the client
- Sanitize data from untrusted sources
- Be cautious with GraphQL queries constructed from user input

## Known Security Considerations

### GraphQL Injection

While this library uses parameterized GraphQL queries to prevent injection, users should:

- Never construct raw GraphQL strings from user input
- Use the provided Pydantic models for type safety
- Validate all user-provided data before sending to Stash

### Dependency Chain

This library depends on:
- `gql` - GraphQL client
- `httpx` - HTTP client
- `pydantic` - Data validation
- And others (see `pyproject.toml`)

**We monitor these dependencies for vulnerabilities** via Snyk and Dependabot.

### Configuration File Security

If using configuration files:

- **File Permissions:** Ensure config files are readable only by the application user
  ```bash
  chmod 600 ~/.config/myapp/stash_config.json
  ```
- **Encryption:** Consider encrypting sensitive config files at rest
- **Validation:** Validate config file contents to prevent injection attacks
- **Path Traversal:** Use absolute paths or carefully validate relative paths

## Security Resources

- **Stash Security:** [https://github.com/stashapp/stash/security](https://github.com/stashapp/stash/security)
- **Python Security:** [https://python.org/dev/security/](https://python.org/dev/security/)
- **OWASP Top 10:** [https://owasp.org/www-project-top-ten/](https://owasp.org/www-project-top-ten/)
- **Commit Signing:** [https://docs.github.com/en/authentication/managing-commit-signature-verification](https://docs.github.com/en/authentication/managing-commit-signature-verification)

## Questions?

If you have questions about this security policy, contact github@jakan.co.

---

**Last Updated:** 2025-12-20
**Version:** 1.0.0
