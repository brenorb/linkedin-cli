----------------------------- MODULE UploadFlow -----------------------------
\* `linkedin post create --video` (or --document, --image) in
\* src/linkedin_cli/client.py: initialize, upload, finalize, wait for
\* processing, create the post. Each failure ends the command with an error.
\*   Upload        -> _initialize_video_upload, _upload_video_parts,
\*                    _finalize_video_upload (one step: the bytes are in)
\*   Processed     -> _wait_for_asset_availability sees AVAILABLE
\*   ProcessFails  -> PROCESSING_FAILED: AssetProcessingFailedError
\*   WaitTimesOut  -> the deadline passes while PROCESSING
\*   Posted        -> POST /rest/posts succeeds
\*   PostFails     -> POST /rest/posts returns an error
\*   Retry         -> the user runs the command again, reusing the asset
\*                    only if the error named it
\* Broken = TRUE is the code before the fix: no error named the asset.
EXTENDS Naturals

CONSTANT Broken

VARIABLES pc, assetUsable, named, uploads, posts

vars == <<pc, assetUsable, named, uploads, posts>>

Init ==
  /\ pc = "start" /\ assetUsable = FALSE /\ named = FALSE
  /\ uploads = 0 /\ posts = 0

Upload ==
  /\ pc = "start" /\ uploads < 2
  /\ uploads' = uploads + 1 /\ assetUsable' = TRUE /\ pc' = "uploaded"
  /\ UNCHANGED <<named, posts>>

Processed == pc = "uploaded" /\ pc' = "ready" /\ UNCHANGED <<assetUsable, named, uploads, posts>>

ProcessFails ==
  /\ pc = "uploaded"
  /\ pc' = "failed" /\ assetUsable' = FALSE /\ named' = FALSE
  /\ UNCHANGED <<uploads, posts>>

WaitTimesOut ==
  /\ pc = "uploaded"
  /\ pc' = "failed" /\ named' = ~Broken
  /\ UNCHANGED <<assetUsable, uploads, posts>>

Posted == pc = "ready" /\ pc' = "done" /\ posts' = posts + 1 /\ UNCHANGED <<assetUsable, named, uploads>>

PostFails ==
  /\ pc = "ready"
  /\ pc' = "failed" /\ named' = ~Broken
  /\ UNCHANGED <<assetUsable, uploads, posts>>

\* With a named asset the retry passes --video-urn and skips the upload.
Retry ==
  /\ pc = "failed"
  /\ IF named /\ assetUsable
     THEN pc' = "ready"
     ELSE pc' = "start"
  /\ named' = FALSE
  /\ UNCHANGED <<assetUsable, uploads, posts>>

\* The model stops after two uploads; the user may also give up.
Done == (pc = "done" \/ (pc = "start" /\ uploads = 2)) /\ UNCHANGED vars

Next == Upload \/ Processed \/ ProcessFails \/ WaitTimesOut \/ Posted \/ PostFails \/ Retry \/ Done

Spec == Init /\ [][Next]_vars

\* When the command fails after LinkedIn holds a usable asset, the error
\* names it, so the retry posts it without uploading the file again.
UsableAssetIsNamed == pc = "failed" /\ assetUsable => named
=============================================================================
