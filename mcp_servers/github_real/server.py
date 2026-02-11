#!/usr/bin/env python3
"""
Real GitHub MCP Server

This MCP server directly uses the PyGithub library to interact with
GitHub repositories instead of calling mock APIs. It provides production-ready
GitHub operations through the Model Context Protocol.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from github import Github
from github.GithubException import GithubException
from github.InputGitAuthor import InputGitAuthor
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize GitHub client
github_client = None
github_repo = None


def initialize_github_client():
    """Initialize GitHub client with token and repository."""
    global github_client, github_repo

    github_token = os.getenv("GITHUB_TOKEN")
    github_repo_name = os.getenv("GITHUB_REPO")  # Format: "owner/repo"

    if not github_token:
        logger.warning("⚠️ GITHUB_TOKEN not set, server will not function")
        return

    if not github_repo_name:
        logger.warning("⚠️ GITHUB_REPO not set, server will not function")
        return

    try:
        github_client = Github(github_token)
        # Test connection
        user = github_client.get_user()
        logger.info(f"✅ Connected to GitHub as {user.login}")

        # Get repository
        github_repo = github_client.get_repo(github_repo_name)
        logger.info(f"✅ Repository: {github_repo.full_name}")

    except GithubException as e:
        logger.error(f"❌ GitHub API error: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to initialize GitHub client: {e}")
        raise


# Initialize on import
try:
    initialize_github_client()
except Exception as e:
    logger.warning(f"⚠️ GitHub client initialization failed: {e}")
    logger.warning("⚠️ Server will start but tools will fail until GITHUB_TOKEN and GITHUB_REPO are set")


# Create FastMCP server
port = int(os.getenv("HTTP_PORT", "3000"))
host = os.getenv("HOST", "0.0.0.0")

mcp = FastMCP("github-real-mcp-server", host=host, port=port)


# Tool parameter models
class ListCommitsParams(BaseModel):
    """Parameters for list_commits tool."""

    since: Optional[str] = Field(
        None, description="Only commits after this date (ISO 8601 format)"
    )
    until: Optional[str] = Field(
        None, description="Only commits before this date (ISO 8601 format)"
    )
    author: Optional[str] = Field(None, description="Filter by author email or username")
    path: Optional[str] = Field(None, description="Filter by file path")
    limit: int = Field(default=50, ge=1, le=100, description="Maximum number of commits")


class GetCommitParams(BaseModel):
    """Parameters for get_commit tool."""
    sha: str = Field(..., description="Commit SHA (full or partial)")


class ListPullRequestsParams(BaseModel):
    """Parameters for list_pull_requests tool."""
    state: Optional[str] = Field(
        "all", description="Filter by state: open, closed, or all"
    )
    author: Optional[str] = Field(None, description="Filter by author username")
    limit: int = Field(default=50, ge=1, le=100, description="Maximum number of PRs")


class GetPullRequestParams(BaseModel):
    """Parameters for get_pull_request tool."""
    pr_number: int = Field(..., description="Pull request number")


class RevertPRParams(BaseModel):
    """Parameters for revert_pr tool."""
    pr_number: int = Field(..., description="Pull request number to revert")
    reason: Optional[str] = Field(
        None, description="Reason for reverting (will be added as comment)"
    )


class CreateRevertPRParams(BaseModel):
    """Parameters for create_revert_pr tool."""
    commit_sha: str = Field(..., description="Full or short commit SHA to revert")
    pr_title: str = Field(..., description="Title for the revert pull request")


class CommentOnPRParams(BaseModel):
    """Parameters for comment_on_pr tool."""
    pr_number: int = Field(..., description="Pull request number")
    comment: str = Field(..., description="Comment body to add to the PR")


# Implementation Helpers

async def handle_list_commits(params: ListCommitsParams) -> str:
    """List commits from repository."""
    logger.info(f"Listing commits (limit: {params.limit})")

    if not github_repo:
        return "Error: GitHub client not initialized."

    loop = asyncio.get_event_loop()

    try:
        # Get commits
        commits = await loop.run_in_executor(None, github_repo.get_commits)

        # Filter and format
        results = []
        count = 0
        for commit in commits:
            if count >= params.limit:
                break

            # Apply filters
            if params.since and commit.commit.author.date.isoformat() < params.since:
                continue
            if params.until and commit.commit.author.date.isoformat() > params.until:
                continue
            if params.author and params.author.lower() not in commit.commit.author.email.lower():
                if params.author.lower() not in (commit.author.login.lower() if commit.author else ""):
                    continue
            if params.path:
                 pass  # Skip path filtering for now

            commit_data = {
                "sha": commit.sha,
                "message": commit.commit.message,
                "author": {
                    "name": commit.commit.author.name,
                    "email": commit.commit.author.email,
                    "login": commit.author.login if commit.author else None,
                },
                "timestamp": commit.commit.author.date.isoformat(),
                "url": commit.html_url,
            }
            results.append(commit_data)
            count += 1

        return json.dumps({"commits": results}, indent=2)
    except Exception as e:
        logger.error(f"Error listing commits: {e}")
        return f"Error listing commits: {e}"


async def handle_get_commit(params: GetCommitParams) -> str:
    """Get commit details with diff."""
    logger.info(f"Getting commit: {params.sha}")

    if not github_repo:
        return "Error: GitHub client not initialized."

    loop = asyncio.get_event_loop()
    try:
        commit = await loop.run_in_executor(None, github_repo.get_commit, params.sha)

        # Get diff (patch)
        patch = commit.patch if hasattr(commit, "patch") else None

        result = {
            "sha": commit.sha,
            "message": commit.commit.message,
            "author": {
                "name": commit.commit.author.name,
                "email": commit.commit.author.email,
                "login": commit.author.login if commit.author else None,
            },
            "timestamp": commit.commit.author.date.isoformat(),
            "url": commit.html_url,
            "files_changed": len(commit.files),
            "additions": commit.stats.additions,
            "deletions": commit.stats.deletions,
            "diff": patch,
        }

        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting commit: {e}")
        return f"Error getting commit: {e}"


async def handle_list_pull_requests(params: ListPullRequestsParams) -> str:
    """List pull requests."""
    logger.info(f"Listing pull requests (state: {params.state}, limit: {params.limit})")

    if not github_repo:
        return "Error: GitHub client not initialized."

    loop = asyncio.get_event_loop()
    try:
        prs = await loop.run_in_executor(
            None, github_repo.get_pulls, params.state if params.state != "all" else None
        )

        results = []
        count = 0
        for pr in prs:
            if count >= params.limit:
                break

            # Filter by author if specified
            if params.author and params.author.lower() not in pr.user.login.lower():
                continue

            pr_data = {
                "number": pr.number,
                "title": pr.title,
                "state": pr.state,
                "author": pr.user.login,
                "created_at": pr.created_at.isoformat(),
                "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                "base_branch": pr.base.ref,
                "head_branch": pr.head.ref,
                "url": pr.html_url,
            }
            results.append(pr_data)
            count += 1

        return json.dumps({"pull_requests": results}, indent=2)
    except Exception as e:
        logger.error(f"Error listing pull requests: {e}")
        return f"Error listing pull requests: {e}"


async def handle_get_pull_request(params: GetPullRequestParams) -> str:
    """Get pull request details."""
    logger.info(f"Getting pull request: #{params.pr_number}")

    if not github_repo:
        return "Error: GitHub client not initialized."

    loop = asyncio.get_event_loop()
    try:
        pr = await loop.run_in_executor(None, github_repo.get_pull, params.pr_number)

        result = {
            "number": pr.number,
            "title": pr.title,
            "state": pr.state,
            "author": pr.user.login,
            "created_at": pr.created_at.isoformat(),
            "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
            "base_branch": pr.base.ref,
            "head_branch": pr.head.ref,
            "url": pr.html_url,
            "body": pr.body,
            "mergeable": pr.mergeable,
            "merged": pr.merged,
        }

        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting pull request: {e}")
        return f"Error getting pull request: {e}"


async def handle_revert_pr(params: RevertPRParams) -> str:
    """Revert a pull request."""
    logger.info(f"Reverting pull request: #{params.pr_number}")

    if not github_repo:
        return "Error: GitHub client not initialized."

    loop = asyncio.get_event_loop()
    try:
        pr = await loop.run_in_executor(None, github_repo.get_pull, params.pr_number)

        # Create review requesting changes
        review_body = f"Reverting PR due to: {params.reason or 'Issue detected in production'}"
        review = await loop.run_in_executor(
            None, pr.create_review, None, "REQUEST_CHANGES", review_body
        )

        result = {
            "status": "revert_requested",
            "pr_number": params.pr_number,
            "review_id": review.id,
            "message": f"Requested changes on PR #{params.pr_number}",
            "reason": params.reason,
        }

        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error reverting PR: {e}")
        return f"Error reverting PR: {e}"


def _create_revert_pr_sync(commit_sha: str, pr_title: str) -> dict:
    """Synchronous implementation: create revert commit and open PR. Returns dict with pr_url and pr_number."""
    commit = github_repo.get_commit(commit_sha)
    if not commit.parents:
        raise ValueError(f"Commit {commit_sha} has no parent (root commit cannot be reverted)")
    parent = commit.parents[0]
    parent_tree_sha = parent.commit.tree.sha
    default_branch = github_repo.default_branch
    base_branch = github_repo.get_branch(default_branch)
    main_sha = base_branch.commit.sha
    short_sha = commit.sha[:7]
    branch_name = f"revert-{short_sha}"
    revert_message = f"Revert \"{commit.commit.message.split(chr(10))[0]}\"\n\nThis reverts commit {commit.sha}."
    author = InputGitAuthor("SRE Agent", "sre-agent@local", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    parent_tree = github_repo.get_git_tree(parent_tree_sha)
    main_git_commit = github_repo.get_git_commit(main_sha)
    new_commit = github_repo.create_git_commit(revert_message, parent_tree, [main_git_commit], author, author)
    github_repo.create_git_ref(f"refs/heads/{branch_name}", new_commit.sha)
    pr = github_repo.create_pull(title=pr_title, body=revert_message, head=branch_name, base=default_branch)
    return {"pr_url": pr.html_url, "pr_number": pr.number, "branch": branch_name}


async def handle_create_revert_pr(params: CreateRevertPRParams) -> str:
    """Create a revert commit for the given SHA and open a PR against main. Returns PR URL."""
    logger.info(f"Creating revert PR for commit {params.commit_sha} with title: {params.pr_title}")
    
    if not github_repo:
        return "Error: GitHub client not initialized."

    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            None, _create_revert_pr_sync, params.commit_sha, params.pr_title
        )
        logger.info(f"Revert PR created: {result['pr_url']}")
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating revert PR: {e}")
        return f"Error creating revert PR: {e}"


async def handle_comment_on_pr(params: CommentOnPRParams) -> str:
    """Add a comment to a pull request. Returns comment ID."""
    logger.info(f"Adding comment to PR #{params.pr_number}")
    
    if not github_repo:
        return "Error: GitHub client not initialized."

    loop = asyncio.get_event_loop()
    try:
        pr = await loop.run_in_executor(None, github_repo.get_pull, params.pr_number)
        comment = await loop.run_in_executor(None, pr.create_issue_comment, params.comment)
        result = {"comment_id": comment.id, "pr_number": params.pr_number, "url": comment.html_url}
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error commenting on PR: {e}")
        return f"Error commenting on PR: {e}"


# Tool wrappers

@mcp.tool()
async def list_commits(since: str = None, until: str = None, author: str = None, path: str = None, limit: int = 50) -> str:
    """List commits from the repository with optional filtering."""
    return await handle_list_commits(
        ListCommitsParams(since=since, until=until, author=author, path=path, limit=limit)
    )

@mcp.tool()
async def get_commit(sha: str) -> str:
    """Get detailed information about a specific commit including diff."""
    return await handle_get_commit(GetCommitParams(sha=sha))

@mcp.tool()
async def list_pull_requests(state: str = "all", author: str = None, limit: int = 50) -> str:
    """List pull requests with optional filtering."""
    return await handle_list_pull_requests(
        ListPullRequestsParams(state=state, author=author, limit=limit)
    )

@mcp.tool()
async def get_pull_request(pr_number: int) -> str:
    """Get detailed information about a specific pull request."""
    return await handle_get_pull_request(GetPullRequestParams(pr_number=pr_number))

@mcp.tool()
async def revert_pr(pr_number: int, reason: str = None) -> str:
    """Revert a pull request by requesting changes."""
    return await handle_revert_pr(RevertPRParams(pr_number=pr_number, reason=reason))

@mcp.tool()
async def create_revert_pr(commit_sha: str, pr_title: str) -> str:
    """Create a revert commit for the given SHA and open a PR against main."""
    return await handle_create_revert_pr(CreateRevertPRParams(commit_sha=commit_sha, pr_title=pr_title))

@mcp.tool()
async def comment_on_pr(pr_number: int, comment: str) -> str:
    """Add a comment to a pull request."""
    return await handle_comment_on_pr(CommentOnPRParams(pr_number=pr_number, comment=comment))


if __name__ == "__main__":
    logger.info("Starting FastMCP server execution...")
    mcp.run(transport="sse")
