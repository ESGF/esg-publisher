#!/bin/bash
# Release script for esgcet
# Usage: ./scripts/release.sh [version]
# Example: ./scripts/release.sh 5.5.2

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
info() { echo -e "${BLUE}ℹ${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
warning() { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; exit 1; }

# Check if version is provided
if [ -z "$1" ]; then
    CURRENT_VERSION=$(grep -m1 'version = ' pyproject.toml | cut -d'"' -f2)
    info "Current version: $CURRENT_VERSION"
    read -p "Enter version to release (e.g., 5.5.2): " VERSION
else
    VERSION=$1
fi

# Remove 'v' prefix if present
VERSION=${VERSION#v}

info "Starting release process for version $VERSION"
echo

# Step 1: Verify we're on integration branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "integration" ]; then
    warning "Not on integration branch (currently on $CURRENT_BRANCH)"
    read -p "Continue anyway? (y/N): " CONTINUE
    if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
        error "Aborted. Switch to integration branch first."
    fi
fi
success "On branch: $CURRENT_BRANCH"

# Step 2: Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    error "Uncommitted changes detected. Commit or stash them first."
fi
success "Working directory clean"

# Step 3: Verify version in pyproject.toml matches
PYPROJECT_VERSION=$(grep -m1 'version = ' pyproject.toml | cut -d'"' -f2)
if [ "$PYPROJECT_VERSION" != "$VERSION" ]; then
    warning "pyproject.toml has version $PYPROJECT_VERSION, but releasing $VERSION"
    read -p "Update pyproject.toml to $VERSION? (y/N): " UPDATE
    if [[ "$UPDATE" =~ ^[Yy]$ ]]; then
        sed -i.bak "s/version = \".*\"/version = \"$VERSION\"/" pyproject.toml
        rm pyproject.toml.bak
        git add pyproject.toml
        git commit -m "Bump version to $VERSION"
        success "Updated pyproject.toml to version $VERSION"
    else
        error "Aborted. Fix version mismatch first."
    fi
else
    success "Version matches: $VERSION"
fi

# Step 4: Run tests
info "Running test suite..."
if python -m pytest tests/ -q --tb=line; then
    success "All tests passed"
else
    error "Tests failed. Fix tests before releasing."
fi

# Step 5: Checkout main and merge integration
info "Merging integration into main..."
git checkout main
git pull origin main

if git merge integration --no-edit; then
    success "Merged integration into main"
else
    error "Merge conflict detected. Resolve manually and re-run."
fi

# Step 6: Test again on main
info "Running tests on main after merge..."
if python -m pytest tests/ -q --tb=line; then
    success "Tests passed on main"
else
    error "Tests failed on main. Fix before continuing."
fi

# Step 7: Extract release notes from whatsnew.rst
info "Extracting release notes..."
RELEASE_NOTES_FILE="RELEASE_NOTES_${VERSION}.md"

# Create release notes (simplified - just get the version section)
cat > "$RELEASE_NOTES_FILE" << EOF
# Release v${VERSION}

See [What's New](https://esg-publisher.readthedocs.io/en/latest/whatsnew.html#v${VERSION//./-}) for complete release notes.

## Installation

\`\`\`bash
pip install esgcet==${VERSION}
# or
conda install -c conda-forge esgcet=${VERSION}
\`\`\`

## Highlights

EOF

# Extract highlights from whatsnew.rst (first few bullet points)
awk '/^v'${VERSION//./\\.}'$/,/^v[0-9]/ {
    if (/^\* \*\*/) {
        print "- " substr($0, 3);
        count++;
        if (count >= 5) exit;
    }
}' docs/whatsnew.rst >> "$RELEASE_NOTES_FILE"

success "Release notes saved to $RELEASE_NOTES_FILE"
cat "$RELEASE_NOTES_FILE"
echo

# Step 8: Confirm before pushing
warning "Ready to release v${VERSION}. This will:"
echo "  1. Push main to origin"
echo "  2. Create and push tag v${VERSION}"
echo "  3. Trigger PyPI publishing"
echo "  4. Create GitHub Release"
echo
read -p "Proceed with release? (yes/N): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    warning "Aborted. To continue manually:"
    echo "  git push origin main"
    echo "  git tag -a v${VERSION} -F $RELEASE_NOTES_FILE"
    echo "  git push origin v${VERSION}"
    exit 0
fi

# Step 9: Push main
info "Pushing main to origin..."
git push origin main
success "Pushed main"

# Step 10: Create annotated tag
info "Creating tag v${VERSION}..."
git tag -a "v${VERSION}" -F "$RELEASE_NOTES_FILE"
success "Created tag v${VERSION}"

# Step 11: Push tag (triggers GitHub Actions for PyPI and Release)
info "Pushing tag v${VERSION}..."
git push origin "v${VERSION}"
success "Pushed tag v${VERSION}"

echo
success "🎉 Release v${VERSION} initiated!"
echo
info "Next steps:"
echo "  1. Monitor GitHub Actions: https://github.com/ESGF/esg-publisher/actions"
echo "  2. Verify PyPI: https://pypi.org/project/esgcet/${VERSION}/"
echo "  3. Check GitHub Release: https://github.com/ESGF/esg-publisher/releases/tag/v${VERSION}"
echo "  4. Update conda-forge (see scripts/conda-forge-release.md)"
echo "  5. Announce release to community"
echo
warning "Recommended: Bump to next dev version on integration"
echo "  On integration: Update pyproject.toml to ${VERSION%.*}.$((${VERSION##*.}+1))-dev"
echo

# Cleanup
rm -f "$RELEASE_NOTES_FILE"
