"""
Git Operations Tool for Google ADK Agent

This tool provides Git operations functionality for agents using GitPython.
It handles common Git operations like cloning, branching, committing, and more.
Supports Personal Access Token (PAT) authentication for GitHub and environment-based configuration.
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
import git
from git import Repo, GitCommandError
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class GitOperationsTool:
    """
    A comprehensive Git operations tool for AI agents.

    This class provides methods for common Git operations including:
    - Cloning repositories
    - Creating and switching branches
    - Staging and committing changes
    - Pushing and pulling changes
    - Getting repository status
    - Managing remotes
    - Personal Access Token (PAT) authentication for GitHub
    - Environment-based configuration
    """

    def __init__(
        self,
        repo_path: Optional[str] = None,
        github_token: Optional[str] = None,
        use_env_config: bool = True
    ):
        """
        Initialize the Git operations tool.

        Args:
            repo_path: Path to an existing Git repository. If None and use_env_config
                      is True, will try to load from GIT_REPO_PATH env variable.
            github_token: GitHub Personal Access Token for authentication.
                         If None and use_env_config is True, will try to load from
                         GITHUB_TOKEN env variable.
            use_env_config: Whether to load configuration from environment variables.
        """
        # Load from environment if requested
        if use_env_config:
            self.repo_path = repo_path or os.getenv('GIT_REPO_PATH')
            self.github_token = github_token or os.getenv('GITHUB_TOKEN')
            self.default_repo_url = os.getenv('GIT_REPO_URL')
            self.default_branch = os.getenv('GIT_DEFAULT_BRANCH', 'main')
        else:
            self.repo_path = repo_path
            self.github_token = github_token
            self.default_repo_url = None
            self.default_branch = 'main'

        self.repo: Optional[Repo] = None

        if self.repo_path and os.path.exists(self.repo_path):
            try:
                self.repo = Repo(self.repo_path)
            except git.exc.InvalidGitRepositoryError:
                raise ValueError(f"{self.repo_path} is not a valid Git repository")

    def _get_authenticated_url(self, repo_url: str) -> str:
        """
        Convert a repository URL to use token authentication.

        Args:
            repo_url: Original repository URL (SSH or HTTPS)

        Returns:
            HTTPS URL with token authentication
        """
        if not self.github_token:
            return repo_url

        # Convert SSH URL to HTTPS if needed
        if repo_url.startswith('git@github.com:'):
            # Convert git@github.com:user/repo.git to https://github.com/user/repo.git
            repo_url = repo_url.replace('git@github.com:', 'https://github.com/')

        # Add token to HTTPS URL
        if repo_url.startswith('https://github.com/'):
            # Insert token into URL: https://TOKEN@github.com/user/repo.git
            repo_url = repo_url.replace('https://github.com/', f'https://{self.github_token}@github.com/')

        return repo_url

    def clone_repository(
        self,
        repo_url: Optional[str] = None,
        destination_path: Optional[str] = None,
        branch: Optional[str] = None,
        depth: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Clone a Git repository.

        Args:
            repo_url: URL of the repository to clone. If None, uses GIT_REPO_URL from env.
            destination_path: Local path where the repository will be cloned.
                            If None, uses GIT_REPO_PATH from env.
            branch: Specific branch to clone (optional, defaults to env GIT_DEFAULT_BRANCH)
            depth: Clone depth for shallow cloning (optional)

        Returns:
            Dict with status and repository information
        """
        # Use environment variables as fallback
        repo_url = repo_url or self.default_repo_url
        destination_path = destination_path or self.repo_path

        if not repo_url:
            return {
                "success": False,
                "error": "No repository URL provided and GIT_REPO_URL not set in environment"
            }

        if not destination_path:
            return {
                "success": False,
                "error": "No destination path provided and GIT_REPO_PATH not set in environment"
            }

        try:
            clone_kwargs = {}
            if branch:
                clone_kwargs['branch'] = branch
            elif self.default_branch:
                clone_kwargs['branch'] = self.default_branch

            if depth:
                clone_kwargs['depth'] = depth

            # Convert URL to use token authentication if available
            authenticated_url = self._get_authenticated_url(repo_url)

            self.repo = Repo.clone_from(authenticated_url, destination_path, **clone_kwargs)
            self.repo_path = destination_path

            return {
                "success": True,
                "message": f"Successfully cloned repository to {destination_path}",
                "repo_path": destination_path,
                "current_branch": self.repo.active_branch.name,
                "using_token": self.github_token is not None
            }
        except GitCommandError as e:
            return {
                "success": False,
                "error": f"Failed to clone repository: {str(e)}"
            }

    def create_branch(
        self,
        branch_name: str,
        checkout: bool = True,
        start_point: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new branch.

        Args:
            branch_name: Name of the new branch
            checkout: Whether to checkout the new branch immediately
            start_point: Commit/branch to start from (defaults to HEAD)

        Returns:
            Dict with status and branch information
        """
        if not self.repo:
            self._ensure_repo_loaded()

        if not self.repo:
            return {"success": False, "error": "No repository loaded"}

        try:
            if start_point:
                new_branch = self.repo.create_head(branch_name, start_point)
            else:
                new_branch = self.repo.create_head(branch_name)

            if checkout:
                new_branch.checkout()

            return {
                "success": True,
                "message": f"Created branch '{branch_name}'",
                "branch_name": branch_name,
                "checked_out": checkout,
                "current_branch": self.repo.active_branch.name
            }
        except GitCommandError as e:
            return {
                "success": False,
                "error": f"Failed to create branch: {str(e)}"
            }

    def checkout_branch(self, branch_name: str, create_if_missing: bool = False) -> Dict[str, Any]:
        """
        Checkout an existing branch.

        Args:
            branch_name: Name of the branch to checkout
            create_if_missing: Create the branch if it doesn't exist

        Returns:
            Dict with status and branch information
        """
        if not self.repo:
            self._ensure_repo_loaded()

        if not self.repo:
            return {"success": False, "error": "No repository loaded"}

        try:
            # Check if branch exists
            if branch_name in self.repo.heads:
                self.repo.heads[branch_name].checkout()
                return {
                    "success": True,
                    "message": f"Checked out branch '{branch_name}'",
                    "current_branch": self.repo.active_branch.name
                }
            elif create_if_missing:
                return self.create_branch(branch_name, checkout=True)
            else:
                return {
                    "success": False,
                    "error": f"Branch '{branch_name}' does not exist"
                }
        except GitCommandError as e:
            return {
                "success": False,
                "error": f"Failed to checkout branch: {str(e)}"
            }

    def stage_files(self, file_paths: Optional[List[str]] = None, stage_all: bool = False) -> Dict[str, Any]:
        """
        Stage files for commit.

        Args:
            file_paths: List of file paths to stage (relative to repo root)
            stage_all: Stage all modified and new files

        Returns:
            Dict with status information
        """
        if not self.repo:
            self._ensure_repo_loaded()

        if not self.repo:
            return {"success": False, "error": "No repository loaded"}

        try:
            if stage_all:
                self.repo.git.add(A=True)
                staged_files = [item.a_path for item in self.repo.index.diff("HEAD")]
                return {
                    "success": True,
                    "message": "Staged all files",
                    "staged_files": staged_files
                }
            elif file_paths:
                self.repo.index.add(file_paths)
                return {
                    "success": True,
                    "message": f"Staged {len(file_paths)} file(s)",
                    "staged_files": file_paths
                }
            else:
                return {
                    "success": False,
                    "error": "No files specified and stage_all is False"
                }
        except GitCommandError as e:
            return {
                "success": False,
                "error": f"Failed to stage files: {str(e)}"
            }

    def commit(
        self,
        message: str,
        author_name: Optional[str] = None,
        author_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a commit with staged changes.

        Args:
            message: Commit message
            author_name: Author name (optional, uses git config if not provided)
            author_email: Author email (optional, uses git config if not provided)

        Returns:
            Dict with commit information
        """
        if not self.repo:
            self._ensure_repo_loaded()

        if not self.repo:
            return {"success": False, "error": "No repository loaded"}

        try:
            commit_kwargs = {}
            if author_name and author_email:
                commit_kwargs['author'] = git.Actor(author_name, author_email)

            commit = self.repo.index.commit(message, **commit_kwargs)

            return {
                "success": True,
                "message": "Commit created successfully",
                "commit_sha": commit.hexsha,
                "commit_message": message,
                "author": str(commit.author),
                "committed_date": commit.committed_datetime.isoformat()
            }
        except GitCommandError as e:
            return {
                "success": False,
                "error": f"Failed to commit: {str(e)}"
            }

    def push(
        self,
        remote: str = "origin",
        branch: Optional[str] = None,
        set_upstream: bool = False,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Push commits to a remote repository using token authentication.

        Args:
            remote: Name of the remote (default: "origin")
            branch: Branch name to push (defaults to current branch)
            set_upstream: Set upstream tracking for the branch
            force: Force push (use with caution)

        Returns:
            Dict with push status
        """
        if not self.repo:
            self._ensure_repo_loaded()

        if not self.repo:
            return {"success": False, "error": "No repository loaded"}

        try:
            if not branch:
                branch = self.repo.active_branch.name

            # Update remote URL to use token authentication if available
            if self.github_token:
                origin = self.repo.remote(name=remote)
                original_url = list(origin.urls)[0]
                authenticated_url = self._get_authenticated_url(original_url)
                origin.set_url(authenticated_url)

            push_kwargs = {}
            if set_upstream:
                push_kwargs['set_upstream'] = True
            if force:
                push_kwargs['force'] = True

            origin = self.repo.remote(name=remote)
            push_info = origin.push(branch, **push_kwargs)

            # Check for errors in push
            if push_info and len(push_info) > 0:
                info = push_info[0]
                if info.flags & info.ERROR:
                    return {
                        "success": False,
                        "error": f"Push failed: {info.summary}"
                    }

            return {
                "success": True,
                "message": f"Pushed to {remote}/{branch}",
                "remote": remote,
                "branch": branch,
                "using_token": self.github_token is not None
            }
        except GitCommandError as e:
            return {
                "success": False,
                "error": f"Failed to push: {str(e)}"
            }

    def pull(self, remote: str = "origin", branch: Optional[str] = None) -> Dict[str, Any]:
        """
        Pull changes from a remote repository using token authentication.

        Args:
            remote: Name of the remote (default: "origin")
            branch: Branch name to pull (defaults to current branch)

        Returns:
            Dict with pull status
        """
        if not self.repo:
            self._ensure_repo_loaded()

        if not self.repo:
            return {"success": False, "error": "No repository loaded"}

        try:
            # Update remote URL to use token authentication if available
            if self.github_token:
                origin = self.repo.remote(name=remote)
                original_url = list(origin.urls)[0]
                authenticated_url = self._get_authenticated_url(original_url)
                origin.set_url(authenticated_url)

            origin = self.repo.remote(name=remote)

            if branch:
                pull_info = origin.pull(branch)
            else:
                pull_info = origin.pull()

            return {
                "success": True,
                "message": f"Pulled from {remote}",
                "remote": remote,
                "using_token": self.github_token is not None
            }
        except GitCommandError as e:
            return {
                "success": False,
                "error": f"Failed to pull: {str(e)}"
            }

    def _ensure_repo_loaded(self) -> bool:
        """
        Attempt to load/reload the repository from the current repo_path.

        Returns:
            True if repo is loaded successfully, False otherwise
        """
        if self.repo_path and os.path.exists(self.repo_path):
            try:
                self.repo = Repo(self.repo_path)
                return True
            except git.exc.InvalidGitRepositoryError:
                return False
        return False

    def get_status(self) -> Dict[str, Any]:
        """
        Get the current repository status.

        Returns:
            Dict with repository status information
        """
        # Attempt to load repo if not already loaded
        if not self.repo:
            self._ensure_repo_loaded()

        if not self.repo:
            return {"success": False, "error": "No repository loaded"}

        try:
            # Get untracked files
            untracked = self.repo.untracked_files

            # Get modified files
            modified = [item.a_path for item in self.repo.index.diff(None)]

            # Get staged files
            staged = [item.a_path for item in self.repo.index.diff("HEAD")]

            return {
                "success": True,
                "current_branch": self.repo.active_branch.name,
                "untracked_files": untracked,
                "modified_files": modified,
                "staged_files": staged,
                "is_dirty": self.repo.is_dirty()
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get status: {str(e)}"
            }

    def get_branches(self, include_remote: bool = False) -> Dict[str, Any]:
        """
        Get list of branches.

        Args:
            include_remote: Include remote branches in the list

        Returns:
            Dict with branch information
        """
        if not self.repo:
            self._ensure_repo_loaded()

        if not self.repo:
            return {"success": False, "error": "No repository loaded"}

        try:
            local_branches = [head.name for head in self.repo.heads]

            result = {
                "success": True,
                "current_branch": self.repo.active_branch.name,
                "local_branches": local_branches
            }

            if include_remote:
                remote_branches = [ref.name for ref in self.repo.remote().refs]
                result["remote_branches"] = remote_branches

            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get branches: {str(e)}"
            }

    def get_commit_history(self, max_count: int = 10, branch: Optional[str] = None) -> Dict[str, Any]:
        """
        Get commit history.

        Args:
            max_count: Maximum number of commits to retrieve
            branch: Branch name (defaults to current branch)

        Returns:
            Dict with commit history
        """
        if not self.repo:
            self._ensure_repo_loaded()

        if not self.repo:
            return {"success": False, "error": "No repository loaded"}

        try:
            if branch:
                commits = list(self.repo.iter_commits(branch, max_count=max_count))
            else:
                commits = list(self.repo.iter_commits(max_count=max_count))

            commit_list = []
            for commit in commits:
                commit_list.append({
                    "sha": commit.hexsha,
                    "short_sha": commit.hexsha[:7],
                    "message": commit.message.strip(),
                    "author": str(commit.author),
                    "date": commit.committed_datetime.isoformat()
                })

            return {
                "success": True,
                "commits": commit_list,
                "count": len(commit_list)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get commit history: {str(e)}"
            }

    def add_remote(self, name: str, url: str) -> Dict[str, Any]:
        """
        Add a remote repository.

        Args:
            name: Name of the remote
            url: URL of the remote repository

        Returns:
            Dict with status information
        """
        if not self.repo:
            self._ensure_repo_loaded()

        if not self.repo:
            return {"success": False, "error": "No repository loaded"}

        try:
            self.repo.create_remote(name, url)
            return {
                "success": True,
                "message": f"Added remote '{name}' with URL '{url}'"
            }
        except GitCommandError as e:
            return {
                "success": False,
                "error": f"Failed to add remote: {str(e)}"
            }

    def get_diff(self, cached: bool = False, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Get diff of changes.

        Args:
            cached: Show staged changes instead of unstaged
            file_path: Specific file to show diff for (optional)

        Returns:
            Dict with diff information
        """
        if not self.repo:
            self._ensure_repo_loaded()

        if not self.repo:
            return {"success": False, "error": "No repository loaded"}

        try:
            if cached:
                if file_path:
                    diff = self.repo.git.diff('--cached', file_path)
                else:
                    diff = self.repo.git.diff('--cached')
            else:
                if file_path:
                    diff = self.repo.git.diff(file_path)
                else:
                    diff = self.repo.git.diff()

            return {
                "success": True,
                "diff": diff
            }
        except GitCommandError as e:
            return {
                "success": False,
                "error": f"Failed to get diff: {str(e)}"
            }


# Example usage and integration with Google ADK
def example_usage():
    """
    Example usage of the GitOperationsTool for demonstration purposes.
    """
    # Initialize tool
    git_tool = GitOperationsTool()

    # Clone a repository
    result = git_tool.clone_repository(
        repo_url="https://github.com/example/repo.git",
        destination_path="/tmp/example_repo"
    )
    print(f"Clone result: {result}")

    # Create and checkout a new branch
    result = git_tool.create_branch("feature/new-feature", checkout=True)
    print(f"Branch creation: {result}")

    # Stage files
    result = git_tool.stage_files(stage_all=True)
    print(f"Stage result: {result}")

    # Commit changes
    result = git_tool.commit(
        message="Add new feature implementation",
        author_name="Agent",
        author_email="agent@example.com"
    )
    print(f"Commit result: {result}")

    # Push changes
    result = git_tool.push(set_upstream=True)
    print(f"Push result: {result}")

    # Get status
    status = git_tool.get_status()
    print(f"Status: {status}")


if __name__ == "__main__":
    # Example usage
    example_usage()
