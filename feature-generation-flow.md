# Feature generation flow

```mermaid
flowchart TD
    A["Run Generate Gherkin workflow"] --> B["Enter requirement and target owner/repo"]
    B --> C{"Same repository?"}

    C -->|Yes| D["Use built-in GITHUB_TOKEN"]
    C -->|No| E["Verify GitHub App installation"]
    E --> F["Create short-lived installation token"]

    D --> G["Clone target repository"]
    F --> G
    G --> H["Call OpenAI using LLM_API_KEY secret"]
    H --> I["Generate and validate Gherkin"]
    I --> J["Create features/name.feature"]
    J --> K["Push ai-feature branch"]
    K --> L["Open pull request in target repository"]
```

## Required credentials

| Purpose | Configuration |
|---|---|
| OpenAI authentication | Repository secret `LLM_API_KEY` |
| Same-repository GitHub access | Built-in `GITHUB_TOKEN` |
| Cross-repository GitHub access | GitHub App variable `GH_APP_ID` and secret `GH_APP_PRIVATE_KEY` |

The target repository must already exist. For cross-repository generation, its
owner must install the GitHub App and authorize the target repository.
