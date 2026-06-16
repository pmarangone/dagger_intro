import dagger
from dagger import Secret, dag, field, function, object_type

from dagger_intro.git_integration import clone_repo, create_pull_request, fetch_issue


@object_type
class DaggerIntro:
    ###
    ### Intro
    ###
    @function
    async def container_echo(self, string_arg: str) -> str:
        """Returns a container that echoes whatever string argument is provided"""
        return await (
            dag.container()
            .from_("alpine:latest")
            .with_exec(["echo", string_arg])
            .stdout()
        )

    @function
    async def grep_dir(self, directory_arg: dagger.Directory, pattern: str) -> str:
        """Returns lines that match a pattern in the files of the provided Directory"""
        return await (
            dag.container()
            .from_("alpine:latest")
            .with_mounted_directory("/mnt", directory_arg)
            .with_workdir("/mnt")
            .with_exec(["grep", "-R", pattern, "."])
            .stdout()
        )

    ###
    ### Publish container to registry
    ###
    @function
    async def publish(self) -> str:
        return await (
            dag.container()
            .from_("alpine:latest")
            .with_new_file("/hi.txt", "Hello from Patrick, Dagger!")
            .with_entrypoint(["cat", "/hi.txt"])
            .publish("ttl.sh/nlm")
        )

    ###
    ### Chain objects
    ###
    @function
    def basics(self) -> "Basics":
        """Access the Basics category of tools"""
        return Basics()

    @function
    def agentic(
        self,
        gh_token: Secret,
        agent_key: Secret,
        max_iterations: int = 3,
        llm_model: str = "google/gemini-3.1-flash-lite",
        agent_name: str = "GEMINI_API_KEY",
    ) -> "Agentic":
        """Access the Agentic functions"""
        return Agentic(
            gh_token=gh_token,
            agent_key=agent_key,
            agent_name=agent_name,
            llm_model=llm_model,
            max_iterations=max_iterations,
        )


@object_type
class Basics:
    ###
    ### Chained functions - Publish container to registry
    ### Publishes a container with bash, git
    ###
    @function
    def base(self) -> dagger.Container:
        """Returns a base container"""
        return dag.container().from_("cgr.dev/chainguard/wolfi-base")

    @function
    def build(self) -> dagger.Container:
        """Builds on top of base container and returns a new container"""
        return self.base().with_exec(["apk", "add", "bash", "git"])

    @function
    async def build_and_publish(self) -> str:
        """Builds and publishes a container"""
        return await self.build().publish("ttl.sh/bar")

    ###
    ### Cache layers, volumes, etc
    ###
    @function
    def env(self) -> dagger.Container:
        apt_cache = dag.cache_volume("apt-cache")
        return (
            dag.container()
            .from_("debian:latest")
            .with_mounted_cache("/var/cache/apt/archives", apt_cache)
            .with_exec(["apt-get", "update"])
            .with_exec(["apt-get", "install", "--yes", "maven", "mariadb-server"])
        )


@object_type
class Agentic:
    gh_token: Secret  # required
    agent_key: Secret  # required

    agent_name: str = field(default="GEMINI_API_KEY")  # optional
    llm_model: str = field(default="google/gemini-3.1-flash-lite")  # optional
    max_iterations: int = field(default=3)  # optional

    @function
    async def execute(self, repo: str, issue_number: int) -> str:
        workspace_container = self.setup_container_with_repository(repo)

        issue_body = await fetch_issue(repo, issue_number, self.gh_token)

        # 3. Multi-Agent Execution Loop
        turn = 0
        stage = "design"
        review_feedback = ""

        # Loop continues until completed OR until the max allowed feedback loops occur
        while stage != "done" and turn < self.max_iterations:
            if stage == "design":
                prompt = (
                    f"Agent 1 (Design): Create a technical design to solve issue #{issue_number}.\n\n"
                    f"Issue Description:\n{issue_body}\n\n"
                )
                if review_feedback:
                    prompt += f"Previous Review Feedback (Address these issues):\n{review_feedback}\n\n"
                prompt += "Instructions: Output your design and save it to /app/DESIGN.md. Do not modify any source code."

                workspace_container = workspace_container.with_exec(
                    ["pi", "--model", self.llm_model, "-p", prompt]
                )
                stage = "ac"

            elif stage == "ac":
                prompt = "Agent 2 (AC Tasks): Read /app/DESIGN.md. Based on the design, create Acceptance Criteria (AC) tasks.\n\n"
                if review_feedback:
                    prompt += f"Previous Review Feedback (Address these issues):\n{review_feedback}\n\n"
                prompt += "Instructions: Output your AC tasks and save them to /app/AC.md. Do not modify any source code."

                workspace_container = workspace_container.with_exec(
                    ["pi", "--model", self.llm_model, "-p", prompt]
                )
                stage = "implement"

            elif stage == "implement":
                prompt = (
                    f"Agent 3 (Implementation): Fix issue #{issue_number} in the provided workspace.\n\n"
                    "Read /app/DESIGN.md and /app/AC.md.\n"
                )
                if review_feedback:
                    prompt += f"Previous Review Feedback (Address these issues):\n{review_feedback}\n\n"
                prompt += "Instructions: Modify the necessary source code files in /app to fulfill the AC tasks and resolve the issue."

                workspace_container = workspace_container.with_exec(
                    ["pi", "--model", self.llm_model, "-p", prompt]
                )
                stage = "review"

            elif stage == "review":
                prompt = (
                    "Agent 4 (Review): Review the implemented changes in the workspace against the issue description, "
                    "/app/DESIGN.md, and /app/AC.md.\n"
                    "Evaluate the implementation and categorize your feedback. "
                    "You MUST include EXACTLY ONE of the following routing tokens anywhere in your response:\n"
                    "- NOT_SOLVED: The implementation completely fails to solve the issue. Needs a new design.\n"
                    "- MISSED_AC: The design is fine, but the implementation missed some Acceptance Criteria tasks.\n"
                    "- CRITICAL: ACs are addressed, but there are critical bugs or necessary changes.\n"
                    "- MINOR: The implementation passes with minor/acceptable issues.\n"
                    "- OK: The implementation is perfect."
                )

                # Execute the review step and capture standard output natively in Python
                review_exec = workspace_container.with_exec(
                    ["pi", "--model", self.llm_model, "-p", prompt]
                )
                workspace_container = review_exec  # Persist container state

                # Fetch output string to determine routing
                review_output = await review_exec.stdout()
                review_feedback = (
                    review_output  # Store feedback for the next agent prompt
                )

                # Flow control logic (Backward jumps count as 1 turn)
                if "NOT_SOLVED" in review_output:
                    stage = "design"
                    turn += 1
                elif "MISSED_AC" in review_output:
                    stage = "ac"
                    turn += 1
                elif "CRITICAL" in review_output:
                    stage = "implement"
                    turn += 1
                elif "MINOR" in review_output or "OK" in review_output:
                    stage = "done"
                else:
                    # Fallback in case the LLM doesn't output a valid token properly
                    stage = "done"

        try:
            design_content = await workspace_container.file("/app/DESIGN.md").contents()
        except Exception:
            design_content = "*(Design document not found or could not be generated)*"

        try:
            ac_content = await workspace_container.file("/app/AC.md").contents()
        except Exception:
            ac_content = (
                "*(Acceptance Criteria document not found or could not be generated)*"
            )

        # Cleanup intermediate AI agent documents so they don't pollute the PR commits
        workspace_container = workspace_container.with_exec(
            ["rm", "-f", "DESIGN.md", "AC.md"]
        )

        # Retrieve the final state of the output directory
        modified_source = workspace_container.directory("/app")

        # 4. PR Creation
        pr_url = await create_pull_request(
            agent_type="dagger_agent",
            modified_source=modified_source,
            issue_number=issue_number,
            gh_token=self.gh_token,
            repo=repo,
            design_content=design_content,
            ac_content=ac_content,
        )

        return pr_url

    def setup_container_with_repository(self, repo):

        # 1. Setup
        source = clone_repo(self.gh_token, repo)

        # 2. Configure the Workspace Environment and Install Pi
        return (
            dag.container()
            .from_("python:3.12-slim")
            # Install system dependencies
            .with_exec(["apt-get", "update"])
            .with_exec(
                ["apt-get", "install", "-y", "curl", "git", "ca-certificates", "gnupg"]
            )
            # Install Node.js 22.x (Required by Pi CLI in headless/non-interactive mode)
            .with_exec(
                [
                    "sh",
                    "-c",
                    "curl -fsSL https://deb.nodesource.com/setup_22.x | bash -",
                ]
            )
            .with_exec(["apt-get", "install", "-y", "nodejs"])
            # Install the official pi-coding-agent CLI
            .with_exec(["sh", "-c", "curl -fsSL https://pi.dev/install.sh | sh"])
            # Provider-specific auth env var expected by the selected model.
            .with_secret_variable(self.agent_name, self.agent_key)
            # Setup workdir
            .with_directory("/app", source)
            .with_workdir("/app")
        )
