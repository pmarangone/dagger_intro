import dagger
from dagger import dag, function, object_type


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
    ### Cache layers, volumes
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
