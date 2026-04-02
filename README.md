# Kanameliser Blender Extensions

[日本語](README.ja.md)

Index repository for Blender Extensions. Serves `index.json` and landing pages via GitHub Pages. Actual addon zip files are distributed directly from each addon repository's GitHub Release assets.

**Landing page:** `https://kxn4t.github.io/blender-extensions/`

**Repository URL (for Blender):** `https://kxn4t.github.io/blender-extensions/index.json`

## How to Add the Repository

1. In Blender, open **Edit > Preferences > Get Extensions**
2. **Repositories** dropdown → **+** → **Add Remote Repository**
3. Enter the URL: `https://kxn4t.github.io/blender-extensions/index.json`

## Included Addons

| Addon | Description | Links |
|---|---|---|
| Vertex Group Merger | Merge multiple vertex groups into a single target group | [GitHub](https://github.com/kxn4t/vertex-group-merger) / [BOOTH](https://kanameliser.booth.pm/items/6853101) |
| Pose to Rest Pose | Apply pose as rest pose while preserving shape keys and drivers | [GitHub](https://github.com/kxn4t/pose-to-rest-pose) / [BOOTH](https://kanameliser.booth.pm/items/6999784) |

---

## Developer Information

### Architecture

- **Each addon repo:** Builds and publishes zip as a GitHub Release asset
- **This repo (blender-extensions):** Serves `index.json` and landing pages via GitHub Pages
- **Blender downloads zip** directly from the addon repo's Release asset → GitHub Release `download_count` reflects actual usage

### How It Works

```
Addon repository                      Index repository (blender-extensions)
       |                                        |
  Tag push → release.yml                        |
    Build zip → create draft release            |
       |                                        |
  Manually publish                              |
       |                                        |
  dispatch.yml → repository_dispatch ──────────>|
       |                                  update-extension.yml:
       |                                    Download zip (temp, for hash/size)
       |                                    Get Release asset URL via API
       |                                    Update index.json (archive_url → Release asset)
       |                                    Update landing pages
       |                                    Commit & push (index.json + READMEs only)
       |                                        |
       |                                  pages.yml → Deploy to GitHub Pages
```

### Release Procedure (Updating an Existing Addon)

1. In the **addon repository**, update the version in `blender_manifest.toml` and push a tag
   ```bash
   git tag v1.2.0
   git push origin v1.2.0
   ```
2. `release.yml` runs, builds the zip, and creates a **draft release**
3. Review the release page on GitHub and click **Publish release**
4. `dispatch.yml` runs and sends a `repository_dispatch` to the distribution repository
5. `update-extension.yml` in the index repository temporarily downloads the zip (for hash/size), fetches the Release asset URL, and updates `index.json`
6. The push triggers `pages.yml`, which deploys to GitHub Pages

> Everything after step 3 (Publish) is fully automatic. The only manual steps are **pushing the tag** and **publishing the release**.

### Addon `id` Naming Convention

The `id` field in `blender_manifest.toml` serves as the system-wide identifier. Everything is unified based on the `id`.

| Usage | Format | Example |
|---|---|---|
| `id` in `blender_manifest.toml` | `snake_case` | `vertex_group_merger` |
| Zip filename | `{id}-{version}.zip` | `vertex_group_merger-0.6.0.zip` |
| `index.json` entry identification | Matched by `id` field | Only the latest entry per `id` |

> The `id` is used internally by Blender to identify packages. Only lowercase letters, digits, and underscores are allowed (no hyphens). Once published, the `id` must not be changed.

### Legacy Addon to Extension Migration Checklist

Checklist for converting an existing addon to the Extension format (official docs: [Getting Started](https://docs.blender.org/manual/en/latest/advanced/extensions/getting_started.html) / [Add-ons](https://docs.blender.org/manual/en/latest/advanced/extensions/addons.html)):

**Code migration:**

- [ ] Create `blender_manifest.toml`
- [ ] Remove `bl_info` (version info is now in the manifest)
- [ ] Replace hardcoded module names with `__package__` (`AddonPreferences.bl_idname`, translation registration, etc.)
- [ ] Convert all imports to relative imports (`from .module import ...`)
- [ ] If using third-party Python modules, [bundle them as wheels](https://docs.blender.org/manual/en/latest/advanced/extensions/python_wheels.html)
- [ ] If writing to the addon's own directory, use `bpy.utils.extension_path_user(__package__)` instead

**Manifest notes:**

- `tagline` must not end with punctuation (`.`)
- `version` must follow semantic versioning
- `license` must use SPDX identifiers with the `SPDX:` prefix
- Optional fields that are not set should be omitted entirely, not left as empty strings or empty lists

**Testing:**

- [ ] Test by installing from disk

### Adding a New Addon

1. Add `blender_manifest.toml` to the addon repository
2. Update `.github/workflows/release.yml` to support the Extension format (include manifest, unify filename to `id`)
3. Add `.github/workflows/dispatch.yml` (template: [`templates/dispatch.yml`](templates/dispatch.yml))
4. Set `EXTENSIONS_REPO_TOKEN` in the repository Secrets
5. Add a new entry in `scripts/addons_meta.json` (used for landing page descriptions and links)
6. Push a tag, create a draft release → publish, and the addon is automatically added to the distribution repository

The only change needed on the index repository side is adding an entry to `addons_meta.json`.

### Using `generate_index.py`

```bash
RELEASE_ASSET_URL=<url> python scripts/generate_index.py add <addon_id> <version>
```

Reads `blender_manifest.toml` from the specified version's zip, computes `archive_size` and `archive_hash`, and sets `archive_url` to the `RELEASE_ASSET_URL` environment variable. Entries with the same `id` are replaced with the latest version.

In the CI pipeline, the zip is temporarily downloaded to a runner, and `RELEASE_ASSET_URL` is automatically set from the GitHub Release API.

### Using `generate_pages.py`

```bash
python scripts/generate_pages.py
```

Reads `index.json` and `scripts/addons_meta.json`, then updates the addon lists on the landing pages (`ja/README.md` and `en/README.md`). It replaces the content between `<!-- EXTENSIONS_LIST_START -->` and `<!-- EXTENSIONS_LIST_END -->` markers in each README.

Normally runs automatically within the `update-extension.yml` pipeline, so manual execution is not needed. Use it manually when you want to regenerate pages after editing descriptions or links in `addons_meta.json`.

### Rollback Procedure

To roll back to a previous version, re-run the `update-extension.yml` workflow via `workflow_dispatch` with the old tag. The workflow will download the zip from the old Release, recalculate the hash/size, and update `index.json` with the correct Release asset URL.

### References

- [Creating Extensions (Official Manual)](https://docs.blender.org/manual/en/latest/advanced/extensions/getting_started.html)
- [Creating a Static Repository (Official Manual)](https://docs.blender.org/manual/en/latest/advanced/extensions/creating_repository/static_repository.html)
- [Extensions API Listing v1 (Developer Docs)](https://developer.blender.org/docs/features/extensions/api_listing/v1/)
- [Manifest Schema (Developer Docs)](https://developer.blender.org/docs/features/extensions/schema/)
- [`blender_ext.py` (Blender Source Code)](https://projects.blender.org/blender/blender/src/branch/main/scripts/addons_core/bl_pkg/cli/blender_ext.py)
