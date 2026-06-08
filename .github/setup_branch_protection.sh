#!/bin/bash
# Скрипт для автоматичного налаштування Branch Protection у GitHub
# Запустити один раз після публікації репозиторію:
#   chmod +x .github/setup_branch_protection.sh
#   GITHUB_TOKEN=your_token REPO=owner/repo-name bash .github/setup_branch_protection.sh

REPO="${REPO:-Vitalik2234/project-2-refactoring}"
TOKEN="${GITHUB_TOKEN:-YOUR_TOKEN}"

echo "Налаштування Branch Protection для $REPO..."

curl -s -X PUT \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$REPO/branches/main/protection" \
  -d '{
    "required_status_checks": {
      "strict": true,
      "contexts": ["Tests & Coverage", "SonarCloud Analysis"]
    },
    "enforce_admins": false,
    "required_pull_request_reviews": {
      "dismiss_stale_reviews": true,
      "require_code_owner_reviews": false,
      "required_approving_review_count": 1
    },
    "restrictions": null,
    "allow_force_pushes": false,
    "allow_deletions": false
  }'

echo ""
echo "Branch Protection налаштовано для гілки main."
echo "PR не можна змерджити якщо:"
echo "  - Tests & Coverage провалено"
echo "  - SonarCloud Quality Gate провалено"
echo "  - Покриття < 70%"
