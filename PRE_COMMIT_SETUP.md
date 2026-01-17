# Pre-commit Hook Setup

This repository uses pre-commit hooks to automatically lint and format code before commits.

## What Gets Checked

### Python Projects
- Code formatting (black, ruff-format)
- Linting issues (ruff)
- Import sorting (isort via ruff)

### Frontend (TypeScript/React)
- ESLint (with TypeScript support)
- Prettier formatting

### All Files
- Trailing whitespace
- End-of-file fixers
- Large file detection
- Merge conflicts
- Debug statements

## Initial Setup

### 1. Install pre-commit

```bash
pip install pre-commit
```

Or with homebrew:
```bash
brew install pre-commit
```

### 2. Unset Husky (if migrating)

If you previously had Husky installed:
```bash
git config --unset-all core.hooksPath
```

### 3. Install the git hooks

From the repository root:
```bash
pre-commit install
```

That's it. The hooks will now run automatically on every commit.

## Usage

### Normal Commits

When you commit, pre-commit will automatically run:
```bash
git commit -m "your message"
```

If hooks fail:
- Most issues are auto-fixed (formatting, trailing whitespace, etc.)
- Review the changes: `git diff`
- Stage the fixes: `git add .`
- Commit again: `git commit -m "your message"`

### Skipping Hooks (Not Recommended)

Only when absolutely necessary:
```bash
git commit -m "your message" --no-verify
```

### Manual Run

Test hooks on all files without committing:
```bash
pre-commit run --all-files
```

Run on specific files:
```bash
pre-commit run --files path/to/file.py
```

## Project-Specific Configuration

### Python Projects
Each project has its own ruff configuration in `pyproject.toml`:
- `projects/web-backend/pyproject.toml` - Django project (Python 3.10+)
- `projects/mission-planner/pyproject.toml` - Flask project (Python 3.9+)
- `projects/integration-tests/pyproject.toml` - Test suite (Python 3.10+)

Ruff will automatically use the appropriate config based on file location.

### Frontend Project
ESLint and Prettier use the existing configuration in:
- `projects/web-frontend/.eslintrc.cjs` or eslint config in `package.json`
- `projects/web-frontend/.prettierrc` or prettier config in `package.json`

## Cleaning Up Husky (Optional)

After migrating to pre-commit, you can optionally remove Husky:

1. Remove the prepare script from `projects/web-frontend/package.json`:
   ```diff
   - "prepare": "cd ../.. && husky install projects/web-frontend/.husky",
   ```

2. Uninstall Husky and lint-staged:
   ```bash
   cd projects/web-frontend
   npm uninstall husky lint-staged
   ```

3. Remove the `.husky` directory:
   ```bash
   rm -rf projects/web-frontend/.husky
   ```

4. Remove lint-staged config from `package.json` (the `lint-staged` section)

## Troubleshooting

### Hooks not running
```bash
pre-commit install
```

### Update hooks to latest versions
```bash
pre-commit autoupdate
```

### Clear cache and retry
```bash
pre-commit clean
pre-commit run --all-files
```
