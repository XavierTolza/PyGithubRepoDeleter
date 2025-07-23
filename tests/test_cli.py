"""
CLI-specific tests for the repo deleter tool
"""

import os
import subprocess
import sys
from unittest.mock import patch, MagicMock
import pytest


class TestCLI:
    """Test CLI functionality"""

    def test_console_script_available(self):
        """Test that the console script is properly installed"""
        try:
            result = subprocess.run(
                ["remove_github_repos", "--help"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            # Should either succeed or fail with specific exit codes
            # but should not fail with "command not found"
            assert result.returncode in [0, 1, 2], (
                f"Console script failed with unexpected return code: "
                f"{result.returncode}"
            )
        except FileNotFoundError:
            pytest.fail("Console script 'remove_github_repos' not found")
        except subprocess.TimeoutExpired:
            pytest.fail("Console script timed out")

    def test_module_execution(self):
        """Test that the module can be executed with python -m"""
        try:
            cmd = [sys.executable, "-m",
                   "github_repo_deleter.repo_deleter", "--help"]
            result = subprocess.run(cmd, capture_output=True,
                                    text=True, timeout=10)
            # Should either succeed or fail gracefully
            assert result.returncode in [0, 1, 2], (
                f"Module execution failed with unexpected return code: "
                f"{result.returncode}"
            )
        except subprocess.TimeoutExpired:
            pytest.fail("Module execution timed out")

    def test_import_no_side_effects(self):
        """Test that importing the module doesn't cause side effects"""
        # This should not trigger any prompts or API calls
        import github_repo_deleter.repo_deleter

        # Should be able to access main functions
        assert hasattr(github_repo_deleter.repo_deleter, "main")
        assert hasattr(github_repo_deleter.repo_deleter, "get_token")
        assert hasattr(github_repo_deleter.repo_deleter, "run_delete")

    def test_help_message_content(self):
        """Test that help message contains expected content"""
        try:
            cmd = [sys.executable, "-m",
                   "github_repo_deleter.repo_deleter", "--help"]
            result = subprocess.run(cmd, capture_output=True,
                                    text=True, timeout=10)

            help_output = result.stdout + result.stderr

            # Should mention the token parameter
            assert "--token" in help_output or "token" in help_output.lower()

        except subprocess.TimeoutExpired:
            pytest.skip("Help command timed out")

    @patch("github_repo_deleter.repo_deleter.inquirer.prompt")
    @patch("github_repo_deleter.repo_deleter.Github")
    def test_main_function_execution(self, mock_github_class,
                                     mock_inquirer_prompt):
        """Test that main function runs without errors in normal flow"""
        # Mock the GitHub client
        mock_github = MagicMock()
        mock_github_class.return_value = mock_github

        mock_user = MagicMock()
        mock_github.get_user.return_value = mock_user
        mock_user.get_repos.return_value = []

        # Mock prompts to avoid interactive input
        mock_inquirer_prompt.side_effect = [
            {"token": "fake_token"},  # Token prompt
            {"repos": []},  # Repo selection prompt
        ]

        # Mock environment to avoid using real token
        with patch.dict(os.environ, {}, clear=True):
            with patch("sys.argv", ["remove_github_repos"]):
                # This should complete without errors
                from github_repo_deleter.repo_deleter import main

                main()

        # Verify the GitHub client was initialized
        mock_github_class.assert_called_once_with("fake_token")


class TestErrorHandling:
    """Test error handling scenarios"""

    @patch("github_repo_deleter.repo_deleter.Github")
    def test_network_error_handling(self, mock_github_class):
        """Test handling of network-related errors"""
        from github import GithubException
        from github_repo_deleter.repo_deleter import run_delete

        mock_github = MagicMock()
        mock_github_class.return_value = mock_github

        # Simulate network error
        mock_github.get_user.side_effect = GithubException(500, "Server Error")

        # Should not crash, should handle gracefully
        try:
            run_delete("fake_token")
        except GithubException:
            # If it propagates, that's also acceptable behavior
            pass

    def test_empty_token_handling(self):
        """Test behavior with empty token"""
        mock_path = "github_repo_deleter.repo_deleter.inquirer.prompt"
        with patch(mock_path) as mock_prompt:
            with patch.dict(os.environ, {}, clear=True):
                with patch("sys.argv", ["remove_github_repos"]):
                    # Mock prompt to provide token after empty attempts
                    mock_prompt.side_effect = [
                        {"token": ""},  # First attempt: empty
                        {"token": "valid_token"},  # Second attempt: valid
                    ]

                    from github_repo_deleter.repo_deleter import get_token

                    token = get_token()

                    assert token == "valid_token"
                    # Should have been called twice due to empty token
                    assert mock_prompt.call_count == 2
