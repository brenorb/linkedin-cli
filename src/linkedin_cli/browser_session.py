from __future__ import annotations

import importlib
from dataclasses import dataclass
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any


SUPPORTED_BROWSERS = ("chrome", "chromium", "brave", "edge", "vivaldi")


@dataclass(frozen=True, slots=True)
class VoyagerBrowserSession:
    browser: str
    li_at: str
    jsessionid: str
    csrf_token: str


def load_voyager_session_from_browser(
    *,
    browser: str,
    cookie_file: Path | None = None,
    domain_name: str = ".linkedin.com",
) -> VoyagerBrowserSession:
    jar = _load_browser_cookie_jar(browser=browser, cookie_file=cookie_file, domain_name=domain_name)
    cookies = _cookies_by_name(jar)

    li_at = cookies.get("li_at")
    jsessionid = cookies.get("JSESSIONID")
    if not li_at:
        raise ValueError(
            f"LinkedIn session cookie `li_at` was not found in the {browser} cookie store for {domain_name}."
        )
    if not jsessionid:
        raise ValueError(
            f"LinkedIn session cookie `JSESSIONID` was not found in the {browser} cookie store for {domain_name}."
        )

    return VoyagerBrowserSession(
        browser=browser,
        li_at=li_at,
        jsessionid=jsessionid,
        csrf_token=jsessionid.strip('"'),
    )


def _load_browser_cookie_jar(
    *,
    browser: str,
    cookie_file: Path | None,
    domain_name: str,
) -> CookieJar:
    browser_cookie3 = _browser_cookie3_module()
    loader = getattr(browser_cookie3, browser, None)
    if loader is None or browser not in SUPPORTED_BROWSERS:
        supported = ", ".join(SUPPORTED_BROWSERS)
        raise ValueError(f"Unsupported browser `{browser}`. Expected one of: {supported}.")

    kwargs: dict[str, Any] = {"domain_name": domain_name}
    if cookie_file is not None:
        kwargs["cookie_file"] = str(cookie_file)
    return loader(**kwargs)


def _browser_cookie3_module() -> Any:
    try:
        return importlib.import_module("browser_cookie3")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "browser-cookie3 is required for browser-backed Voyager auth. "
            "Install project dependencies again to enable `--browser`."
        ) from exc


def _cookies_by_name(jar: CookieJar) -> dict[str, str]:
    cookies: dict[str, str] = {}
    for cookie in jar:
        if cookie.name not in cookies and cookie.value:
            cookies[cookie.name] = cookie.value
    return cookies
