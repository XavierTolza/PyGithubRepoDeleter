# Tests for PyGithubRepoDeleter

This directory contains comprehensive tests for the PyGithubRepoDeleter package.

## Test Files

### `test_repo_listing.py`
- **TestRepoListing**: Unit tests for repository listing functionality
  - Token handling from environment variables
  - Repository listing and filtering (admin repos only)
  - Repository sorting by update date
  - Error handling for bad credentials
  - GitHub API integration tests (when token available)

- **TestGitHubIntegration**: Integration tests with real GitHub API
  - Tests actual GitHub API connection (requires GITHUB_TOKEN)
  - Verifies repository listing works with real data

### `test_cli.py` 
- **TestCLI**: Command-line interface tests
  - Console script availability (`remove_github_repos`)
  - Module execution (`python -m github_repo_deleter.repo_deleter`)
  - Help command functionality
  - Import behavior and side effects

- **TestErrorHandling**: Error handling scenarios
  - Network error handling
  - Empty token handling
  - Graceful failure modes

## Running Tests

### Run all tests:
```bash
python -m pytest tests/ -v
```

### Run specific test classes:
```bash
# Unit tests only
python -m pytest tests/test_repo_listing.py::TestRepoListing -v

# CLI tests only  
python -m pytest tests/test_cli.py::TestCLI -v

# Integration tests (requires GITHUB_TOKEN)
python -m pytest tests/test_repo_listing.py::TestGitHubIntegration -v
```

### Manual testing:
```bash
# Set your GitHub token
export GITHUB_TOKEN="your_token_here"

# Run manual test script
python test_manual.py
```

## GitHub Actions CI/CD

The `.github/workflows/test.yml` workflow runs these tests automatically on:
- Push to main/master branches
- Pull requests to main/master branches  
- Manual workflow dispatch

The workflow tests across multiple Python versions:
- Python 3.8, 3.9, 3.10, 3.11, 3.12, 3.13

### Test Matrix

For each Python version, the workflow:
1. Sets up the environment
2. Installs dependencies
3. Runs linting checks
4. Tests package installation and imports
5. Tests CLI help commands
6. Runs unit tests
7. Runs integration tests (if GitHub token available)
8. Validates package metadata

## Environment Variables

- `GITHUB_TOKEN`: Required for integration tests and manual testing
  - Should have `repo` and `delete_repo` permissions
  - Not required for unit tests (they use mocking)

## Test Coverage

The tests cover:
- ✅ Repository listing functionality
- ✅ Authentication and token handling
- ✅ Repository filtering (admin permissions)
- ✅ Repository sorting
- ✅ CLI interface and console scripts
- ✅ Error handling (bad credentials, network errors)
- ✅ Package installation and imports
- ✅ Integration with real GitHub API
- ✅ Cross-platform compatibility (via CI)
