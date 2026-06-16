## In another project

> dagger init --blueprint=github.com/kpenfound/blueprints/python-uv-ruff
> dagger call --help # Get all info about the toolchain
> dagger functions
> dagger call lint --help
> dagger call --source . lint # Change the default source variable inside the base class of the toolchain

## Agentic execution

`gh-token` and `agent-key` are Dagger `Secret` arguments. Pass the names of
environment variables that contain the secret values, not the raw token values:

```sh
export GH_TOKEN=...
export GEMINI_API_KEY=...

dagger call \
	agentic \
	--gh-token env://GH_TOKEN \
	--agent-key env://GEMINI_API_KEY \
	--max-iterations 20 \
	execute \
	--repo pmarangone/sentiment-analysis \
	--issue-number 5
```
