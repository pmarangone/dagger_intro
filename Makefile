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

execute:
	@set -a; \
	[ ! -f .env ] || . ./.env; \
	set +a; \
	dagger call \
		agentic \
		--gh-token env://GH_TOKEN \
		--agent-key env://GEMINI_API_KEY \
		--max-iterations 20 \
		execute \
		--repo pmarangone/sentiment-analysis \
		--issue-number 5