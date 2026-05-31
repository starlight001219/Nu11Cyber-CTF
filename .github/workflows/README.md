# GitHub Actions Workflows

This directory contains automated CI/CD workflows for Nu11Cyber-CTF.

## Workflows

### 1. CI (`ci.yml`)
**Trigger**: Push to `main`/`develop`, Pull Requests to `main`

- ✅ Python syntax checking
- ✅ Code linting with flake8
- ✅ Docker Compose validation
- ✅ Docker image build test

### 2. Docker Publish (`docker-publish.yml`)
**Trigger**: Push version tags (`v*`), Manual dispatch

- 🐳 Builds backend Docker image
- 📦 Pushes to GitHub Container Registry (ghcr.io)
- 🏷️ Tags: `latest`, `v1.0.0`, `1.0`

**Usage**:
```bash
git tag v1.0.0
git push origin v1.0.0
```

### 3. Deploy (`deploy.yml`)
**Trigger**: Manual dispatch, GitHub Release published

- 🚀 Deploys to production server via SSH
- 🔄 Pulls latest code, rebuilds containers
- 📊 Runs database migrations (if any)

## Setup Required

### For Docker Publish
1. Go to **Settings** → **Actions** → **General**
2. Set **Workflow permissions** to "Read and write permissions"
3. Images will be published to: `ghcr.io/starlight001219/Nu11Cyber-CTF-backend`

### For Auto-Deploy
Add these secrets in **Settings** → **Secrets and variables** → **Actions**:

| Secret | Description |
|--------|-------------|
| `DEPLOY_HOST` | Server IP or hostname |
| `DEPLOY_USER` | SSH username |
| `DEPLOY_SSH_KEY` | SSH private key |
| `DEPLOY_PORT` | SSH port (default: 22) |

## Manual Deployment

You can also trigger deployment manually:
1. Go to **Actions** tab
2. Select **Deploy** workflow
3. Click **Run workflow**
4. Select `main` branch
5. Click **Run workflow** button
