echo:
	dagger call container-echo --string-arg "Hello world"

publish:
	dagger call publish

view_published:
	docker run ttl.sh/nlm

publish_chained:
	dagger call publish-chained

help:
	dagger call --help

basics_help:
	dagger call basics --help
	
basics_build:
	dagger call basics build