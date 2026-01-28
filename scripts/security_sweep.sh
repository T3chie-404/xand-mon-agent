#!/bin/bash
# AGGRESSIVE security scan for PUBLIC repository
# This script blocks commits containing sensitive data

set -e

echo "🔒 Running security sweep for PUBLIC repository..."
echo ""

# Patterns to search for (case insensitive where appropriate)
declare -A PATTERNS=(
    ["api-key="]="API key in URL"
    ["password"]="Password reference"
    ["secret"]="Secret reference"  
    ["BEGIN.*PRIVATE KEY"]="SSH private key"
    ["id_ed25519"]="SSH key file"
    ["id_rsa"]="SSH key file"
    ["\.pem"]="PEM file"
    ["148\.72\."]="Internal IP address"
    ["10\.252\."]="Internal network"
    ["192\.168\."]="Private network"
    ["solval"]="Internal username"
    ["xand-rpc-MB-velia"]="Internal hostname"
    ["d8f4ee9c"]="Helius API key"
    ["jwt.*=.*[a-f0-9]{32}"]="JWT secret"
)

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "⚠️  Not in a git repository, skipping security sweep"
    exit 0
fi

# Check staged files
STAGED_FILES=$(git diff --cached --name-only)

if [ -z "$STAGED_FILES" ]; then
    echo "ℹ️  No staged files to check"
    exit 0
fi

echo "Checking staged files for sensitive data..."
echo ""

FOUND_SENSITIVE=0

for pattern_key in "${!PATTERNS[@]}"; do
    pattern_desc="${PATTERNS[$pattern_key]}"
    
    # Search in staged files
    if git diff --cached | grep -iE "$pattern_key" > /dev/null 2>&1; then
        echo "❌ FOUND: $pattern_desc"
        echo "   Pattern: $pattern_key"
        
        # Show matches (limited)
        git diff --cached | grep -iE "$pattern_key" | head -3 | sed 's/^/   > /'
        echo ""
        
        FOUND_SENSITIVE=1
    fi
done

# Check for actual .env files (not .env.example)
if echo "$STAGED_FILES" | grep -E "^\.env$|/\.env$" > /dev/null 2>&1; then
    echo "❌ FOUND: Actual .env file"
    echo "   Only .env.example or env.example should be committed!"
    echo ""
    FOUND_SENSITIVE=1
fi

# Check for common sensitive file patterns
SENSITIVE_FILES=(
    "*.key"
    "*.pem"
    "id_*"
    "*.local"
)

for file_pattern in "${SENSITIVE_FILES[@]}"; do
    if echo "$STAGED_FILES" | grep -E "$file_pattern" > /dev/null 2>&1; then
        echo "❌ FOUND: Sensitive file pattern: $file_pattern"
        echo ""
        FOUND_SENSITIVE=1
    fi
done

# Final verdict
echo "===================================="
if [ $FOUND_SENSITIVE -eq 1 ]; then
    echo "❌ COMMIT BLOCKED: Sensitive data detected in PUBLIC repository"
    echo ""
    echo "This repository is PUBLIC on GitHub!"
    echo "Please review and remove sensitive information before committing."
    echo ""
    echo "If this is a false positive, you can bypass with:"
    echo "  git commit --no-verify"
    echo ""
    exit 1
else
    echo "✅ Security sweep passed - no sensitive data detected"
    echo ""
    exit 0
fi
