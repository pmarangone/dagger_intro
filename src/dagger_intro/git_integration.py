import dagger
from dagger import Secret, dag


async def fetch_issue(repo: str, issue_number: int, gh_token: Secret) -> str:
    """Fetches the issue description via the GitHub CLI."""
    return await (
        dag.container()
        .from_("alpine:latest")
        .with_exec(["apk", "add", "github-cli"])
        .with_secret_variable("GITHUB_TOKEN", gh_token)
        .with_exec(["gh", "issue", "view", str(issue_number), "--repo", repo])
        .stdout()
    )


def clone_repo(gh_token: Secret, repo: str) -> dagger.Directory:
    """Clones the target repository."""
    return (
        dag.git(
            f"https://github.com/{repo}.git",
            http_auth_username="x-access-token",
            http_auth_token=gh_token,
        )
        .head()
        .tree(discard_git_dir=False)
    )


async def create_pull_request(
    agent_type: str,
    modified_source: dagger.Directory,  # Assuming dagger is imported
    issue_number: int,
    gh_token: Secret,
    repo: str,
    design_content: str = "",
    ac_content: str = "",
) -> str:
    """Commits changes to a new branch and opens a GitHub PR."""
    branch_name = f"agent-{agent_type}-fix-{issue_number}"

    # Build the PR body dynamically using collapsible Markdown sections
    pr_body = (
        f"Resolves #{issue_number}.\n\n*Generated securely via Dagger and Pi CLI.*\n\n"
    )

    if design_content:
        pr_body += f"<details>\n<summary><b>Agent 1: Design Document</b></summary>\n\n{design_content}\n\n</details>\n\n"

    if ac_content:
        pr_body += f"<details>\n<summary><b>Agent 2: Acceptance Criteria</b></summary>\n\n{ac_content}\n\n</details>\n"

    return await (
        dag.container()
        .from_("alpine:latest")
        .with_exec(["apk", "add", "github-cli", "git"])
        .with_secret_variable("GITHUB_TOKEN", gh_token)
        .with_directory("/src", modified_source)
        .with_workdir("/src")
        .with_exec(["git", "config", "--global", "user.name", "Dagger Agent"])
        .with_exec(["git", "config", "--global", "user.email", "agent@dagger.local"])
        .with_exec(
            [
                "sh",
                "-c",
                f"git remote set-url origin https://x-access-token:$GITHUB_TOKEN@github.com/{repo}.git",
            ]
        )
        .with_exec(["git", "checkout", "-b", branch_name])
        .with_exec(["git", "add", "."])
        .with_exec(
            ["git", "commit", "-m", f"fix: automated AI fix for issue #{issue_number}"]
        )
        .with_exec(["git", "push", "-f", "-u", "origin", branch_name])
        .with_exec(
            [
                "gh",
                "pr",
                "create",
                "--title",
                f"AI Fix for #{issue_number}",
                "--body",
                pr_body,  # Using the newly constructed PR body
                "--repo",
                repo,
            ]
        )
        .stdout()
    )
