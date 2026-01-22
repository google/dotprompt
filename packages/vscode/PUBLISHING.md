# How to Publish `dotprompt-vscode`

This guide details the steps to publish the VS Code extension to the [Visual Studio Marketplace](https://marketplace.visualstudio.com/).

## Prerequisites

1.  **Publisher Account**: You must be a member of the `Google` publisher organization on the VS Code Marketplace.
2.  **Personal Access Token (PAT)**: You need a PAT from Azure DevOps with `Marketplace (manage)` scope.

## Manual Publishing

1.  **Login**:
    ```bash
    vsce login Google
    ```
    Enter your PAT when prompted.

2.  **Publish**:
    ```bash
    cd packages/vscode
    vsce publish
    ```
    Or from the root using `pnpm`:
    ```bash
    pnpm -C packages/vscode vsce publish
    ```

## Automated Publishing (Recommended)

This repository is configured to automatically publish releases via GitHub Actions.

### Setup

1.  **Secret**: proper `VSCE_PAT` secret must be set in the repository secrets.
2.  **Workflow**: Use the `.github/workflows/vscode_publish.yml` workflow.

### Trigger

The release workflow triggers when a GitHub Release is created (managed by Release Please).
