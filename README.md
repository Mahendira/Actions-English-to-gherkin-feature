# English to Gherkin

Convert English software requirements into validated `.feature` files without coupling the project to one LLM vendor. Run it locally or manually from GitHub Actions, and write the result to the same repository or a different repository.

## Design goals

- Provider-neutral core using a small `LlmProvider` interface.
- Supports OpenAI-compatible APIs (OpenAI, OpenRouter, Groq, compatible gateways) and Gemini.
- Fails clearly when the provider fails; it does not hide failures with fake fallback features.
- Cleans and validates generated Gherkin before writing it.
- Keeps Git operations in GitHub Actions, outside the Python generator.
- Creates a pull request by default instead of writing directly to `main`.
- Scopes commits to the configured output directory.

## Repository structure

```text
.
├── .github/workflows/
│   ├── generate-feature.yml
│   └── test.yml
├── examples/search-api.txt
├── src/english_to_gherkin/
│   ├── providers/
│   ├── cli.py
│   ├── config.py
│   ├── generator.py
│   ├── gherkin.py
│   └── prompts.py
├── tests/
├── .env.example
└── pyproject.toml
```

## GitHub setup

### 1. Create the repository

Upload this project to a new GitHub repository. GitHub Actions must be enabled.

### 2. Configure the LLM

In **Settings → Secrets and variables → Actions**, add:

| Type | Name | Example |
|---|---|---|
| Secret | `LLM_API_KEY` | Provider API key |
| Variable | `LLM_PROVIDER` | `openai_compatible` or `gemini` |
| Variable | `LLM_API_URL` | Provider endpoint shown below |
| Variable | `LLM_MODEL` | Provider model ID |

Example configurations:

| Provider | `LLM_PROVIDER` | `LLM_API_URL` | Model example |
|---|---|---|---|
| OpenRouter | `openai_compatible` | `https://openrouter.ai/api/v1/chat/completions` | A model available to your account |
| OpenAI | `openai_compatible` | `https://api.openai.com/v1/chat/completions` | A chat-completions model |
| Groq | `openai_compatible` | `https://api.groq.com/openai/v1/chat/completions` | A model available to your account |
| Gemini | `gemini` | `https://generativelanguage.googleapis.com/v1beta` | A Gemini model available to your account |

Provider model availability and free-tier limits change. Use a model currently enabled in your provider account.

### 3. Allow workflow pull requests

For same-repository output, enable the repository setting that permits GitHub Actions to create and approve pull requests. The workflow uses the built-in `GITHUB_TOKEN`.

For a different output repository, add this secret to the generator repository:

| Secret | Purpose |
|---|---|
| `CROSS_REPO_TOKEN` | Fine-grained token with contents write and pull-request write access to the target repository |

Do not put a token into the repository URL or workflow inputs.

## Run from GitHub Actions

Open **Actions → Generate Gherkin feature → Run workflow** and enter:

- `requirement_name`: short filename/title such as `search-api`.
- `requirement_text`: the English requirement.
- `output_repo`: blank for the current repo; otherwise `owner/repo` or its GitHub URL.
- `output_directory`: defaults to `features`.
- `base_branch`: blank uses the target repository's default branch.
- `overwrite`: replaces an existing same-named feature only when enabled.
- `create_pull_request`: recommended and enabled by default.

The workflow validates access, clones the target repository, generates the feature, validates it, commits only the output directory, and opens a pull request.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Export the values shown in `.env.example`, then run:

```bash
english-to-gherkin \
  --requirement-name search-api \
  --requirement-file examples/search-api.txt \
  --output-dir features
```

Or pass the requirement directly:

```bash
english-to-gherkin \
  --requirement-name hello-api \
  --requirement-text "Create a GET endpoint that returns Hello World with HTTP 200" \
  --output-dir features
```

The CLI refuses to overwrite an existing file unless `--overwrite` is supplied.

## Add another LLM provider

1. Implement `LlmProvider.generate()` under `src/english_to_gherkin/providers/`.
2. Register it in `providers/factory.py`.
3. Add response-parsing and failure tests.

The prompt, validation, output, workflow, and Git handling do not need to change.

## Validation boundary

The built-in validator checks structure: one feature, one or more scenarios, and Given/When/Then in each scenario. It intentionally does not claim full Cucumber-parser equivalence. In an application repository, the pull request should also run that application's Cucumber test stack before merge.

## Security notes

- Secrets are provided only to the generation/authentication steps that need them.
- Repository tokens are never embedded in clone URLs.
- Cross-repository access must be granted explicitly.
- Generated content is submitted through a pull request by default.
- Treat requirement text sent to an external provider according to your organization's data policy.
