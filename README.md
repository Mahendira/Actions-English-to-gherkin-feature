# English to Gherkin

Convert a text requirement into three independently generated and validated
`.feature` candidates using OpenAI, Gemini, and OpenRouter. Run it locally or
manually from GitHub Actions, and write the results to the same repository or a
different repository.

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

### 2. Configure the three LLM providers

In **Settings → Secrets and variables → Actions**, add:

| Type | Name | Example |
|---|---|---|
| Secret | `OPENAI_API_KEY` | OpenAI Platform API key; existing `LLM_API_KEY` is also accepted |
| Secret | `GEMINI_API_KEY` | Google Gemini API key |
| Secret | `OPENROUTER_API_KEY` | OpenRouter API key |
| Variable | `OPENAI_MODEL` | OpenAI model enabled for your project |
| Variable | `GEMINI_MODEL` | Gemini model enabled for your project |
| Variable | `OPENROUTER_MODEL` | OpenRouter model enabled for your account |
| Variable | `REVIEWER_MODEL` | Optional free reviewer model; defaults to `qwen/qwen3.8-27b:free` |

The workflow owns the three provider endpoints, so API URLs are not stored as
repository variables. Provider model availability and free-tier limits change;
use model IDs currently enabled in each account.

### 3. Allow workflow pull requests

For same-repository output, enable the repository setting that permits GitHub Actions to create and approve pull requests. The workflow uses the built-in `GITHUB_TOKEN`.

For a different output repository, use a GitHub App. This allows repository
owners to install the App on selected repositories without sharing personal
access tokens.

### 4. Create and configure the GitHub App

Under your GitHub account, open **Settings → Developer settings → GitHub Apps →
New GitHub App** and configure:

- GitHub App name: a globally unique name such as `Semsel Feature Generator`.
- Homepage URL: your project or company URL.
- Webhook: clear **Active** because this workflow does not receive webhooks.
- Repository permissions:
  - **Contents:** Read and write.
  - **Pull requests:** Read and write.
  - **Metadata:** Read-only (automatically included).
- Installation scope: select **Any account** if unrelated GitHub users should
  be able to install it. Use **Only on this account** for a private POC.

After creating the App:

1. Copy its **App ID**.
2. Under **Private keys**, select **Generate a private key** and download the
   `.pem` file.
3. Select **Install App**, choose an account or organization, and grant either
   all repositories or only the repositories that may receive generated files.
4. In the generator repository, open **Settings → Secrets and variables →
   Actions**.
5. Add repository variable `GH_APP_ID` containing the App ID.
6. Add repository secret `GH_APP_PRIVATE_KEY` containing the complete contents
   of the downloaded `.pem` file, including the BEGIN and END lines.

The workflow uses `actions/create-github-app-token` to mint a short-lived token
for only the selected target repository. Do not put the private key or a token
into a repository URL, source file, or workflow input.

For a target owned by another user or organization, that owner must install the
App and authorize the target repository before the workflow can access it.

## Run from GitHub Actions

Place a UTF-8 text requirement in the target repository, either at its root or
in a subdirectory. For example:

```text
search-api.txt
```

Then open **Actions → Generate Gherkin feature → Run workflow** and enter:

- `requirement_file`: repository-relative path such as `search-api.txt` or
  `requirements/search-api.txt`.
- `output_repo`: blank for the current repo; otherwise `owner/repo` or its GitHub URL.
- `output_directory`: defaults to `features`.
- `base_branch`: blank uses the target repository's default branch.
- `overwrite`: replaces an existing same-named feature only when enabled.
- `create_pull_request`: recommended and enabled by default.

The workflow validates the target and requirement path, creates a short-lived
GitHub App installation token when needed, and generates three files:

```text
features/search-api-openai.feature
features/search-api-gemini.feature
features/search-api-openrouter.feature
features/search-api.feature
```

Each candidate is structurally validated before anything is committed. The
free independent reviewer compares the original requirement with all three
candidates and writes the unsuffixed `search-api.feature` master file. Invalid
reviewer output is automatically repaired up to three times. The workflow is
all-or-nothing: if a provider or reviewer fails, nothing is pushed. It commits
the output directory and opens one pull request. When the target is the
generator repository itself, it uses the built-in `GITHUB_TOKEN`.

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
- Cross-repository access must be granted explicitly by installing the GitHub
  App on the target repository.
- GitHub App installation tokens are short-lived and scoped to the selected
  target repository.
- Generated content is submitted through a pull request by default.
- Treat requirement text sent to an external provider according to your organization's data policy.
