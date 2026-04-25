#!/bin/bash
# cleanup.sh - Script to clean unwanted files from the FastAPI project

echo "🧹 Cleaning up FastAPI project..."

# Remove test/debug HTML files
rm -f test_user_creation.html debug_signup.html

# Remove Python cache files
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Remove coverage files
rm -f .coverage
rm -rf htmlcov/

# Remove pytest cache
rm -rf .pytest_cache/
rm -rf test_suite/.pytest_cache/

# Remove macOS system files
find . -name ".DS_Store" -delete 2>/dev/null || true

# Remove backup files
find . -name "*~" -delete 2>/dev/null || true
find . -name "*.bak" -delete 2>/dev/null || true

# Remove log files
find . -name "*.log" -delete 2>/dev/null || true

echo "✅ Cleanup complete!"
echo ""
echo "📁 Current project structure:"
ls -la | grep -E '^d|^-.*\.(py|toml|txt|md|yml|yaml|json|html|css|js)$'
