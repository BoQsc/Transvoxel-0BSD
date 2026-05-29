# Release notes v34

v34 fixes the GitHub Actions repository check from v33.

## Fixed

`tools/test_core_c.py` can create `proof/c_compiler_cache.json` during a CI run. In v33,
`tools/github_ready_report.py` treated any local generated cache file as a repository failure.
That made the GitHub workflow fail after the C smoke test even when the file was ignored by
`.gitignore`.

v34 changes the GitHub-ready check to detect forbidden files through `git ls-files` when a Git
checkout is available. Local generated files may exist after a run, but they only fail the check if
they are actually tracked by Git.

## If upgrading an existing repository

If `proof/c_compiler_cache.json` was already committed, remove it from Git tracking:

```cmd
git rm --cached proof/c_compiler_cache.json
git commit -m "Remove generated compiler cache"
```

The file is local runtime state and should not be committed.
