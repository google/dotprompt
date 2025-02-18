# Git Workflow

This project follows a rebase-based workflow to maintain a clean, linear history in the main branch. This approach makes the project history easier to follow and understand.

## Core Principles

1. The `main` branch maintains a linear history
2. Feature branches are rebased on top of `main` before merging
3. Commits are squashed when appropriate to maintain atomic changes
4. Force-pushing to `main` is strictly prohibited

## Workflow Steps

### 1. Starting New Work

```bash
# Ensure you're on main and up-to-date
git checkout main
git pull origin main

# Create a new feature branch
git checkout -b ${USER}/feat/your-feature-name
```

### 2. Making Changes

```bash
# Make your changes and commit them
git add .
git commit -m "feat: your descriptive commit message"

# Make more commits as needed during development
```

### 3. Keeping Your Branch Updated

```bash
# Fetch latest changes from main
git fetch origin main

# Rebase your branch on top of main
git rebase --update-refs origin/main

# If there are conflicts, resolve them and continue
git add .
git rebase --continue

# Force push your branch (only if you've already pushed it before)
git push origin HEAD -f
```

### 4. Preparing for Pull Request

```bash
# Squash commits if needed to maintain atomic changes
git rebase -i origin/main

# Force push your changes
git push origin HEAD -f
```

### 5. Merging to Main

Once your pull request is approved:

```bash
# Ensure your branch is up-to-date with main
git checkout ${USER}/feat/your-feature-name
git fetch origin main
git rebase --update-refs origin/main

# If using GitHub UI:
# Select "Rebase and merge" option in the PR

# If merging locally:
git checkout main
git merge --ff-only ${USER}/feat/your-feature-name
git push origin main
```

## Best Practices

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code changes that neither fix bugs nor add features
- `test`: Adding or modifying tests
- `chore`: Maintenance tasks

### Rebasing Guidelines

1. **Always** rebase feature branches onto `main` before merging
2. Use interactive rebase (`git rebase -i`) to clean up commits before merging
3. Ensure each commit represents a complete, atomic change
4. Write clear commit messages that explain the "why" not just the "what"

### Force Push Safety

1. Always use `--force-with-lease` instead of `--force`
2. Never force push to `main` or shared integration branches
3. Only force push to your own feature branches

### Handling Conflicts

When resolving conflicts during rebase:

1. Understand both changes before resolving
2. Maintain project coding standards
3. Test thoroughly after resolution
4. If unsure, consult with team members

## Common Issues and Solutions

### Recovering from Mistakes

If you made a mistake during rebase:

```bash
# Abort a rebase in progress
git rebase --abort

# Reset to before the rebase
git reset --hard ORIG_HEAD
```

### Checking Branch Status

```bash
# View branch status relative to main
git log --graph --oneline main..HEAD

# Check if branch needs rebase
git fetch origin main
git log --oneline main..HEAD
```

## Additional Resources

- [Pro Git Book - Rebasing](https://git-scm.com/book/en/v2/Git-Branching-Rebasing)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Force Push with Lease](https://git-scm.com/docs/git-push#Documentation/git-push.txt---force-with-leaseltrefnamegt)
