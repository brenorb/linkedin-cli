export const title = "Post a video from the CLI";
const screens = {
  command: "Run post create --video",
  processing: "Uploaded, LinkedIn processing",
  posting: "Creating the post",
  posted: "Post published",
  reuse: "Error names the video URN",
  error: "Error, nothing to reuse",
};
export const state = (v) => screens[v.screen];
const steps = {
  Uploads: "the file uploads",
  UploadFails: "the upload fails",
  Ready: "processing finishes",
  TimesOut: "processing outlasts the wait",
  Rejected: "LinkedIn cannot process the video",
  Published: "LinkedIn creates the post",
  PostRefused: "the post call fails",
  RetryWithUrn: "you rerun with --video-urn",
};
export const step = (action) => steps[action] ?? null;
export const group = (v) =>
  v.screen === "posted" ? "done" : v.screen === "error" ? "stopped" : v.screen === "reuse" ? "resumable" : "working";
export const colors = { done: "teal", stopped: "orange", resumable: "yellow", working: "blue" };
