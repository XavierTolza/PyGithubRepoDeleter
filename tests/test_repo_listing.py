import os
import pytest
from unittest.mock import patch, MagicMock
from github import Github, BadCredentialsException
from github_repo_deleter.repo_deleter import run_delete, get_token


class TestRepoListing:
    """Test repository listing functionality"""

    def test_github_token_from_environment(self):
        """Test that we can get a token from environment variables"""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
            with patch("github_repo_deleter.repo_deleter.prompt") as mock_prompt:
                parser_path = "github_repo_deleter.repo_deleter.ArgumentParser"
                with patch(parser_path) as mock_parser:
                    mock_args = MagicMock()
                    mock_args.token = None
                    parser_mock = mock_parser.return_value
                    parser_mock.parse_args.return_value = mock_args

                    token = get_token()
                    assert token == "test_token"
                    # Should not prompt user when token is available in env
                    mock_prompt.assert_not_called()

    @patch("github_repo_deleter.repo_deleter.Github")
    def test_list_repositories_success(self, mock_github_class):
        """Test successful repository listing"""
        # Setup mock GitHub client
        mock_github = MagicMock()
        mock_github_class.return_value = mock_github

        # Setup mock user
        mock_user = MagicMock()
        mock_github.get_user.return_value = mock_user

        # Setup mock repositories
        mock_repo1 = MagicMock()
        mock_repo1.full_name = "test-user/repo1"
        mock_repo1.permissions.admin = True
        mock_repo1.updated_at = "2023-01-01"

        mock_repo2 = MagicMock()
        mock_repo2.full_name = "test-user/repo2"
        mock_repo2.permissions.admin = True
        mock_repo2.updated_at = "2023-01-02"

        mock_user.get_repos.return_value = [mock_repo1, mock_repo2]

        # Mock PyInquirer to simulate user selecting no repos (empty list)
        with patch("github_repo_deleter.repo_deleter.prompt") as mock_prompt:
            mock_prompt.return_value = {"repos": []}

            # This should not raise any exceptions
            run_delete("fake_token")

            # Verify GitHub client was created with correct token
            mock_github_class.assert_called_once_with("fake_token")

            # Verify user repos were fetched
            mock_user.get_repos.assert_called_once()

            # Verify prompt was called with repository choices
            prompt_calls = mock_prompt.call_args_list
            assert len(prompt_calls) >= 1

            # Check that repositories were included in choices
            choices_arg = prompt_calls[0][0][0]["choices"]
            repo_names = [choice["name"] for choice in choices_arg]
            assert "test-user/repo1" in repo_names
            assert "test-user/repo2" in repo_names

    @patch("github_repo_deleter.repo_deleter.Github")
    def test_bad_credentials_handling(self, mock_github_class):
        """Test handling of bad credentials"""
        mock_github = MagicMock()
        mock_github_class.return_value = mock_github

        # Simulate bad credentials
        mock_github.get_user.side_effect = BadCredentialsException(None, None)

        with patch("builtins.print") as mock_print:
            run_delete("invalid_token")

            # Should print error message about invalid token
            expected_msg = (
                "Invalid token. Make sure the token is correct "
                "and you have the repo and delete_repo rights"
            )
            mock_print.assert_called_with(expected_msg)

    @patch("github_repo_deleter.repo_deleter.Github")
    def test_filter_admin_repos_only(self, mock_github_class):
        """Test that only repositories with admin permissions are shown"""
        mock_github = MagicMock()
        mock_github_class.return_value = mock_github

        mock_user = MagicMock()
        mock_github.get_user.return_value = mock_user

        # Setup repos with different permission levels
        mock_repo_admin = MagicMock()
        mock_repo_admin.full_name = "test-user/admin-repo"
        mock_repo_admin.permissions.admin = True
        mock_repo_admin.updated_at = "2023-01-01"

        mock_repo_no_admin = MagicMock()
        mock_repo_no_admin.full_name = "test-user/no-admin-repo"
        mock_repo_no_admin.permissions.admin = False
        mock_repo_no_admin.updated_at = "2023-01-02"

        repos = [mock_repo_admin, mock_repo_no_admin]
        mock_user.get_repos.return_value = repos

        with patch("github_repo_deleter.repo_deleter.prompt") as mock_prompt:
            mock_prompt.return_value = {"repos": []}

            run_delete("fake_token")

            # Check that only admin repos are in choices
            prompt_calls = mock_prompt.call_args_list
            choices_arg = prompt_calls[0][0][0]["choices"]
            repo_names = [choice["name"] for choice in choices_arg]

            assert "test-user/admin-repo" in repo_names
            assert "test-user/no-admin-repo" not in repo_names

    def test_import_main_function(self):
        """Test that main function can be imported without errors"""
        from github_repo_deleter.repo_deleter import main

        assert callable(main)

    @patch("github_repo_deleter.repo_deleter.Github")
    def test_repository_sorting_by_updated_at(self, mock_github_class):
        """Test that repositories are sorted by updated_at"""
        mock_github = MagicMock()
        mock_github_class.return_value = mock_github

        mock_user = MagicMock()
        mock_github.get_user.return_value = mock_user

        # Create repos with different update times (unsorted)
        from datetime import datetime

        mock_repo1 = MagicMock()
        mock_repo1.full_name = "test-user/newer-repo"
        mock_repo1.permissions.admin = True
        mock_repo1.updated_at = datetime(2023, 6, 1)

        mock_repo2 = MagicMock()
        mock_repo2.full_name = "test-user/older-repo"
        mock_repo2.permissions.admin = True
        mock_repo2.updated_at = datetime(2023, 1, 1)

        # Return repos in unsorted order
        mock_user.get_repos.return_value = [mock_repo1, mock_repo2]

        with patch("github_repo_deleter.repo_deleter.prompt") as mock_prompt:
            mock_prompt.return_value = {"repos": []}

            run_delete("fake_token")

            # Verify repos are sorted by updated_at (older first)
            prompt_calls = mock_prompt.call_args_list
            choices_arg = prompt_calls[0][0][0]["choices"]

            # Should be sorted with older repo first
            assert choices_arg[0]["name"] == "test-user/older-repo"
            assert choices_arg[1]["name"] == "test-user/newer-repo"


# Integration-like test that uses the actual GitHub API
class TestGitHubIntegration:
    """Integration tests that use real GitHub API (but only for listing)"""

    def test_github_api_connection(self):
        """Test that we can connect to GitHub API with a token"""
        # Use the GitHub token from environment (if available)
        token = os.getenv("GITHUB_TOKEN")

        if not token:
            pytest.skip("No GITHUB_TOKEN environment variable set")

        # Test basic API connection
        try:
            g = Github(token)
            user = g.get_user()

            # Just verify we can get user info and list repos
            login = user.login
            assert login is not None
            assert isinstance(login, str)

            # Test listing repositories (limit to first 5 to keep test fast)
            repos = list(user.get_repos())[:5]
            print(
                f"Successfully connected as {login}, found {len(repos)} repositories (showing first 5)"
            )

            for repo in repos:
                print(f"  - {repo.full_name} (admin: {repo.permissions.admin})")

        except BadCredentialsException:
            pytest.fail(
                "Invalid GitHub token. Check GITHUB_TOKEN environment variable."
            )
        except Exception as e:
            pytest.fail(f"Unexpected error connecting to GitHub API: {e}")
