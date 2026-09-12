hi

## In another project

> dagger init --blueprint=github.com/kpenfound/blueprints/python-uv-ruff
> dagger call --help # Get all info about the toolchain
> dagger functions
> dagger call lint --help
> dagger call --source . lint # Change the default source variable inside the base class of the toolchain

## Agentic execution

`gh-token` and `agent-key` are Dagger `Secret` arguments. Pass secret URIs that
point to environment variables containing the secret values, not the raw token
values. Use `agent-name` for the provider-specific env var name expected by the
selected model:

```sh
export GH_TOKEN=...
export GEMINI_API_KEY=...

dagger call \
	agentic \
	--gh-token env://GH_TOKEN \
	--agent-key env://GEMINI_API_KEY \
	--agent-name GEMINI_API_KEY \
	--llm-model google/gemini-3.1-flash-lite \
	--max-iterations 20 \
	execute \
	--repo pmarangone/sentiment-analysis \
	--issue-number 5
```

For another provider, change the secret env var name and model together:

```sh
export OPENAI_API_KEY=...

dagger call \
	agentic \
	--gh-token env://GH_TOKEN \
	--agent-key env://OPENAI_API_KEY \
	--agent-name OPENAI_API_KEY \
	--llm-model openai/gpt-5 \
	execute \
	--repo pmarangone/sentiment-analysis \
	--issue-number 5
```
