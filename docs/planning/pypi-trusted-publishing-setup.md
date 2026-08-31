# PyPI Trusted Publishing Setup Guide

**Purpose**: Configure PyPI to accept package uploads from GitHub Actions without API tokens

**Status**: Needs to be configured before first automated release

## What is Trusted Publishing?

PyPI Trusted Publishing uses OpenID Connect (OIDC) to verify that the package upload is coming from an authorized GitHub Actions workflow. No API tokens are stored or exposed.

## Prerequisites

- Admin access to PyPI project: https://pypi.org/project/esgcet/
- Package must already exist on PyPI (✅ esgcet exists)
- Workflow file must be committed: `.github/workflows/publish-pypi.yml` (✅ done)

## Configuration Steps

### 1. Go to PyPI Project Settings

Navigate to: https://pypi.org/manage/project/esgcet/settings/publishing/

### 2. Add Trusted Publisher

Click **"Add a new pending publisher"** or **"Add a new publisher"** (if package exists)

Fill in the form:

| Field | Value | Notes |
|-------|-------|-------|
| **PyPI Project Name** | `esgcet` | Must match exactly |
| **Owner** | `ESGF` | GitHub organization name |
| **Repository name** | `esg-publisher` | GitHub repo name |
| **Workflow filename** | `publish-pypi.yml` | Must match `.github/workflows/publish-pypi.yml` |
| **Environment name** | (leave empty) | Optional - can use "release" if you want extra protection |

### 3. Save Configuration

Click **"Add"** to save the trusted publisher configuration.

## How It Works

1. Developer pushes a version tag: `git push origin v5.5.0`
2. GitHub Actions workflow triggered by tag
3. Workflow builds the package (sdist + wheel)
4. GitHub generates OIDC token for the workflow
5. PyPI verifies:
   - Token is from `ESGF/esg-publisher` repository
   - Token is from `publish-pypi.yml` workflow
   - Token is valid and not expired
6. If verified, PyPI accepts the upload
7. Package published! 🎉

## Security Benefits

✅ **No API tokens** - Nothing to leak or rotate  
✅ **Scoped permissions** - Only specific workflow can publish  
✅ **Audit trail** - PyPI records which workflow published each version  
✅ **Automatic** - No manual intervention needed  

## Testing the Configuration

### Before Testing - Prerequisites

1. ✅ Trusted publisher configured on PyPI
2. ✅ Workflow file committed to repository
3. ✅ Version in `pyproject.toml` is higher than current PyPI version

### Test with a Pre-release

```bash
# Update version to a pre-release
# Edit pyproject.toml: version = "5.5.0a1"

# Commit the version bump
git add pyproject.toml
git commit -m "chore: bump version to 5.5.0a1"
git push

# Create and push the tag
git tag v5.5.0a1
git push origin v5.5.0a1

# Watch the workflow
# Go to: https://github.com/ESGF/esg-publisher/actions
```

If successful, you'll see:
- ✅ Workflow completes successfully
- ✅ Package appears on PyPI: https://pypi.org/project/esgcet/5.5.0a1/
- ✅ GitHub release created: https://github.com/ESGF/esg-publisher/releases/tag/v5.5.0a1

### If Testing Fails

**Common issues:**

1. **"Trusted publisher not found"**
   - Check configuration matches exactly: `ESGF`, `esg-publisher`, `publish-pypi.yml`
   - Ensure workflow file is in the repository when tag is pushed

2. **"Version already exists"**
   - Use a different version number
   - PyPI doesn't allow re-uploading the same version

3. **"Invalid OIDC token"**
   - Ensure workflow has `id-token: write` permission
   - Check that workflow runs on tag, not on push to branch

## Alternative: Test PyPI

You can test the entire process on Test PyPI first:

### 1. Configure Test PyPI Trusted Publisher

Go to: https://test.pypi.org/manage/project/esgcet/settings/publishing/

(Same configuration as above, but on test.pypi.org)

### 2. Modify Workflow Temporarily

Add to the "Publish to PyPI" step:

```yaml
- name: Publish to Test PyPI
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    repository-url: https://test.pypi.org/legacy/
```

### 3. Test Release

```bash
git tag v5.5.0-test1
git push origin v5.5.0-test1
```

### 4. Verify on Test PyPI

Check: https://test.pypi.org/project/esgcet/

### 5. Revert Workflow

Remove the `repository-url` line for production releases.

## Production Release Checklist

Before the first production release using trusted publishing:

- [ ] Trusted publisher configured on PyPI
- [ ] Workflow tested (either on Test PyPI or with pre-release)
- [ ] Version number in `pyproject.toml` updated
- [ ] Release notes in `docs/whatsnew.rst` updated
- [ ] All tests passing in CI
- [ ] Documentation builds successfully

## Release Process

Once configured, releasing is simple:

```bash
# 1. Update version and docs
vim pyproject.toml  # Update version
vim docs/whatsnew.rst  # Add release notes
git add pyproject.toml docs/whatsnew.rst
git commit -m "chore: prepare v5.5.0 release"
git push

# 2. Create and push tag
git tag -a v5.5.0 -m "Release v5.5.0 - Package refactoring and test suite"
git push origin v5.5.0

# 3. Workflow does the rest automatically!
```

## Troubleshooting

### Where to Find Logs

1. **GitHub Actions logs**: https://github.com/ESGF/esg-publisher/actions
   - Shows build process, testing, and upload status
   - Look for "Publish to PyPI" step

2. **PyPI upload history**: https://pypi.org/manage/project/esgcet/releases/
   - Shows successful uploads
   - Shows which GitHub workflow published each version

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `File already exists` | Version already on PyPI | Bump version number |
| `Invalid or expired token` | OIDC token issue | Check workflow permissions |
| `Trusted publisher not configured` | PyPI configuration missing | Complete setup steps |
| `Insufficient permissions` | Workflow missing `id-token: write` | Add to workflow permissions |

### Getting Help

- **PyPI Trusted Publishers**: https://docs.pypi.org/trusted-publishers/
- **GitHub OIDC**: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect
- **pypa/gh-action-pypi-publish**: https://github.com/pypa/gh-action-pypi-publish

## Security Notes

### What This Does NOT Do

- ❌ Does not give GitHub Actions access to modify PyPI settings
- ❌ Does not allow uploads from forks
- ❌ Does not allow uploads from pull requests
- ❌ Does not allow uploads from any workflow except `publish-pypi.yml`

### What This DOES

- ✅ Allows ONLY the specified workflow to upload packages
- ✅ Requires the tag to be on the main repository (not a fork)
- ✅ Creates an audit trail of all uploads
- ✅ Can be revoked at any time from PyPI settings

## Maintenance

### Rotating Credentials

With trusted publishing, there are **no credentials to rotate**! 🎉

The OIDC tokens are:
- Generated fresh for each workflow run
- Valid for only a few minutes
- Automatically expired after use

### Revoking Access

To revoke access:
1. Go to https://pypi.org/manage/project/esgcet/settings/publishing/
2. Find the trusted publisher entry
3. Click "Remove"

The workflow will immediately stop working (no grace period).

### Updating the Workflow

If you rename the workflow file:
1. Rename `.github/workflows/publish-pypi.yml` to new name
2. Update the PyPI trusted publisher configuration
3. Test with a pre-release tag

## Questions & Answers

**Q: Do we need to do this for every fork?**  
A: No. Only the upstream `ESGF/esg-publisher` repository can publish to PyPI.

**Q: What if someone pushes a malicious tag?**  
A: Only repository maintainers with push access can create tags on `ESGF/esg-publisher`. This is the same trust level required for manual releases.

**Q: Can we still publish manually if needed?**  
A: Yes! You can still use `twine upload` with an API token for emergency releases. This just adds an automated option.

**Q: What happens to old API tokens?**  
A: They continue to work. You can keep them as a backup or revoke them. Trusted publishing is recommended for all new releases.

## Summary

**To enable automated PyPI releases:**

1. ✅ (Done) Create workflow: `.github/workflows/publish-pypi.yml`
2. ⏳ (Needed) Configure trusted publisher on PyPI
3. ✅ (Done) Push workflow to repository
4. 🧪 (Recommended) Test with pre-release or Test PyPI
5. 🚀 (Ready) Push version tags to trigger releases

**Time to configure:** ~5 minutes  
**Maintenance required:** None  
**Security improvement:** Significant  
