"""
GitHub Operations Tool for Google ADK Agent

This tool provides GitHub API operations functionality for agents using PyGithub.
It handles creating pull requests, managing issues, and other GitHub operations.
Supports Personal Access Token (PAT) authentication and environment-based configuration.
"""

from typing import Optional, List, Dict, Any
from github import Github, GithubException, Auth
import os
from dotenv import load_dotenv
from pathlib import Path
import git
from git import Repo

# Load environment variables from .env file
load_dotenv()


class GitHubOperationsTool:
    """
    A comprehensive GitHub operations tool for AI agents.

    This class provides methods for GitHub operations including:
    - Creating pull requests
    - Managing labels and assignees
    - Getting repository information
    - Personal Access Token (PAT) authentication
    - Environment-based configuration
    """

    def __init__(
        self,
        github_token: Optional[str] = None,
        repo_path: Optional[str] = None,
        use_env_config: bool = True
    ):
        """
        Initialize the GitHub operations tool.

        Args:
            github_token: GitHub Personal Access Token for authentication.
                         If None and use_env_config is True, will try to load from
                         GITHUB_TOKEN env variable.
            repo_path: Path to the Git repository. If None and use_env_config
                      is True, will try to load from GIT_REPO_PATH env variable.
            use_env_config: Whether to load configuration from environment variables.
        """
        # Load from environment if requested
        if use_env_config:
            self.github_token = github_token or os.getenv('GITHUB_TOKEN')
            self.repo_path = repo_path or os.getenv('GIT_REPO_PATH')
        else:
            self.github_token = github_token
            self.repo_path = repo_path

        if not self.github_token:
            raise ValueError(
                "GitHub token is required. Set GITHUB_TOKEN environment variable "
                "or pass github_token parameter."
            )

        # Initialize GitHub API client with token authentication
        auth = Auth.Token(self.github_token)
        self.github = Github(auth=auth)

        # Initialize repository information
        self.repo: Optional[Repo] = None
        self.github_repo = None

        if self.repo_path and os.path.exists(self.repo_path):
            try:
                self.repo = Repo(self.repo_path)
                # Extract owner and repo name from remote URL
                self._initialize_github_repo()
            except git.exc.InvalidGitRepositoryError:
                pass

    def _initialize_github_repo(self):
        """
        Initialize the GitHub repository object from the local git repository.
        Extracts the owner and repo name from the remote URL.
        """
        if not self.repo:
            return

        try:
            # Get the remote URL
            remote_url = self.repo.remote('origin').url

            # Parse owner and repo name from URL
            # Handles both HTTPS and SSH URLs
            if remote_url.startswith('git@github.com:'):
                # SSH: git@github.com:owner/repo.git
                repo_path = remote_url.replace('git@github.com:', '').replace('.git', '')
            elif 'github.com/' in remote_url:
                # HTTPS: https://github.com/owner/repo.git or https://token@github.com/owner/repo.git
                repo_path = remote_url.split('github.com/')[-1].replace('.git', '')
                # Remove token if present
                if '@' in repo_path:
                    repo_path = repo_path.split('@')[-1]
            else:
                return

            # Get the GitHub repository object
            self.github_repo = self.github.get_repo(repo_path)

        except Exception:
            # If we can't get the repo, silently fail - it will be required for operations
            pass

    def _ensure_github_repo(self) -> bool:
        """
        Ensure that the GitHub repository is initialized.

        Returns:
            True if initialized, False otherwise
        """
        if not self.github_repo:
            if self.repo_path and os.path.exists(self.repo_path):
                self.repo = Repo(self.repo_path)
                self._initialize_github_repo()

        return self.github_repo is not None

    def create_pull_request(
        self,
        title: str,
        head: Optional[str] = None,
        base: str = "master",
        body: Optional[str] = None,
        draft: bool = False,
        maintainer_can_modify: bool = True
    ) -> Dict[str, Any]:
        """
        Create a pull request on GitHub.

        This method assumes that the branch has already been pushed to the remote.

        Args:
            title: Title of the pull request
            head: The name of the branch where your changes are implemented.
                 If None, uses the current branch from the local repository.
            base: The name of the branch you want the changes pulled into (default: "main")
            body: The contents of the pull request (optional)
            draft: Whether to create the pull request as a draft (default: False)
            maintainer_can_modify: Whether maintainers can modify the PR (default: True)

        Returns:
            Dict with PR information and status
        """
        # Ensure GitHub repo is initialized
        if not self._ensure_github_repo():
            return {
                "success": False,
                "error": "GitHub repository not initialized. Check repo_path and remote URL."
            }

        try:
            # If head is not specified, use current branch
            if not head:
                if not self.repo:
                    return {
                        "success": False,
                        "error": "No branch specified and no local repository available"
                    }
                head = self.repo.active_branch.name

            # Create the pull request
            pr = self.github_repo.create_pull(
                title=title,
                body=body or "",
                head=head,
                base=base,
                draft=draft,
                maintainer_can_modify=maintainer_can_modify
            )

            return {
                "success": True,
                "message": f"Pull request created successfully",
                "pr_number": pr.number,
                "pr_url": pr.html_url,
                "title": pr.title,
                "head": head,
                "base": base,
                "state": pr.state,
                "draft": pr.draft
            }

        except GithubException as e:
            return {
                "success": False,
                "error": f"Failed to create pull request: {e.data.get('message', str(e))}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create pull request: {str(e)}"
            }

    def add_labels_to_pr(
        self,
        pr_number: int,
        labels: List[str]
    ) -> Dict[str, Any]:
        """
        Add labels to a pull request.

        Args:
            pr_number: Pull request number
            labels: List of label names to add

        Returns:
            Dict with status information
        """
        if not self._ensure_github_repo():
            return {
                "success": False,
                "error": "GitHub repository not initialized"
            }

        try:
            pr = self.github_repo.get_pull(pr_number)
            pr.add_to_labels(*labels)

            return {
                "success": True,
                "message": f"Added {len(labels)} label(s) to PR #{pr_number}",
                "labels": labels
            }
        except GithubException as e:
            return {
                "success": False,
                "error": f"Failed to add labels: {e.data.get('message', str(e))}"
            }

    def add_assignees_to_pr(
        self,
        pr_number: int,
        assignees: List[str]
    ) -> Dict[str, Any]:
        """
        Add assignees to a pull request.

        Args:
            pr_number: Pull request number
            assignees: List of GitHub usernames to assign

        Returns:
            Dict with status information
        """
        if not self._ensure_github_repo():
            return {
                "success": False,
                "error": "GitHub repository not initialized"
            }

        try:
            pr = self.github_repo.get_pull(pr_number)
            pr.add_to_assignees(*assignees)

            return {
                "success": True,
                "message": f"Added {len(assignees)} assignee(s) to PR #{pr_number}",
                "assignees": assignees
            }
        except GithubException as e:
            return {
                "success": False,
                "error": f"Failed to add assignees: {e.data.get('message', str(e))}"
            }

    def add_reviewers_to_pr(
        self,
        pr_number: int,
        reviewers: List[str],
        team_reviewers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Request reviewers for a pull request.

        Args:
            pr_number: Pull request number
            reviewers: List of GitHub usernames to request as reviewers
            team_reviewers: List of team slugs to request as reviewers (optional)

        Returns:
            Dict with status information
        """
        if not self._ensure_github_repo():
            return {
                "success": False,
                "error": "GitHub repository not initialized"
            }

        try:
            pr = self.github_repo.get_pull(pr_number)

            if team_reviewers:
                pr.create_review_request(
                    reviewers=reviewers,
                    team_reviewers=team_reviewers
                )
            else:
                pr.create_review_request(reviewers=reviewers)

            return {
                "success": True,
                "message": f"Requested {len(reviewers)} reviewer(s) for PR #{pr_number}",
                "reviewers": reviewers,
                "team_reviewers": team_reviewers or []
            }
        except GithubException as e:
            return {
                "success": False,
                "error": f"Failed to add reviewers: {e.data.get('message', str(e))}"
            }

    def get_pull_request(self, pr_number: int) -> Dict[str, Any]:
        """
        Get information about a pull request.

        Args:
            pr_number: Pull request number

        Returns:
            Dict with PR information
        """
        if not self._ensure_github_repo():
            return {
                "success": False,
                "error": "GitHub repository not initialized"
            }

        try:
            pr = self.github_repo.get_pull(pr_number)

            return {
                "success": True,
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "state": pr.state,
                "draft": pr.draft,
                "head": pr.head.ref,
                "base": pr.base.ref,
                "url": pr.html_url,
                "created_at": pr.created_at.isoformat(),
                "updated_at": pr.updated_at.isoformat(),
                "mergeable": pr.mergeable,
                "merged": pr.merged,
                "author": pr.user.login
            }
        except GithubException as e:
            return {
                "success": False,
                "error": f"Failed to get pull request: {e.data.get('message', str(e))}"
            }

    def list_open_pull_requests(self, state: str = "open", max_count: int = 10) -> Dict[str, Any]:
        """
        List pull requests in the repository.

        Args:
            state: State of PRs to list: "open", "closed", or "all" (default: "open")
            max_count: Maximum number of PRs to retrieve (default: 10)

        Returns:
            Dict with list of pull requests
        """
        if not self._ensure_github_repo():
            return {
                "success": False,
                "error": "GitHub repository not initialized"
            }

        try:
            pulls = self.github_repo.get_pulls(state=state)
            pr_list = []

            for i, pr in enumerate(pulls):
                if i >= max_count:
                    break

                pr_list.append({
                    "number": pr.number,
                    "title": pr.title,
                    "state": pr.state,
                    "draft": pr.draft,
                    "head": pr.head.ref,
                    "base": pr.base.ref,
                    "url": pr.html_url,
                    "author": pr.user.login,
                    "created_at": pr.created_at.isoformat()
                })

            return {
                "success": True,
                "count": len(pr_list),
                "pull_requests": pr_list
            }
        except GithubException as e:
            return {
                "success": False,
                "error": f"Failed to list pull requests: {e.data.get('message', str(e))}"
            }

    def get_repository_info(self) -> Dict[str, Any]:
        """
        Get information about the GitHub repository.

        Returns:
            Dict with repository information
        """
        if not self._ensure_github_repo():
            return {
                "success": False,
                "error": "GitHub repository not initialized"
            }

        try:
            repo = self.github_repo

            return {
                "success": True,
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "url": repo.html_url,
                "default_branch": repo.default_branch,
                "private": repo.private,
                "fork": repo.fork,
                "stars": repo.stargazers_count,
                "watchers": repo.watchers_count,
                "forks": repo.forks_count,
                "open_issues": repo.open_issues_count
            }
        except GithubException as e:
            return {
                "success": False,
                "error": f"Failed to get repository info: {e.data.get('message', str(e))}"
            }


# Example usage and integration with Google ADK
def example_usage():
    """
    Example usage of the GitHubOperationsTool for demonstration purposes.
    """
    # Initialize tool (uses GITHUB_TOKEN from environment)
    github_tool = GitHubOperationsTool(repo_path="/path/to/repo")

    # Get repository info
    result = github_tool.get_repository_info()
    print(f"Repository info: {result}")

    # Create a pull request (assumes branch is already pushed)
    result = github_tool.create_pull_request(
        title="Add new feature",
        head="feature/new-feature",
        base="main",
        body="This PR adds a new feature to the application.\n\n## Changes\n- Added feature X\n- Updated documentation",
        draft=False
    )
    print(f"Create PR result: {result}")

    if result["success"]:
        pr_number = result["pr_number"]

        # Add labels to the PR
        result = github_tool.add_labels_to_pr(
            pr_number=pr_number,
            labels=["enhancement", "documentation"]
        )
        print(f"Add labels result: {result}")

        # Add reviewers
        result = github_tool.add_reviewers_to_pr(
            pr_number=pr_number,
            reviewers=["reviewer1", "reviewer2"]
        )
        print(f"Add reviewers result: {result}")

    # List open pull requests
    result = github_tool.list_open_pull_requests(max_count=5)
    print(f"Open PRs: {result}")


if __name__ == "__main__":
    # Example usage
    example_usage()
