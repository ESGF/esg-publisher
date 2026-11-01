# Release Automation Plan for esg-publisher

## Current State

- ✅ Tests run on push to main/integration
- ✅ PyPI publish triggers on version tags (`v*`)
- ✅ GitHub Release created automatically on tag
- ❌ Manual version bumping in pyproject.toml
- ❌ Manual whatsnew.rst updates
- ❌ Manual PR creation (integration → main)
- ❌ Manual git tagging

## Common Release Automation Patterns

### 1. Release Please (Google's approach)
- **How it works**: Automatically creates "release PR" based on conventional commits
- **Used by**: Google, many open-source projects
- **Pros**: Fully automated, changelog generation, works with monorepos
- **Cons**: Requires conventional commit discipline
- **Example**: https://github.com/googleapis/release-please

### 2. semantic-release
- **How it works**: Fully automated versioning and publishing based on commit analysis
- **Pros**: Zero-config releases, plugin ecosystem
- **Cons**: Very opinionated, less control over timing
- **Example**: https://github.com/semantic-release/semantic-release

### 3. Manual + GitHub Actions (Recommended)
- **How it works**: Manual trigger with workflow_dispatch, specify version bump type
- **Pros**: Full control, explicit release decisions, easier to adopt incrementally
- **Cons**: Still requires one manual step (triggering the workflow)

## Recommended Approach: "Release PR" Workflow

### High-Level Flow

```
1. Development on integration branch
2. Ready to release → Run GitHub workflow: "Create Release PR"
   - Choose bump type: patch (5.5.1→5.5.2), minor (5.5.1→5.6.0), major (5.5.1→6.0.0)
   - Workflow auto-creates PR: integration → main
   - Version bumped in pyproject.toml
   - Whatsnew.rst template inserted
3. Review/edit the PR (add detailed release notes)
4. Merge PR → automatically triggers:
   - Create git tag (e.g., v5.5.2)
   - Push tag
   - PyPI publish (existing workflow)
   - GitHub Release creation (existing workflow)
```

### Visual Workflow

```
┌─────────────────┐
│ Work on         │
│ integration     │
│ branch          │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│ Trigger workflow manually:  │
│ "Create Release PR"         │
│ Input: patch/minor/major    │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ Auto-created PR:            │
│ integration → main          │
│ - Version bumped            │
│ - Whatsnew template added   │
│ - Label: "release"          │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────┐
│ Human review:   │
│ - Edit notes    │
│ - Verify tests  │
│ - Approve       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Merge PR        │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│ Auto-triggered actions:     │
│ 1. Create git tag v5.5.x    │
│ 2. Push tag to GitHub       │
│ 3. PyPI publish (existing)  │
│ 4. GitHub Release (existing)│
└─────────────────────────────┘
```

## Implementation Files Needed

### 1. `.bumpversion.cfg`

Configuration for the bump2version tool:

```ini
[bumpversion]
current_version = 5.5.1
commit = False
tag = False

[bumpversion:file:pyproject.toml]
search = version = "{current_version}"
replace = version = "{new_version}"
```

### 2. `.github/workflows/create-release-pr.yml`

Workflow to create the release PR:

```yaml
name: Create Release PR

on:
  workflow_dispatch:
    inputs:
      version-bump:
        description: 'Version bump type'
        required: true
        type: choice
        options:
          - patch  # 5.5.1 → 5.5.2
          - minor  # 5.5.1 → 5.6.0
          - major  # 5.5.1 → 6.0.0
      release-notes:
        description: 'Brief release notes (optional)'
        required: false

jobs:
  create-release-pr:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: integration
          
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          
      - name: Install bump2version
        run: pip install bump2version
        
      - name: Bump version
        run: |
          bump2version ${{ inputs.version-bump }} --allow-dirty
          NEW_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
          echo "NEW_VERSION=$NEW_VERSION" >> $GITHUB_ENV
          
      - name: Update whatsnew.rst
        run: |
          # Insert new version section at top of release notes
          sed -i "4i\\
          v${{ env.NEW_VERSION }}\\
          ------\\
          \\
          ${{ inputs.release-notes || '* TBD' }}\\
          \\
          " docs/whatsnew.rst
          
      - name: Create Pull Request
        uses: peter-evans/create-pull-request@v6
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          commit-message: "chore: release v${{ env.NEW_VERSION }}"
          branch: release-v${{ env.NEW_VERSION }}
          base: main
          title: "Release v${{ env.NEW_VERSION }}"
          body: |
            ## Release v${{ env.NEW_VERSION }}
            
            This PR prepares version ${{ env.NEW_VERSION }} for release.
            
            ### Changes
            - Bumped version in pyproject.toml: ${{ env.NEW_VERSION }}
            - Updated whatsnew.rst with release section
            
            ### Checklist before merging
            - [ ] Review and complete release notes in whatsnew.rst
            - [ ] Verify version number is correct
            - [ ] All tests passing
            - [ ] Documentation updated if needed
            
            **After merge**, this will automatically:
            - Create git tag v${{ env.NEW_VERSION }}
            - Publish to PyPI
            - Create GitHub Release with notes
          labels: release
```

### 3. `.github/workflows/tag-on-merge.yml`

Workflow to auto-tag when release PR is merged:

```yaml
name: Create Tag on Release Merge

on:
  pull_request:
    types: [closed]
    branches: [main]

jobs:
  tag-release:
    # Only run if PR was merged (not just closed) and has 'release' label
    if: |
      github.event.pull_request.merged == true &&
      contains(github.event.pull_request.labels.*.name, 'release')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: main
          fetch-depth: 0
          
      - name: Get version from pyproject.toml
        id: get-version
        run: |
          VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
          echo "version=$VERSION" >> $GITHUB_OUTPUT
          echo "Version to tag: v$VERSION"
          
      - name: Check if tag already exists
        id: check-tag
        run: |
          if git rev-parse "v${{ steps.get-version.outputs.version }}" >/dev/null 2>&1; then
            echo "exists=true" >> $GITHUB_OUTPUT
            echo "Tag v${{ steps.get-version.outputs.version }} already exists"
          else
            echo "exists=false" >> $GITHUB_OUTPUT
          fi
          
      - name: Create and push tag
        if: steps.check-tag.outputs.exists == 'false'
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git tag -a v${{ steps.get-version.outputs.version }} \
            -m "Release v${{ steps.get-version.outputs.version }}"
          git push origin v${{ steps.get-version.outputs.version }}
          
      - name: Tag already exists
        if: steps.check-tag.outputs.exists == 'true'
        run: |
          echo "::warning::Tag v${{ steps.get-version.outputs.version }} already exists, skipping tag creation"
```

## Usage Instructions

### For a New Release

1. **Navigate to GitHub Actions**
   - Go to: https://github.com/ESGF/esg-publisher/actions
   - Select "Create Release PR" workflow

2. **Trigger the workflow**
   - Click "Run workflow"
   - Select branch: `integration`
   - Choose version bump type:
     - `patch` for bug fixes (5.5.1 → 5.5.2)
     - `minor` for new features (5.5.1 → 5.6.0)
     - `major` for breaking changes (5.5.1 → 6.0.0)
   - Optionally add brief release notes
   - Click "Run workflow"

3. **Review the auto-created PR**
   - A new PR will appear: `release-vX.X.X` → `main`
   - Review the version bump in `pyproject.toml`
   - Edit `docs/whatsnew.rst` to add detailed release notes
   - Ensure all tests pass

4. **Merge the PR**
   - Once satisfied, merge the PR
   - The tag will be automatically created and pushed
   - PyPI publish and GitHub Release will trigger automatically

5. **Verify the release**
   - Check that tag was created: https://github.com/ESGF/esg-publisher/tags
   - Check PyPI: https://pypi.org/project/esgcet/
   - Check GitHub Releases: https://github.com/ESGF/esg-publisher/releases

## Rollback Plan

If something goes wrong:

1. **Before merge**: Simply close the PR without merging
2. **After merge but before tag**: Delete the merge commit (requires force push)
3. **After tag is created**: 
   - Delete the tag: `git push origin --delete vX.X.X`
   - Delete the GitHub Release
   - PyPI uploads cannot be deleted (only yanked), so avoid merging if unsure

## Alternative: Fully Automated with Release Please

If you prefer zero-manual-triggers:

```yaml
# .github/workflows/release-please.yml
name: Release Please

on:
  push:
    branches: [main]

jobs:
  release-please:
    runs-on: ubuntu-latest
    steps:
      - uses: google-github-actions/release-please-action@v4
        with:
          release-type: python
          package-name: esgcet
```

**Requirements**:
- Use conventional commits: `feat:`, `fix:`, `chore:`, etc.
- Every commit to main triggers analysis
- Release Please creates/updates a release PR automatically
- Merging that PR creates the tag

**Pros**: Zero manual steps
**Cons**: Requires team to follow conventional commit format

## Next Steps

1. Review this plan
2. Choose approach (manual trigger vs. Release Please)
3. Create the workflow files
4. Test with a patch release (e.g., v5.5.2-rc1)
5. Document the process in CONTRIBUTING.md

## Questions to Consider

1. **Who should have permission to trigger releases?**
   - Currently: Anyone with write access
   - Can restrict with GitHub environment protection rules

2. **Should we create pre-releases for testing?**
   - Could add `--pre-release` flag to workflow
   - Would publish to Test PyPI first

3. **Do we want release candidates?**
   - Could add `rc` bump type (5.5.1 → 5.5.2-rc1)
   - Test before final release

4. **Should integration → main PRs always trigger releases?**
   - Current plan: No, only PRs created by the release workflow
   - Alternative: Every merge to main = release (Release Please style)
