# CandelaAssets File Management

This repository is production data for Candela. Pushing to `master` can change what the app loads without publishing a new app build.

## Current Live Entry Points

- Books list: `assets/List_Books.json`
- Default subject fallback: `assets/Physics_Paper_1.json`
- Contributor list: `assets/ContributorsList.json`

Keep these root files as the live source. Avoid reintroducing duplicate production JSON under `assets/CandelaJsonFiles/` unless it is clearly marked as legacy or staging and is not referenced by `List_Books.json`.

## Removed Content

`assets/SardaFiles/` is not needed for the Candela app and has been removed from the production asset tree.

## Rules

- Keep URLs stable when possible. Do not rename files already referenced by JSON unless the JSON is updated in the same commit.
- Do not commit `.DS_Store`, temporary optimizer files, local scripts, or editor metadata.
- Prefer WebP for still images used by lessons and contributors.
- Keep animated GIF only when animation is required and the app cannot yet use WebP/MP4 for that asset.
- For PDFs, preserve readability first. Do not run aggressive compression over textbooks unless the output is visually reviewed.
- Use lowercase, extension-bearing file names for new assets. Avoid spaces and Bangla characters in new file paths; keep old paths stable until JSON migration is complete.
- Treat `assets/List_Books.json` as a release manifest. Any URL change there needs validation before push.

## Validation Before Push

Run:

```bash
python3 tools/validate_assets.py
```

By default this validates the production graph starting from `assets/List_Books.json` plus contributors. It checks JSON parsing, raw GitHub links, missing local files, old `CandelaPics` URLs, commit-hash raw URLs, `.DS_Store` files, and large media files.

For a deeper legacy/staging sweep, run:

```bash
python3 tools/validate_assets.py --all-json
```

`--all-json` is expected to be noisier until old folders such as `assets/CandelaJsonFiles/` and `assets/NewJsonFormatFiles/` are either cleaned or removed from production maintenance.

## Suggested Future Structure

Use this shape for new content:

```text
assets/
  List_Books.json
  Physics_Paper_1.json
  pdfs/
    physics_1/ch01/...
    math_1/ch01/...
images/
  physics_1/ch01/...
  contributors/...
```

Do not move existing live files into this structure in bulk. Migrate gradually: copy, update JSON, validate, then remove the old path only after the app no longer references it.
