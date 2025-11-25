"""
Unit Tests for Git Operations Tool

This test suite covers the GitOperationsTool class functionality including:
- Repository initialization
- Cloning repositories
- Branch creation and checkout
- Staging and committing changes
- Pushing and pulling changes
- Repository status and history
- Error handling

Uses pytest and temporary directories for isolated testing.
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from git import Repo, GitCommandError
import sys

# Add parent directory to path to import the tool
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools.git_operations_tool import GitOperationsTool


class TestGitOperationsToolInit:
    """Test GitOperationsTool initialization"""

    def test_init_with_no_params(self):
        """Test initialization with no parameters"""
        git_tool = GitOperationsTool(use_env_config=False)
        assert git_tool.repo is None
        assert git_tool.repo_path is None
        assert git_tool.github_token is None
        assert git_tool.default_branch == 'main'

    def test_init_with_env_config(self):
        """Test initialization with environment configuration"""
        with patch.dict(os.environ, {
            'GIT_REPO_PATH': '/tmp/test_repo',
            'GITHUB_TOKEN': 'test_token',
            'GIT_REPO_URL': 'https://github.com/test/repo.git',
            'GIT_DEFAULT_BRANCH': 'develop'
        }):
            git_tool = GitOperationsTool(use_env_config=True)
            assert git_tool.repo_path == '/tmp/test_repo'
            assert git_tool.github_token == 'test_token'
            assert git_tool.default_repo_url == 'https://github.com/test/repo.git'
            assert git_tool.default_branch == 'develop'

    def test_init_with_existing_repo(self):
        """Test initialization with an existing repository"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a git repo
            Repo.init(temp_dir)

            # Initialize tool with existing repo
            git_tool = GitOperationsTool(repo_path=temp_dir, use_env_config=False)
            assert git_tool.repo is not None
            assert isinstance(git_tool.repo, Repo)

    def test_init_with_invalid_repo(self):
        """Test initialization with invalid repository path"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Directory exists but is not a git repo
            with pytest.raises(ValueError, match="is not a valid Git repository"):
                GitOperationsTool(repo_path=temp_dir, use_env_config=False)


class TestGitOperationsToolAuthentication:
    """Test authentication URL conversion"""

    def test_get_authenticated_url_no_token(self):
        """Test URL conversion without token"""
        git_tool = GitOperationsTool(use_env_config=False)
        url = "https://github.com/test/repo.git"
        result = git_tool._get_authenticated_url(url)
        assert result == url

    def test_get_authenticated_url_with_token_https(self):
        """Test URL conversion with token for HTTPS URL"""
        git_tool = GitOperationsTool(github_token="test_token", use_env_config=False)
        url = "https://github.com/test/repo.git"
        result = git_tool._get_authenticated_url(url)
        assert result == "https://test_token@github.com/test/repo.git"

    def test_get_authenticated_url_with_token_ssh(self):
        """Test URL conversion with token for SSH URL"""
        git_tool = GitOperationsTool(github_token="test_token", use_env_config=False)
        url = "git@github.com:test/repo.git"
        result = git_tool._get_authenticated_url(url)
        assert result == "https://test_token@github.com/test/repo.git"


class TestGitOperationsToolClone:
    """Test repository cloning functionality"""

    def test_clone_repository_success(self):
        """Test successful repository cloning"""
        with tempfile.TemporaryDirectory() as source_dir:
            with tempfile.TemporaryDirectory() as dest_dir:
                # Create a source repo
                source_repo = Repo.init(source_dir)

                # Create a test file and commit
                test_file = Path(source_dir) / "test.txt"
                test_file.write_text("test content")
                source_repo.index.add(["test.txt"])
                source_repo.index.commit("Initial commit")

                # Get the actual branch name (could be 'master' or 'main')
                current_branch = source_repo.active_branch.name

                # Clone the repository with the actual branch name
                git_tool = GitOperationsTool(use_env_config=False)
                clone_dest = os.path.join(dest_dir, "cloned_repo")
                result = git_tool.clone_repository(
                    repo_url=source_dir,
                    destination_path=clone_dest,
                    branch=current_branch  # Use actual branch name
                )

                assert result["success"] is True, f"Clone failed: {result.get('error', 'Unknown error')}"
                assert "Successfully cloned" in result["message"]
                assert os.path.exists(clone_dest)
                assert git_tool.repo is not None

    def test_clone_repository_no_url(self):
        """Test clone without URL provided"""
        git_tool = GitOperationsTool(use_env_config=False)
        result = git_tool.clone_repository()

        assert result["success"] is False
        assert "No repository URL provided" in result["error"]

    def test_clone_repository_no_destination(self):
        """Test clone without destination path"""
        git_tool = GitOperationsTool(use_env_config=False)
        result = git_tool.clone_repository(repo_url="https://github.com/test/repo.git")

        assert result["success"] is False
        assert "No destination path provided" in result["error"]

    def test_clone_repository_with_branch(self):
        """Test cloning specific branch"""
        with tempfile.TemporaryDirectory() as source_dir:
            with tempfile.TemporaryDirectory() as dest_dir:
                # Create source repo with multiple branches
                source_repo = Repo.init(source_dir)
                test_file = Path(source_dir) / "test.txt"
                test_file.write_text("test")
                source_repo.index.add(["test.txt"])
                source_repo.index.commit("Initial commit")

                # Create a new branch
                source_repo.create_head("feature")

                # Clone specific branch
                git_tool = GitOperationsTool(use_env_config=False)
                clone_dest = os.path.join(dest_dir, "cloned_repo")
                result = git_tool.clone_repository(
                    repo_url=source_dir,
                    destination_path=clone_dest,
                    branch="feature"
                )

                assert result["success"] is True
                assert result["current_branch"] == "feature"


class TestGitOperationsToolBranches:
    """Test branch operations"""

    @pytest.fixture
    def git_repo(self):
        """Fixture to create a temporary git repository"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Repo.init(temp_dir)
            # Create initial commit
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test")
            repo.index.add(["test.txt"])
            repo.index.commit("Initial commit")

            yield temp_dir

    def test_create_branch_success(self, git_repo):
        """Test successful branch creation"""
        git_tool = GitOperationsTool(repo_path=git_repo, use_env_config=False)
        result = git_tool.create_branch("feature/test", checkout=True)

        assert result["success"] is True
        assert result["branch_name"] == "feature/test"
        assert result["checked_out"] is True
        assert result["current_branch"] == "feature/test"

    def test_create_branch_without_checkout(self, git_repo):
        """Test branch creation without checkout"""
        git_tool = GitOperationsTool(repo_path=git_repo, use_env_config=False)
        result = git_tool.create_branch("feature/test", checkout=False)

        assert result["success"] is True
        assert result["checked_out"] is False
        # Current branch should still be master/main
        assert result["current_branch"] in ["master", "main"]

    def test_create_branch_no_repo(self):
        """Test branch creation without repository"""
        git_tool = GitOperationsTool(use_env_config=False)
        result = git_tool.create_branch("feature/test")

        assert result["success"] is False
        assert "No repository loaded" in result["error"]

    def test_checkout_branch_success(self, git_repo):
        """Test successful branch checkout"""
        git_tool = GitOperationsTool(repo_path=git_repo, use_env_config=False)

        # Create a branch first
        git_tool.create_branch("feature/test", checkout=False)

        # Checkout the branch
        result = git_tool.checkout_branch("feature/test")

        assert result["success"] is True
        assert result["current_branch"] == "feature/test"

    def test_checkout_nonexistent_branch(self, git_repo):
        """Test checkout of non-existent branch"""
        git_tool = GitOperationsTool(repo_path=git_repo, use_env_config=False)
        result = git_tool.checkout_branch("nonexistent")

        assert result["success"] is False
        assert "does not exist" in result["error"]

    def test_checkout_branch_create_if_missing(self, git_repo):
        """Test checkout with create_if_missing option"""
        git_tool = GitOperationsTool(repo_path=git_repo, use_env_config=False)
        result = git_tool.checkout_branch("feature/new", create_if_missing=True)

        assert result["success"] is True
        assert result["current_branch"] == "feature/new"

    def test_get_branches(self, git_repo):
        """Test getting list of branches"""
        git_tool = GitOperationsTool(repo_path=git_repo, use_env_config=False)

        # Create a few branches
        git_tool.create_branch("feature/one", checkout=False)
        git_tool.create_branch("feature/two", checkout=False)

        result = git_tool.get_branches()

        assert result["success"] is True
        assert len(result["local_branches"]) >= 3  # master/main + 2 feature branches
        assert "feature/one" in result["local_branches"]
        assert "feature/two" in result["local_branches"]


class TestGitOperationsToolStaging:
    """Test file staging operations"""

    @pytest.fixture
    def git_repo_with_changes(self):
        """Fixture to create a repo with uncommitted changes"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Repo.init(temp_dir)

            # Initial commit
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("initial")
            repo.index.add(["test.txt"])
            repo.index.commit("Initial commit")

            # Create new files
            new_file1 = Path(temp_dir) / "file1.txt"
            new_file1.write_text("file1 content")
            new_file2 = Path(temp_dir) / "file2.txt"
            new_file2.write_text("file2 content")

            yield temp_dir

    def test_stage_all_files(self, git_repo_with_changes):
        """Test staging all files"""
        git_tool = GitOperationsTool(repo_path=git_repo_with_changes, use_env_config=False)
        result = git_tool.stage_files(stage_all=True)

        assert result["success"] is True
        assert "Staged all files" in result["message"]

    def test_stage_specific_files(self, git_repo_with_changes):
        """Test staging specific files"""
        git_tool = GitOperationsTool(repo_path=git_repo_with_changes, use_env_config=False)
        result = git_tool.stage_files(file_paths=["file1.txt"])

        assert result["success"] is True
        assert len(result["staged_files"]) == 1
        assert "file1.txt" in result["staged_files"]

    def test_stage_no_files_specified(self, git_repo_with_changes):
        """Test staging without specifying files"""
        git_tool = GitOperationsTool(repo_path=git_repo_with_changes, use_env_config=False)
        result = git_tool.stage_files()

        assert result["success"] is False
        assert "No files specified" in result["error"]


class TestGitOperationsToolCommit:
    """Test commit operations"""

    @pytest.fixture
    def git_repo_with_staged(self):
        """Fixture with staged changes"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Repo.init(temp_dir)

            # Create and stage a file
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content")
            repo.index.add(["test.txt"])

            yield temp_dir

    def test_commit_success(self, git_repo_with_staged):
        """Test successful commit"""
        git_tool = GitOperationsTool(repo_path=git_repo_with_staged, use_env_config=False)
        result = git_tool.commit("Test commit message")

        assert result["success"] is True
        assert "Commit created successfully" in result["message"]
        assert result["commit_message"] == "Test commit message"
        assert "commit_sha" in result
        assert len(result["commit_sha"]) == 40  # Full SHA

    def test_commit_with_author(self, git_repo_with_staged):
        """Test commit with custom author"""
        git_tool = GitOperationsTool(repo_path=git_repo_with_staged, use_env_config=False)
        result = git_tool.commit(
            "Test commit",
            author_name="Test Author",
            author_email="test@example.com"
        )

        assert result["success"] is True
        assert "Test Author" in result["author"]

    def test_commit_no_repo(self):
        """Test commit without repository"""
        git_tool = GitOperationsTool(use_env_config=False)
        result = git_tool.commit("Test message")

        assert result["success"] is False
        assert "No repository loaded" in result["error"]


class TestGitOperationsToolStatus:
    """Test repository status operations"""

    @pytest.fixture
    def git_repo_with_mixed_changes(self):
        """Fixture with mixed changes (staged, unstaged, untracked)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Repo.init(temp_dir)

            # Initial commit
            tracked_file = Path(temp_dir) / "tracked.txt"
            tracked_file.write_text("tracked")
            repo.index.add(["tracked.txt"])
            repo.index.commit("Initial commit")

            # Modify tracked file (unstaged)
            tracked_file.write_text("modified tracked")

            # Create new file and stage it
            staged_file = Path(temp_dir) / "staged.txt"
            staged_file.write_text("staged content")
            repo.index.add(["staged.txt"])

            # Create untracked file
            untracked_file = Path(temp_dir) / "untracked.txt"
            untracked_file.write_text("untracked content")

            yield temp_dir

    def test_get_status(self, git_repo_with_mixed_changes):
        """Test getting repository status"""
        git_tool = GitOperationsTool(repo_path=git_repo_with_mixed_changes, use_env_config=False)
        result = git_tool.get_status()

        assert result["success"] is True
        assert "current_branch" in result
        assert "untracked_files" in result
        assert "modified_files" in result
        assert "staged_files" in result
        assert result["is_dirty"] is True

        # Check specific files
        assert "untracked.txt" in result["untracked_files"]
        assert "tracked.txt" in result["modified_files"]
        assert "staged.txt" in result["staged_files"]

    def test_get_status_clean_repo(self):
        """Test status of clean repository"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Repo.init(temp_dir)
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test")
            repo.index.add(["test.txt"])
            repo.index.commit("Initial commit")

            git_tool = GitOperationsTool(repo_path=temp_dir, use_env_config=False)
            result = git_tool.get_status()

            assert result["success"] is True
            assert result["is_dirty"] is False
            assert len(result["untracked_files"]) == 0
            assert len(result["modified_files"]) == 0


class TestGitOperationsToolHistory:
    """Test commit history operations"""

    @pytest.fixture
    def git_repo_with_history(self):
        """Fixture with commit history"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Repo.init(temp_dir)

            # Create multiple commits
            for i in range(5):
                test_file = Path(temp_dir) / f"file{i}.txt"
                test_file.write_text(f"content {i}")
                repo.index.add([f"file{i}.txt"])
                repo.index.commit(f"Commit {i}")

            yield temp_dir

    def test_get_commit_history(self, git_repo_with_history):
        """Test getting commit history"""
        git_tool = GitOperationsTool(repo_path=git_repo_with_history, use_env_config=False)
        result = git_tool.get_commit_history(max_count=3)

        assert result["success"] is True
        assert len(result["commits"]) == 3
        assert result["count"] == 3

        # Check commit structure
        commit = result["commits"][0]
        assert "sha" in commit
        assert "short_sha" in commit
        assert "message" in commit
        assert "author" in commit
        assert "date" in commit
        assert len(commit["short_sha"]) == 7

    def test_get_commit_history_all(self, git_repo_with_history):
        """Test getting full commit history"""
        git_tool = GitOperationsTool(repo_path=git_repo_with_history, use_env_config=False)
        result = git_tool.get_commit_history(max_count=10)

        assert result["success"] is True
        assert result["count"] == 5  # All commits


class TestGitOperationsToolDiff:
    """Test diff operations"""

    @pytest.fixture
    def git_repo_with_changes(self):
        """Fixture with changes for diff"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Repo.init(temp_dir)

            # Initial commit
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("original content")
            repo.index.add(["test.txt"])
            repo.index.commit("Initial commit")

            # Modify file
            test_file.write_text("modified content")

            yield temp_dir

    def test_get_diff_unstaged(self, git_repo_with_changes):
        """Test getting unstaged diff"""
        git_tool = GitOperationsTool(repo_path=git_repo_with_changes, use_env_config=False)
        result = git_tool.get_diff()

        assert result["success"] is True
        assert "diff" in result
        assert "modified content" in result["diff"] or "test.txt" in result["diff"]

    def test_get_diff_staged(self, git_repo_with_changes):
        """Test getting staged diff"""
        git_tool = GitOperationsTool(repo_path=git_repo_with_changes, use_env_config=False)

        # Stage the changes first
        git_tool.stage_files(file_paths=["test.txt"])

        result = git_tool.get_diff(cached=True)

        assert result["success"] is True
        assert "diff" in result


class TestGitOperationsToolRemote:
    """Test remote operations"""

    def test_add_remote_success(self):
        """Test adding a remote"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Repo.init(temp_dir)
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test")
            repo.index.add(["test.txt"])
            repo.index.commit("Initial commit")

            git_tool = GitOperationsTool(repo_path=temp_dir, use_env_config=False)
            result = git_tool.add_remote("origin", "https://github.com/test/repo.git")

            assert result["success"] is True
            assert "Added remote 'origin'" in result["message"]

    def test_add_remote_no_repo(self):
        """Test adding remote without repository"""
        git_tool = GitOperationsTool(use_env_config=False)
        result = git_tool.add_remote("origin", "https://github.com/test/repo.git")

        assert result["success"] is False
        assert "No repository loaded" in result["error"]


class TestGitOperationsToolPushPull:
    """Test push and pull operations (mocked)"""

    @pytest.fixture
    def git_repo_with_remote(self):
        """Fixture with a repository that has a remote configured"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Repo.init(temp_dir)
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test")
            repo.index.add(["test.txt"])
            repo.index.commit("Initial commit")

            # Add a mock remote
            repo.create_remote("origin", "https://github.com/test/repo.git")

            yield temp_dir

    def test_push_no_repo(self):
        """Test push without repository"""
        git_tool = GitOperationsTool(use_env_config=False)
        result = git_tool.push()

        assert result["success"] is False
        assert "No repository loaded" in result["error"]

    def test_pull_no_repo(self):
        """Test pull without repository"""
        git_tool = GitOperationsTool(use_env_config=False)
        result = git_tool.pull()

        assert result["success"] is False
        assert "No repository loaded" in result["error"]


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
