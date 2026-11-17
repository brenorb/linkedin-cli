----------------------------- MODULE PostVideo -----------------------------
\* Posting a video with `linkedin post create --video`, as the user sees it.
VARIABLES screen, asset

vars == <<screen, asset>>

Init == screen = "command" /\ asset = "none"

Uploads == screen = "command" /\ screen' = "processing" /\ asset' = "held"
UploadFails == screen = "command" /\ screen' = "error" /\ UNCHANGED asset
Ready == screen = "processing" /\ screen' = "posting" /\ UNCHANGED asset
TimesOut == screen = "processing" /\ screen' = "reuse" /\ UNCHANGED asset
Rejected == screen = "processing" /\ screen' = "error" /\ asset' = "failed"
Published == screen = "posting" /\ screen' = "posted" /\ UNCHANGED asset
PostRefused == screen = "posting" /\ screen' = "reuse" /\ UNCHANGED asset
RetryWithUrn == screen = "reuse" /\ screen' = "posting" /\ UNCHANGED asset

Done == screen \in {"posted", "error"} /\ UNCHANGED vars

Next == Uploads \/ UploadFails \/ Ready \/ TimesOut \/ Rejected \/ Published
        \/ PostRefused \/ RetryWithUrn \/ Done

Spec == Init /\ [][Next]_vars

\* A held asset is always either posted or offered for reuse.
HeldAssetNotLost == screen = "error" => asset # "held"
=============================================================================
