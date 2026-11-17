---
name: verify-linkedin-media-post
description: Check that a failed video, document or image post never makes the user upload the file again when LinkedIn already holds a usable asset. Use when changing create_video_post, create_document_post, create_image_post, _after_upload, _wait_for_asset_availability, AssetProcessingFailedError, or the upload steps in src/linkedin_cli/client.py.
---

# Verify LinkedIn media posts

**Property.** `UsableAssetIsNamed`: when `post create` fails after LinkedIn holds a usable uploaded asset (processing timed out, or the post call failed), the error names the asset URN and its reuse flag.

**Harm if broken.** The user uploads a large video again, and LinkedIn keeps an unused asset from the first try.

## Run

```sh
export TLA2TOOLS=/absolute/path/to/tla2tools.jar   # TLC 1.7.4 release
export JAVA=/path/to/java                          # Java 11 or later
bash scripts/verification/check-model.sh .claude/skills/verify-linkedin-media-post/model/UploadFlow.tla
bash scripts/verification/check-model.sh .claude/skills/verify-linkedin-media-post/model/UploadFlow.tla --mutant
uv run --frozen pytest -q tests/test_client.py -k reusable
```

The model must pass (13 distinct states). The `--mutant` run replays the code before commit c6021d8 and must report `UsableAssetIsNamed` violated (upload, then the wait times out). The test drives both failure paths through `httpx.MockTransport`. Read every TLC result with the pstack `/statechart` skill.

## Coverage

Synced with the code at commit `c6021d8`. Move this forward only after you confirm that the model still describes the code at the new commit.

| Model step | Code (`src/linkedin_cli/client.py`) |
| --- | --- |
| `Upload` | `_initialize_video_upload`, `_upload_video_parts`, `_finalize_video_upload` (also the image and document uploads) |
| `Processed`, `ProcessFails`, `WaitTimesOut` | `_wait_for_asset_availability` |
| `Posted`, `PostFails` | `_create_media_post` |
| failure after upload | `_after_upload` |

## Not covered

Multi-image posts, captions and thumbnails, a failure in the middle of the upload (the asset is then unusable), and duplicate text posts when a network timeout hides a post LinkedIn already created.
