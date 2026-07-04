# Publishing TopHash to PyPI — Step-by-Step

This guide walks you through publishing the `tophash` package to PyPI. The package is already built and tested — you just need to do the final upload.

## What's already done

- ✅ `pyproject.toml` written with all metadata, dependencies, classifiers
- ✅ Package built: `dist/tophash-0.1.0-py3-none-any.whl` and `dist/tophash-0.1.0.tar.gz`
- ✅ Tested in a fresh venv: `pip install /path/to/wheel` works, `import tophash` works, all 3 layers (v3, TopHashX, Ω∞) functional
- ✅ `tophash/py.typed` marker added for PEP 561 type-checking support

## What you need to do

### Step 1: Create a PyPI account

1. Go to https://pypi.org/account/register/
2. Create an account using `founders@tophash.io` (or the email you want associated with the package)
3. Verify your email address
4. Enable 2FA (required for PyPI now)

### Step 2: Create a PyPI API token

1. Go to https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Scope: "Entire account" (for the first upload; you can scope future uploads to just the `tophash` project)
4. Name: "tophash-initial-upload"
5. Copy the token — it starts with `pypi-` and you'll only see it once

### Step 3: Upload to PyPI

From the `/home/z/my-project/` directory, run:

```bash
# Install twine if you don't have it
pip install twine

# Upload to PyPI (it will prompt for username/password)
# Username: __token__
# Password: <paste your pypi-... token>
twine upload dist/tophash-0.1.0-py3-none-any.whl dist/tophash-0.1.0.tar.gz
```

Or, to avoid the interactive prompt, set the token as an environment variable:

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-token-here
twine upload dist/tophash-0.1.0-py3-none-any.whl dist/tophash-0.1.0.tar.gz
```

### Step 4: Verify the upload

1. Go to https://pypi.org/project/tophash/ — you should see the package page
2. Test the install in a fresh environment:
   ```bash
   pip install tophash
   python -c "from tophash import v3, canon; import networkx as nx; print(canon.tophashx(nx.karate_club_graph(), include_certificate=False)['canonical_id'][:32])"
   ```

### Step 5: Test on TestPyPI first (optional but recommended)

If you want to test the upload process without affecting the real PyPI:

```bash
# Upload to TestPyPI first
twine upload --repository testpypi dist/tophash-0.1.0-py3-none-any.whl dist/tophash-0.1.0.tar.gz

# Test install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ tophash
```

TestPyPI account: https://test.pypi.org/account/register/ (separate from main PyPI)

## After publishing

### Update the README

The README already says `pip install tophash` — once the package is on PyPI, that command will work for everyone. No README changes needed.

### Announce

1. **Twitter/X**: "TopHash v0.1 is now on PyPI: `pip install tophash`. A training-free, theorem-backed structural identity primitive for graphs. Pynauty-backed exact canonization, bitwise-deterministic, MIT licensed. github.com/rossbuckley1990-hash/tophash"
2. **Python Weekly / PyCoder's Weekly**: Submit the DEV.to blog post
3. **Hacker News**: The "86 of 100 PyPI packages" finding is the HN hook

### Version management

For future releases (v0.2, v1.0, etc.):
1. Update `version` in `pyproject.toml`
2. Update `__version__` in `tophash/__init__.py`
3. Rebuild: `python -m build`
4. Upload: `twine upload dist/tophash-X.Y.Z-*`

PyPI does not allow re-uploading the same version number, so each release must have a unique version.

## Troubleshooting

**"File already exists" error**: You're trying to upload a version that's already on PyPI. Bump the version in `pyproject.toml`.

**"Invalid token" error**: Make sure your token starts with `pypi-` and you're using `__token__` as the username.

**Build dependencies missing**: Run `pip install build twine` to ensure you have the build tools.

**pynauty install fails on user machines**: pynauty requires a C compiler. The `pyproject.toml` lists it as a hard dependency. If this becomes a problem, we can make it optional and fall back to the bounded-search heuristic (with `exactness_guaranteed: False`).
