from __future__ import annotations

import json
import subprocess
import sys

from linkedin_cli.employment import normalize_browser_experience_entries


def load_employment_history_from_chrome_profile(public_identifier: str) -> list[dict[str, object]]:
    if sys.platform != "darwin":
        raise RuntimeError("Chrome profile scraping fallback currently supports macOS only.")

    script = _apple_script_for_profile(public_identifier)
    result = subprocess.run(
        ["osascript"],
        input=script,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        if "Allow JavaScript from Apple Events" in stderr:
            raise RuntimeError(
                "Chrome fallback needs `View > Developer > Allow JavaScript from Apple Events` enabled."
            )
        raise RuntimeError(f"Chrome fallback failed: {stderr or 'unknown AppleScript error'}")

    payload = json.loads(result.stdout or "{}")
    entries = payload.get("entries")
    if not isinstance(entries, list):
        return []
    return normalize_browser_experience_entries(entries)


def _apple_script_for_profile(public_identifier: str) -> str:
    target_url = f"https://www.linkedin.com/in/{public_identifier}/details/experience/"
    javascript = r"""
(() => {
  const monthPattern = /(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\s*-\s*(?:Present|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4})/i;
  const cards = Array.from(document.querySelectorAll('[componentkey^="entity-collection-item"]'))
    .map((item) => ({
      lines: item.innerText.split("\n").map((line) => line.trim()).filter(Boolean),
      description: item.querySelector('[data-testid="expandable-text-box"]')?.innerText?.trim() || null,
    }))
    .filter((entry) => entry.lines.some((line) => monthPattern.test(line)));
  if (cards.length > 0) {
    return JSON.stringify({ entries: cards });
  }

  const sections = Array.from(document.querySelectorAll("section"));
  const experience = sections.find((section) => {
    const heading = section.querySelector("h1, h2, h3, h4");
    return heading && heading.innerText.trim().toLowerCase() === "experience";
  }) || sections.find((section) => /\bExperience\b/.test(section.innerText || ""));
  if (!experience) {
    return JSON.stringify({ entries: [] });
  }
  const entries = Array.from(experience.querySelectorAll("li"))
    .map((item) => item.innerText.split("\n").map((line) => line.trim()).filter(Boolean))
    .filter((lines) => lines.some((line) => monthPattern.test(line)));
  return JSON.stringify({ entries });
})();
""".strip()
    target_url_literal = _apple_script_string(target_url)
    javascript_literal = _apple_script_string(javascript)
    return f"""
tell application "Google Chrome"
  if (count of windows) is 0 then
    make new window
  end if
  set targetUrl to {target_url_literal}
  set jsCode to {javascript_literal}
  tell front window
    set targetIndex to missing value
    repeat with i from 1 to (count of tabs)
      if (URL of tab i as text) contains targetUrl then
        set targetIndex to i
        exit repeat
      end if
    end repeat
    if targetIndex is missing value then
      make new tab at end of tabs with properties {{URL:targetUrl}}
      set targetIndex to count of tabs
    end if
    set active tab index to targetIndex
  end tell
  delay 5
  return execute active tab of front window javascript jsCode
end tell
""".strip()


def _apple_script_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
