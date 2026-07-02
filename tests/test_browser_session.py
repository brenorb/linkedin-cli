from __future__ import annotations

from http.cookiejar import Cookie, CookieJar
from pathlib import Path

import pytest

from linkedin_cli import browser_session
from linkedin_cli.browser_session import VoyagerBrowserSession, load_voyager_session_from_browser


def test_load_voyager_session_from_browser_extracts_required_cookies(monkeypatch: pytest.MonkeyPatch) -> None:
    jar = CookieJar()
    jar.set_cookie(_cookie("li_at", "test-li-at"))
    jar.set_cookie(_cookie("JSESSIONID", '"ajax:123"'))

    def fake_loader(*, browser: str, cookie_file: Path | None, domain_name: str) -> CookieJar:
        assert browser == "chrome"
        assert cookie_file == Path("/tmp/cookies.sqlite")
        assert domain_name == ".linkedin.com"
        return jar

    monkeypatch.setattr(browser_session, "_load_browser_cookie_jar", fake_loader)

    result = load_voyager_session_from_browser(
        browser="chrome",
        cookie_file=Path("/tmp/cookies.sqlite"),
    )

    assert result == VoyagerBrowserSession(
        browser="chrome",
        li_at="test-li-at",
        jsessionid='"ajax:123"',
        csrf_token="ajax:123",
    )


def test_load_voyager_session_from_browser_requires_linkedin_cookies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(browser_session, "_load_browser_cookie_jar", lambda **_: CookieJar())

    with pytest.raises(ValueError, match="li_at"):
        load_voyager_session_from_browser(browser="chrome")


def _cookie(name: str, value: str) -> Cookie:
    return Cookie(
        version=0,
        name=name,
        value=value,
        port=None,
        port_specified=False,
        domain=".linkedin.com",
        domain_specified=True,
        domain_initial_dot=True,
        path="/",
        path_specified=True,
        secure=True,
        expires=None,
        discard=False,
        comment=None,
        comment_url=None,
        rest={},
        rfc2109=False,
    )
