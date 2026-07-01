import json
from pathlib import Path

import httpx
import pytest

from linkedin_cli.client import LinkedInApiError, LinkedInClient


def test_client_defaults_to_current_linkedin_api_version() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Linkedin-Version"] == "202606"
        return httpx.Response(
            201,
            headers={"x-restli-id": "urn:li:share:987"},
            json={"id": "urn:li:share:987"},
        )

    client = LinkedInClient(
        access_token="test-token",
        transport=httpx.MockTransport(handler),
    )

    result = client.create_text_post(
        author="urn:li:person:abc123",
        commentary="Hello from tests",
    )

    assert result.post_id == "urn:li:share:987"


def test_create_text_post_uses_rest_posts_api() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/posts")
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["Linkedin-Version"] == "202505"
        assert request.headers["X-Restli-Protocol-Version"] == "2.0.0"

        payload = json.loads(request.content.decode("utf-8"))
        assert payload == {
            "author": "urn:li:person:abc123",
            "commentary": "Hello from tests",
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        return httpx.Response(
            201,
            headers={"x-restli-id": "urn:li:share:987"},
            json={"id": "urn:li:share:987"},
        )

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.create_text_post(
        author="urn:li:person:abc123",
        commentary="Hello from tests",
    )

    assert result.post_id == "urn:li:share:987"
    assert result.response["id"] == "urn:li:share:987"


def test_create_reshare_post_uses_reshare_context() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/posts")
        payload = json.loads(request.content.decode("utf-8"))
        assert payload == {
            "author": "urn:li:person:abc123",
            "commentary": "Worth reading",
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
            "reshareContext": {
                "parent": "urn:li:share:555",
            },
        }
        return httpx.Response(
            201,
            headers={"x-restli-id": "urn:li:share:999"},
            json={"id": "urn:li:share:999"},
        )

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.create_reshare_post(
        author="urn:li:person:abc123",
        commentary="Worth reading",
        reshared_post_urn="urn:li:share:555",
    )

    assert result.post_id == "urn:li:share:999"


def test_get_post_uses_rest_posts_api() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL(
            "https://api.linkedin.com/rest/posts/urn%3Ali%3Ashare%3A987?viewContext=AUTHOR"
        )
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["Linkedin-Version"] == "202505"
        return httpx.Response(
            200,
            json={
                "id": "urn:li:share:987",
                "author": "urn:li:person:abc123",
                "commentary": "Hello from tests",
            },
        )

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.get_post("urn:li:share:987", view_context="AUTHOR")

    assert result["id"] == "urn:li:share:987"
    assert result["commentary"] == "Hello from tests"


def test_list_posts_uses_author_finder() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL(
            "https://api.linkedin.com/rest/posts"
            "?author=urn%3Ali%3Aperson%3Aabc123&q=author&count=25&start=5&sortBy=CREATED&viewContext=AUTHOR"
        )
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["Linkedin-Version"] == "202505"
        assert request.headers["X-RestLi-Method"] == "FINDER"
        return httpx.Response(
            200,
            json={
                "paging": {"start": 5, "count": 25, "links": []},
                "elements": [
                    {
                        "id": "urn:li:share:987",
                        "author": "urn:li:person:abc123",
                        "commentary": "Newest first",
                    }
                ],
            },
        )

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.list_posts(
        author="urn:li:person:abc123",
        count=25,
        start=5,
        sort_by="CREATED",
        view_context="AUTHOR",
    )

    assert result["paging"]["start"] == 5
    assert result["elements"][0]["id"] == "urn:li:share:987"


def test_batch_get_posts_uses_rest_posts_batch_get() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL(
            "https://api.linkedin.com/rest/posts"
            "?ids=List(urn%3Ali%3Ashare%3A123,urn%3Ali%3Ashare%3A456)&viewContext=AUTHOR"
        )
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["Linkedin-Version"] == "202505"
        assert request.headers["X-RestLi-Method"] == "BATCH_GET"
        return httpx.Response(
            200,
            json={
                "results": {
                    "urn:li:share:123": {"id": "urn:li:share:123"},
                    "urn:li:share:456": {"id": "urn:li:share:456"},
                },
                "statuses": {},
                "errors": {},
            },
        )

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.batch_get_posts(
        ["urn:li:share:123", "urn:li:share:456"],
        view_context="AUTHOR",
    )

    assert result["results"]["urn:li:share:123"]["id"] == "urn:li:share:123"
    assert result["results"]["urn:li:share:456"]["id"] == "urn:li:share:456"


def test_get_document_uses_rest_documents_api() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/documents/urn%3Ali%3Adocument%3A123")
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["Linkedin-Version"] == "202505"
        return httpx.Response(200, json={"id": "urn:li:document:123", "status": "AVAILABLE"})

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.get_document("urn:li:document:123")

    assert result["id"] == "urn:li:document:123"


def test_batch_get_documents_uses_restli_batch_get() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL(
            "https://api.linkedin.com/rest/documents"
            "?ids=List(urn%3Ali%3Adocument%3A123,urn%3Ali%3Adocument%3A456)"
        )
        assert request.headers["X-RestLi-Method"] == "BATCH_GET"
        return httpx.Response(
            200,
            json={
                "results": {
                    "urn:li:document:123": {"id": "urn:li:document:123"},
                    "urn:li:document:456": {"id": "urn:li:document:456"},
                }
            },
        )

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.batch_get_documents(["urn:li:document:123", "urn:li:document:456"])

    assert result["results"]["urn:li:document:456"]["id"] == "urn:li:document:456"


def test_list_organization_access_uses_role_assignee_finder() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL(
            "https://api.linkedin.com/rest/organizationAcls"
            "?q=roleAssignee&count=100&start=0&role=ADMINISTRATOR&state=APPROVED"
        )
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["Linkedin-Version"] == "202505"
        assert request.headers["X-RestLi-Method"] == "FINDER"
        return httpx.Response(
            200,
            json={
                "elements": [
                    {
                        "organization": "urn:li:organization:2414183",
                        "roleAssignee": "urn:li:person:abc123",
                        "role": "ADMINISTRATOR",
                        "state": "APPROVED",
                    }
                ],
                "paging": {"count": 100, "start": 0, "links": []},
            },
        )

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.list_organization_access(
        count=100,
        start=0,
        role="ADMINISTRATOR",
        state="APPROVED",
    )

    assert result["elements"][0]["organization"] == "urn:li:organization:2414183"


def test_preflight_organization_author_summarizes_post_capability() -> None:
    requests: list[httpx.Request] = []
    acl_url = httpx.URL(
        "https://api.linkedin.com/rest/organizationAcls"
        "?q=roleAssignee&count=100&start=0"
    )
    authorization_urls = {
        "ORGANIC_SHARE_CREATE": httpx.URL(
            "https://api.linkedin.com/rest/organizationAuthorizations/"
            "(impersonator:urn%3Ali%3Aperson%3Aabc123,organization:urn%3Ali%3Aorganization%3A2414183,"
            "action:(organizationContentAuthorizationAction:(actionType:ORGANIC_SHARE_CREATE)))"
        ),
        "ORGANIC_SHARE_VIEW_AS_AUTHOR": httpx.URL(
            "https://api.linkedin.com/rest/organizationAuthorizations/"
            "(impersonator:urn%3Ali%3Aperson%3Aabc123,organization:urn%3Ali%3Aorganization%3A2414183,"
            "action:(organizationContentAuthorizationAction:(actionType:ORGANIC_SHARE_VIEW_AS_AUTHOR)))"
        ),
        "ORGANIC_SHARE_EDIT": httpx.URL(
            "https://api.linkedin.com/rest/organizationAuthorizations/"
            "(impersonator:urn%3Ali%3Aperson%3Aabc123,organization:urn%3Ali%3Aorganization%3A2414183,"
            "action:(organizationContentAuthorizationAction:(actionType:ORGANIC_SHARE_EDIT)))"
        ),
        "ORGANIC_SHARE_DELETE": httpx.URL(
            "https://api.linkedin.com/rest/organizationAuthorizations/"
            "(impersonator:urn%3Ali%3Aperson%3Aabc123,organization:urn%3Ali%3Aorganization%3A2414183,"
            "action:(organizationContentAuthorizationAction:(actionType:ORGANIC_SHARE_DELETE)))"
        ),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url == acl_url:
            return httpx.Response(
                200,
                json={
                    "elements": [
                        {
                            "organization": "urn:li:organization:2414183",
                            "roleAssignee": "urn:li:person:abc123",
                            "role": "CONTENT_ADMINISTRATOR",
                            "state": "APPROVED",
                        },
                        {
                            "organization": "urn:li:organization:2414183",
                            "roleAssignee": "urn:li:person:abc123",
                            "role": "ANALYST",
                            "state": "APPROVED",
                        },
                        {
                            "organization": "urn:li:organization:9999999",
                            "roleAssignee": "urn:li:person:abc123",
                            "role": "ADMINISTRATOR",
                            "state": "APPROVED",
                        },
                    ],
                    "paging": {"count": 100, "start": 0, "links": []},
                },
            )
        if request.url == authorization_urls["ORGANIC_SHARE_CREATE"]:
            return httpx.Response(
                200,
                json={"status": {"com.linkedin.organization.Approved": {}}},
            )
        if request.url == authorization_urls["ORGANIC_SHARE_VIEW_AS_AUTHOR"]:
            return httpx.Response(
                200,
                json={"status": {"com.linkedin.organization.Approved": {}}},
            )
        if request.url == authorization_urls["ORGANIC_SHARE_EDIT"]:
            return httpx.Response(
                200,
                json={"status": {"com.linkedin.organization.Denied": {"reasons": ["NOPE"]}}},
            )
        if request.url == authorization_urls["ORGANIC_SHARE_DELETE"]:
            return httpx.Response(
                200,
                json={"status": {"com.linkedin.organization.Denied": {"reasons": ["NOPE"]}}},
            )
        raise AssertionError(f"Unexpected request: {request.url}")

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.preflight_organization_author(
        role_assignee="urn:li:person:abc123",
        organization="urn:li:organization:2414183",
    )

    assert result == {
        "organization": "urn:li:organization:2414183",
        "roleAssignee": "urn:li:person:abc123",
        "aclApprovedRoles": ["ANALYST", "CONTENT_ADMINISTRATOR"],
        "roles": ["ANALYST", "CONTENT_ADMINISTRATOR"],
        "states": ["APPROVED"],
        "canCreateOrganicPosts": True,
        "canReadOrganizationPosts": True,
        "canEditOrganicPosts": False,
        "canDeleteOrganicPosts": False,
    }
    assert [request.url for request in requests] == [
        acl_url,
        authorization_urls["ORGANIC_SHARE_CREATE"],
        authorization_urls["ORGANIC_SHARE_VIEW_AS_AUTHOR"],
        authorization_urls["ORGANIC_SHARE_EDIT"],
        authorization_urls["ORGANIC_SHARE_DELETE"],
    ]


def test_preflight_organization_author_paginates_until_matching_org_is_found() -> None:
    request_urls: list[httpx.URL] = []
    acl_page_one_url = httpx.URL(
        "https://api.linkedin.com/rest/organizationAcls"
        "?q=roleAssignee&count=100&start=0"
    )
    acl_page_two_url = httpx.URL(
        "https://api.linkedin.com/rest/organizationAcls"
        "?q=roleAssignee&count=100&start=100"
    )
    authorization_urls = [
        httpx.URL(
            "https://api.linkedin.com/rest/organizationAuthorizations/"
            "(impersonator:urn%3Ali%3Aperson%3Aabc123,organization:urn%3Ali%3Aorganization%3A2414183,"
            "action:(organizationContentAuthorizationAction:(actionType:ORGANIC_SHARE_CREATE)))"
        ),
        httpx.URL(
            "https://api.linkedin.com/rest/organizationAuthorizations/"
            "(impersonator:urn%3Ali%3Aperson%3Aabc123,organization:urn%3Ali%3Aorganization%3A2414183,"
            "action:(organizationContentAuthorizationAction:(actionType:ORGANIC_SHARE_VIEW_AS_AUTHOR)))"
        ),
        httpx.URL(
            "https://api.linkedin.com/rest/organizationAuthorizations/"
            "(impersonator:urn%3Ali%3Aperson%3Aabc123,organization:urn%3Ali%3Aorganization%3A2414183,"
            "action:(organizationContentAuthorizationAction:(actionType:ORGANIC_SHARE_EDIT)))"
        ),
        httpx.URL(
            "https://api.linkedin.com/rest/organizationAuthorizations/"
            "(impersonator:urn%3Ali%3Aperson%3Aabc123,organization:urn%3Ali%3Aorganization%3A2414183,"
            "action:(organizationContentAuthorizationAction:(actionType:ORGANIC_SHARE_DELETE)))"
        ),
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        request_urls.append(request.url)
        if request.url == acl_page_one_url:
            return httpx.Response(
                200,
                json={
                    "elements": [
                        {
                            "organization": "urn:li:organization:111",
                            "roleAssignee": "urn:li:person:abc123",
                            "role": "ANALYST",
                            "state": "APPROVED",
                        }
                    ]
                    * 100,
                    "paging": {"count": 100, "start": 0, "links": []},
                },
            )
        if request.url == acl_page_two_url:
            return httpx.Response(
                200,
                json={
                    "elements": [
                        {
                            "organization": "urn:li:organization:2414183",
                            "roleAssignee": "urn:li:person:abc123",
                            "role": "CONTENT_ADMINISTRATOR",
                            "state": "APPROVED",
                        }
                    ],
                    "paging": {"count": 100, "start": 100, "links": []},
                },
            )
        if request.url in authorization_urls:
            return httpx.Response(
                200,
                json={"status": {"com.linkedin.organization.Approved": {}}},
            )
        raise AssertionError(f"Unexpected request: {request.url}")

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.preflight_organization_author(
        role_assignee="urn:li:person:abc123",
        organization="urn:li:organization:2414183",
    )

    assert result["canCreateOrganicPosts"] is True
    assert result["canReadOrganizationPosts"] is True
    assert result["canEditOrganicPosts"] is True
    assert result["canDeleteOrganicPosts"] is True
    assert request_urls == [
        acl_page_one_url,
        acl_page_two_url,
        *authorization_urls,
    ]


def test_preflight_organization_author_accepts_organization_target_shape() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/rest/organizationAcls":
            return httpx.Response(
                200,
                json={
                    "elements": [
                        {
                            "organizationTarget": "urn:li:organization:2414183",
                            "roleAssignee": "urn:li:person:abc123",
                            "role": "CONTENT_ADMINISTRATOR",
                            "state": "APPROVED",
                        }
                    ],
                    "paging": {"count": 100, "start": 0, "links": []},
                },
            )
        if request.url.path.startswith("/rest/organizationAuthorizations/"):
            return httpx.Response(
                200,
                json={"status": {"com.linkedin.organization.Approved": {}}},
            )
        raise AssertionError(f"Unexpected request: {request.url}")

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.preflight_organization_author(
        role_assignee="urn:li:person:abc123",
        organization="urn:li:organization:2414183",
    )

    assert result["aclApprovedRoles"] == ["CONTENT_ADMINISTRATOR"]
    assert result["roles"] == ["CONTENT_ADMINISTRATOR"]
    assert result["canCreateOrganicPosts"] is True


def test_preflight_organization_author_checks_action_endpoint_even_without_acl_match() -> None:
    request_urls: list[httpx.URL] = []
    acl_url = httpx.URL(
        "https://api.linkedin.com/rest/organizationAcls"
        "?q=roleAssignee&count=100&start=0"
    )
    authorization_urls = [
        httpx.URL(
            "https://api.linkedin.com/rest/organizationAuthorizations/"
            "(impersonator:urn%3Ali%3Aperson%3Aabc123,organization:urn%3Ali%3Aorganization%3A2414183,"
            "action:(organizationContentAuthorizationAction:(actionType:ORGANIC_SHARE_CREATE)))"
        ),
        httpx.URL(
            "https://api.linkedin.com/rest/organizationAuthorizations/"
            "(impersonator:urn%3Ali%3Aperson%3Aabc123,organization:urn%3Ali%3Aorganization%3A2414183,"
            "action:(organizationContentAuthorizationAction:(actionType:ORGANIC_SHARE_VIEW_AS_AUTHOR)))"
        ),
        httpx.URL(
            "https://api.linkedin.com/rest/organizationAuthorizations/"
            "(impersonator:urn%3Ali%3Aperson%3Aabc123,organization:urn%3Ali%3Aorganization%3A2414183,"
            "action:(organizationContentAuthorizationAction:(actionType:ORGANIC_SHARE_EDIT)))"
        ),
        httpx.URL(
            "https://api.linkedin.com/rest/organizationAuthorizations/"
            "(impersonator:urn%3Ali%3Aperson%3Aabc123,organization:urn%3Ali%3Aorganization%3A2414183,"
            "action:(organizationContentAuthorizationAction:(actionType:ORGANIC_SHARE_DELETE)))"
        ),
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        request_urls.append(request.url)
        if request.url == acl_url:
            return httpx.Response(
                200,
                json={
                    "elements": [
                        {
                            "organization": "urn:li:organization:9999999",
                            "roleAssignee": "urn:li:person:abc123",
                            "role": "ANALYST",
                            "state": "APPROVED",
                        }
                    ],
                    "paging": {"count": 100, "start": 0, "links": []},
                },
            )
        if request.url in authorization_urls:
            return httpx.Response(
                200,
                json={"status": {"com.linkedin.organization.Denied": {"reasons": ["NOPE"]}}},
            )
        raise AssertionError(f"Unexpected request: {request.url}")

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.preflight_organization_author(
        role_assignee="urn:li:person:abc123",
        organization="urn:li:organization:2414183",
    )

    assert result == {
        "organization": "urn:li:organization:2414183",
        "roleAssignee": "urn:li:person:abc123",
        "aclApprovedRoles": [],
        "roles": [],
        "states": [],
        "canCreateOrganicPosts": False,
        "canReadOrganizationPosts": False,
        "canEditOrganicPosts": False,
        "canDeleteOrganicPosts": False,
    }
    assert request_urls == [acl_url, *authorization_urls]


def test_create_document_post_initializes_upload_uploads_binary_waits_and_creates_post(
    tmp_path: Path,
) -> None:
    document_path = tmp_path / "deck.pdf"
    document_bytes = b"%PDF-1.7 fake"
    document_path.write_bytes(document_bytes)
    requests: list[httpx.Request] = []
    status_polls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal status_polls
        requests.append(request)

        if request.url == httpx.URL("https://api.linkedin.com/rest/documents?action=initializeUpload"):
            payload = json.loads(request.content.decode("utf-8"))
            assert payload == {
                "initializeUploadRequest": {
                    "owner": "urn:li:person:abc123",
                }
            }
            return httpx.Response(
                200,
                json={
                    "value": {
                        "uploadUrl": "https://www.linkedin.com/dms-uploads/example/uploaded-document/0",
                        "document": "urn:li:document:123",
                    }
                },
            )

        if request.url == httpx.URL("https://www.linkedin.com/dms-uploads/example/uploaded-document/0"):
            assert request.method == "PUT"
            assert request.headers["Content-Type"] == "application/pdf"
            assert request.extensions["timeout"]["write"] == 300.0
            assert request.content == document_bytes
            return httpx.Response(201)

        if request.url == httpx.URL("https://api.linkedin.com/rest/documents/urn%3Ali%3Adocument%3A123"):
            status_polls += 1
            if status_polls == 1:
                return httpx.Response(200, json={"id": "urn:li:document:123", "status": "PROCESSING"})
            return httpx.Response(200, json={"id": "urn:li:document:123", "status": "AVAILABLE"})

        if request.url == httpx.URL("https://api.linkedin.com/rest/posts"):
            payload = json.loads(request.content.decode("utf-8"))
            assert payload == {
                "author": "urn:li:person:abc123",
                "commentary": "Hello with document",
                "visibility": "PUBLIC",
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": [],
                },
                "content": {
                    "media": {
                        "id": "urn:li:document:123",
                        "title": "June deck",
                    }
                },
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": False,
            }
            return httpx.Response(
                201,
                headers={"x-restli-id": "urn:li:share:991"},
                json={"id": "urn:li:share:991"},
            )

        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
        video_wait_interval=0.0,
    )

    result = client.create_document_post(
        author="urn:li:person:abc123",
        commentary="Hello with document",
        document_path=document_path,
        title="June deck",
    )

    assert result.post_id == "urn:li:share:991"
    assert [request.url for request in requests] == [
        httpx.URL("https://api.linkedin.com/rest/documents?action=initializeUpload"),
        httpx.URL("https://www.linkedin.com/dms-uploads/example/uploaded-document/0"),
        httpx.URL("https://api.linkedin.com/rest/documents/urn%3Ali%3Adocument%3A123"),
        httpx.URL("https://api.linkedin.com/rest/documents/urn%3Ali%3Adocument%3A123"),
        httpx.URL("https://api.linkedin.com/rest/posts"),
    ]


def test_create_document_post_from_existing_asset_uses_media_urn() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/posts")
        payload = json.loads(request.content.decode("utf-8"))
        assert payload == {
            "author": "urn:li:person:abc123",
            "commentary": "Hello with reused document",
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "content": {
                "media": {
                    "id": "urn:li:document:123",
                    "title": "June deck",
                }
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        return httpx.Response(
            201,
            headers={"x-restli-id": "urn:li:share:992"},
            json={"id": "urn:li:share:992"},
        )

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.create_document_post_from_asset(
        author="urn:li:person:abc123",
        commentary="Hello with reused document",
        document_urn="urn:li:document:123",
        title="June deck",
    )

    assert result.post_id == "urn:li:share:992"


def test_create_article_post_uses_article_content() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/posts")
        payload = json.loads(request.content.decode("utf-8"))
        assert payload == {
            "author": "urn:li:person:abc123",
            "commentary": "Worth reading",
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "content": {
                "article": {
                    "source": "https://example.com/post",
                    "title": "Deep systems",
                    "description": "A long read",
                    "thumbnail": "urn:li:image:777",
                }
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        return httpx.Response(
            201,
            headers={"x-restli-id": "urn:li:share:993"},
            json={"id": "urn:li:share:993"},
        )

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.create_article_post(
        author="urn:li:person:abc123",
        commentary="Worth reading",
        article_url="https://example.com/post",
        title="Deep systems",
        description="A long read",
        thumbnail_image_urn="urn:li:image:777",
    )

    assert result.post_id == "urn:li:share:993"


def test_create_article_post_can_upload_thumbnail_image(tmp_path: Path) -> None:
    thumbnail_path = tmp_path / "thumb.png"
    thumbnail_bytes = b"thumb"
    thumbnail_path.write_bytes(thumbnail_bytes)
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)

        if request.url == httpx.URL("https://api.linkedin.com/rest/images?action=initializeUpload"):
            return httpx.Response(
                200,
                json={
                    "value": {
                        "image": "urn:li:image:777",
                        "uploadUrl": "https://www.linkedin.com/dms-uploads/example/uploaded-image/0",
                    }
                },
            )
        if request.url == httpx.URL("https://www.linkedin.com/dms-uploads/example/uploaded-image/0"):
            assert request.method == "PUT"
            assert request.content == thumbnail_bytes
            return httpx.Response(201)
        if request.url == httpx.URL("https://api.linkedin.com/rest/posts"):
            payload = json.loads(request.content.decode("utf-8"))
            assert payload["content"]["article"]["thumbnail"] == "urn:li:image:777"
            return httpx.Response(201, headers={"x-restli-id": "urn:li:share:993"}, json={"id": "urn:li:share:993"})
        raise AssertionError(f"unexpected request: {request.method} {request.url}")

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.create_article_post(
        author="urn:li:person:abc123",
        commentary="Worth reading",
        article_url="https://example.com/post",
        title="Deep systems",
        thumbnail_image_path=thumbnail_path,
    )

    assert result.post_id == "urn:li:share:993"


def test_create_multi_image_post_uploads_each_image_and_creates_post(tmp_path: Path) -> None:
    first_image = tmp_path / "one.png"
    second_image = tmp_path / "two.png"
    first_image.write_bytes(b"one")
    second_image.write_bytes(b"two")
    requests: list[httpx.Request] = []
    initialized_images = iter(
        [
            (
                "https://www.linkedin.com/dms-uploads/example/uploaded-image/0",
                "urn:li:image:123",
            ),
            (
                "https://www.linkedin.com/dms-uploads/example/uploaded-image/1",
                "urn:li:image:456",
            ),
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)

        if request.url == httpx.URL("https://api.linkedin.com/rest/images?action=initializeUpload"):
            upload_url, image_urn = next(initialized_images)
            return httpx.Response(
                200,
                json={"value": {"uploadUrl": upload_url, "image": image_urn}},
            )

        if request.url == httpx.URL("https://www.linkedin.com/dms-uploads/example/uploaded-image/0"):
            assert request.method == "PUT"
            assert request.content == b"one"
            return httpx.Response(201)

        if request.url == httpx.URL("https://www.linkedin.com/dms-uploads/example/uploaded-image/1"):
            assert request.method == "PUT"
            assert request.content == b"two"
            return httpx.Response(201)

        if request.url == httpx.URL("https://api.linkedin.com/rest/posts"):
            payload = json.loads(request.content.decode("utf-8"))
            assert payload == {
                "author": "urn:li:person:abc123",
                "commentary": "Photo dump",
                "visibility": "PUBLIC",
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": [],
                },
                "content": {
                    "multiImage": {
                        "images": [
                            {"id": "urn:li:image:123"},
                            {"id": "urn:li:image:456"},
                        ]
                    }
                },
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": False,
            }
            return httpx.Response(
                201,
                headers={"x-restli-id": "urn:li:share:994"},
                json={"id": "urn:li:share:994"},
            )

        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.create_multi_image_post(
        author="urn:li:person:abc123",
        commentary="Photo dump",
        image_paths=[first_image, second_image],
    )

    assert result.post_id == "urn:li:share:994"


def test_create_multi_image_post_supports_alt_text_for_uploaded_files(tmp_path: Path) -> None:
    first_image = tmp_path / "one.png"
    second_image = tmp_path / "two.png"
    first_image.write_bytes(b"one")
    second_image.write_bytes(b"two")
    requests: list[httpx.Request] = []
    initialized_images = iter(
        [
            (
                "https://www.linkedin.com/dms-uploads/example/uploaded-image/0",
                "urn:li:image:123",
            ),
            (
                "https://www.linkedin.com/dms-uploads/example/uploaded-image/1",
                "urn:li:image:456",
            ),
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url == httpx.URL("https://api.linkedin.com/rest/images?action=initializeUpload"):
            upload_url, image_urn = next(initialized_images)
            return httpx.Response(
                200,
                json={"value": {"uploadUrl": upload_url, "image": image_urn}},
            )
        if request.url in {
            httpx.URL("https://www.linkedin.com/dms-uploads/example/uploaded-image/0"),
            httpx.URL("https://www.linkedin.com/dms-uploads/example/uploaded-image/1"),
        }:
            return httpx.Response(201)
        if request.url == httpx.URL("https://api.linkedin.com/rest/posts"):
            payload = json.loads(request.content.decode("utf-8"))
            assert payload["content"]["multiImage"]["images"] == [
                {"id": "urn:li:image:123", "altText": "First image"},
                {"id": "urn:li:image:456", "altText": "Second image"},
            ]
            return httpx.Response(201, headers={"x-restli-id": "urn:li:share:994"}, json={"id": "urn:li:share:994"})
        raise AssertionError(f"unexpected request: {request.method} {request.url}")

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.create_multi_image_post(
        author="urn:li:person:abc123",
        commentary="Photo dump",
        image_paths=[first_image, second_image],
        alt_texts=["First image", "Second image"],
    )

    assert result.post_id == "urn:li:share:994"
    assert [request.url for request in requests] == [
        httpx.URL("https://api.linkedin.com/rest/images?action=initializeUpload"),
        httpx.URL("https://www.linkedin.com/dms-uploads/example/uploaded-image/0"),
        httpx.URL("https://api.linkedin.com/rest/images?action=initializeUpload"),
        httpx.URL("https://www.linkedin.com/dms-uploads/example/uploaded-image/1"),
        httpx.URL("https://api.linkedin.com/rest/posts"),
    ]


def test_create_video_post_uploads_captions_and_thumbnail_when_requested(
    tmp_path: Path,
) -> None:
    video_path = tmp_path / "clip.mp4"
    captions_path = tmp_path / "clip.vtt"
    thumbnail_path = tmp_path / "thumb.png"
    video_path.write_bytes(b"abcdefgh")
    captions_bytes = b"WEBVTT\n\n00:00.000 --> 00:01.000\nHello\n"
    captions_path.write_bytes(captions_bytes)
    thumbnail_bytes = b"thumb"
    thumbnail_path.write_bytes(thumbnail_bytes)
    requests: list[httpx.Request] = []
    status_polls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal status_polls
        requests.append(request)

        if request.url == httpx.URL("https://api.linkedin.com/rest/videos?action=initializeUpload"):
            payload = json.loads(request.content.decode("utf-8"))
            assert payload == {
                "initializeUploadRequest": {
                    "owner": "urn:li:person:abc123",
                    "fileSizeBytes": 8,
                    "uploadCaptions": True,
                    "uploadThumbnail": True,
                }
            }
            return httpx.Response(
                200,
                json={
                    "value": {
                        "video": "urn:li:video:123",
                        "uploadToken": "upload-token",
                        "uploadInstructions": [
                            {
                                "uploadUrl": "https://www.linkedin.com/dms-uploads/example/uploaded-video/0",
                                "firstByte": 0,
                                "lastByte": 7,
                            }
                        ],
                        "captionsUploadUrl": "https://www.linkedin.com/dms-uploads/example/uploaded-video/captions",
                        "thumbnailUploadUrl": "https://www.linkedin.com/dms-uploads/example/uploaded-video/thumbnail",
                    }
                },
            )

        if request.url == httpx.URL("https://www.linkedin.com/dms-uploads/example/uploaded-video/0"):
            assert request.method == "PUT"
            assert request.content == b"abcdefgh"
            return httpx.Response(200, headers={"ETag": '/ambry-videoei/signedId/part-1.bin'})

        if request.url == httpx.URL("https://www.linkedin.com/dms-uploads/example/uploaded-video/captions"):
            assert request.method == "PUT"
            assert request.headers["Content-Type"] == "text/vtt"
            assert request.content == captions_bytes
            return httpx.Response(201)

        if request.url == httpx.URL("https://www.linkedin.com/dms-uploads/example/uploaded-video/thumbnail"):
            assert request.method == "PUT"
            assert request.headers["Content-Type"] == "image/png"
            assert request.content == thumbnail_bytes
            return httpx.Response(201)

        if request.url == httpx.URL("https://api.linkedin.com/rest/videos?action=finalizeUpload"):
            return httpx.Response(200, json={})

        if request.url == httpx.URL("https://api.linkedin.com/rest/videos/urn%3Ali%3Avideo%3A123"):
            status_polls += 1
            if status_polls == 1:
                return httpx.Response(200, json={"id": "urn:li:video:123", "status": "PROCESSING"})
            return httpx.Response(200, json={"id": "urn:li:video:123", "status": "AVAILABLE"})

        if request.url == httpx.URL("https://api.linkedin.com/rest/posts"):
            payload = json.loads(request.content.decode("utf-8"))
            assert payload["content"]["media"]["id"] == "urn:li:video:123"
            return httpx.Response(
                201,
                headers={"x-restli-id": "urn:li:share:995"},
                json={"id": "urn:li:share:995"},
            )

        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
        video_wait_interval=0.0,
    )

    result = client.create_video_post(
        author="urn:li:person:abc123",
        commentary="Hello with video",
        video_path=video_path,
        title="Linus clip",
        captions_path=captions_path,
        thumbnail_path=thumbnail_path,
    )

    assert result.post_id == "urn:li:share:995"


def test_create_poll_post_uses_poll_content() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/posts")
        payload = json.loads(request.content.decode("utf-8"))
        assert payload == {
            "author": "urn:li:person:abc123",
            "commentary": "Vote now",
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
            "content": {
                "poll": {
                    "question": "Favorite color?",
                    "options": [{"text": "Red"}, {"text": "Blue"}],
                    "settings": {"duration": "THREE_DAYS"},
                }
            },
        }
        return httpx.Response(201, headers={"x-restli-id": "urn:li:share:996"}, json={"id": "urn:li:share:996"})

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.create_poll_post(
        author="urn:li:person:abc123",
        commentary="Vote now",
        question="Favorite color?",
        options=["Red", "Blue"],
        duration="THREE_DAYS",
    )

    assert result.post_id == "urn:li:share:996"


def test_create_multi_image_post_from_assets_supports_alt_text() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/posts")
        payload = json.loads(request.content.decode("utf-8"))
        assert payload == {
            "author": "urn:li:person:abc123",
            "commentary": "Photo dump",
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
            "content": {
                "multiImage": {
                    "images": [
                        {"id": "urn:li:image:123", "altText": "First image"},
                        {"id": "urn:li:image:456", "altText": "Second image"},
                    ]
                }
            },
        }
        return httpx.Response(201, headers={"x-restli-id": "urn:li:share:997"}, json={"id": "urn:li:share:997"})

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.create_multi_image_post_from_assets(
        author="urn:li:person:abc123",
        commentary="Photo dump",
        image_urns=["urn:li:image:123", "urn:li:image:456"],
        alt_texts=["First image", "Second image"],
    )

    assert result.post_id == "urn:li:share:997"


def test_create_multi_image_post_from_assets_requires_between_two_and_twenty_images() -> None:
    client = LinkedInClient(
        access_token="test-token",
        transport=httpx.MockTransport(lambda request: httpx.Response(500)),
    )

    with pytest.raises(ValueError, match="2 to 20"):
        client.create_multi_image_post_from_assets(
            author="urn:li:person:abc123",
            commentary="Hello",
            image_urns=["urn:li:image:1"],
        )

    with pytest.raises(ValueError, match="2 to 20"):
        client.create_multi_image_post_from_assets(
            author="urn:li:person:abc123",
            commentary="Hello",
            image_urns=[f"urn:li:image:{index}" for index in range(21)],
        )


def test_list_organization_access_by_organization_uses_official_rest_finder() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL(
            "https://api.linkedin.com/rest/organizationAcls"
            "?q=organization&organization=urn%3Ali%3Aorganization%3A2414183"
            "&count=100&start=0&role=ADMINISTRATOR&state=APPROVED"
        )
        assert request.headers["X-RestLi-Method"] == "FINDER"
        return httpx.Response(200, json={"elements": [{"roleAssignee": "urn:li:person:abc"}], "paging": {"count": 100, "start": 0, "links": []}})

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.list_organization_access_by_organization(
        organization="urn:li:organization:2414183",
        count=100,
        start=0,
        role="ADMINISTRATOR",
        state="APPROVED",
    )

    assert result["elements"][0]["roleAssignee"] == "urn:li:person:abc"


def test_preflight_organization_author_ignores_non_approved_non_posting_roles() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/rest/organizationAcls":
            return httpx.Response(
                200,
                json={
                    "elements": [
                        {
                            "organization": "urn:li:organization:2414183",
                            "roleAssignee": "urn:li:person:abc123",
                            "role": "ANALYST",
                            "state": "APPROVED",
                        },
                        {
                            "organization": "urn:li:organization:2414183",
                            "roleAssignee": "urn:li:person:abc123",
                            "role": "CONTENT_ADMINISTRATOR",
                            "state": "REVOKED",
                        },
                    ],
                    "paging": {"count": 100, "start": 0, "links": []},
                },
            )
        if request.url.path.startswith("/rest/organizationAuthorizations/"):
            return httpx.Response(
                200,
                json={"status": {"com.linkedin.organization.Denied": {"reasons": ["NOPE"]}}},
            )
        raise AssertionError(f"Unexpected request: {request.url}")

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.preflight_organization_author(
        role_assignee="urn:li:person:abc123",
        organization="urn:li:organization:2414183",
    )

    assert result["aclApprovedRoles"] == ["ANALYST"]
    assert result["canCreateOrganicPosts"] is False
    assert result["canReadOrganizationPosts"] is False


def test_get_comment_uses_social_actions_comment_endpoint() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/socialActions/urn%3Ali%3Ashare%3A123/comments/456")
        return httpx.Response(200, json={"id": "456", "message": {"text": "Hello"}})

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.get_comment("urn:li:share:123", "456")

    assert result["id"] == "456"


def test_list_comments_uses_social_actions_comments_collection() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL(
            "https://api.linkedin.com/rest/socialActions/urn%3Ali%3Ashare%3A123/comments?count=25&start=10"
        )
        return httpx.Response(200, json={"elements": [{"id": "456"}], "paging": {"count": 25, "start": 10, "links": []}})

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.list_comments(
        target_urn="urn:li:share:123",
        count=25,
        start=10,
    )

    assert result["elements"][0]["id"] == "456"


def test_batch_get_comments_uses_restli_batch_get() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL(
            "https://api.linkedin.com/rest/socialActions/urn%3Ali%3Ashare%3A123/comments?ids=List(456,789)"
        )
        assert request.headers["X-RestLi-Method"] == "BATCH_GET"
        return httpx.Response(200, json={"results": {"456": {"id": "456"}, "789": {"id": "789"}}})

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.batch_get_comments("urn:li:share:123", ["456", "789"])

    assert result["results"]["789"]["id"] == "789"


def test_create_comment_uses_social_actions_collection() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/socialActions/urn%3Ali%3Ashare%3A123/comments")
        payload = json.loads(request.content.decode("utf-8"))
        assert payload == {
            "actor": "urn:li:person:abc",
            "object": "urn:li:share:123",
            "message": {
                "text": "Hello world",
                "attributes": [{"start": 0, "length": 5, "value": {"member": "urn:li:person:abc"}}],
            },
            "content": [{"entity": {"image": "urn:li:image:123"}}],
        }
        return httpx.Response(201, json={"id": "456", "message": {"text": "Hello world"}})

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.create_comment(
        target_urn="urn:li:share:123",
        actor="urn:li:person:abc",
        text="Hello world",
        attributes=[{"start": 0, "length": 5, "value": {"member": "urn:li:person:abc"}}],
        content_image_urn="urn:li:image:123",
    )

    assert result["id"] == "456"


def test_create_comment_reply_uses_parent_comment_in_path_and_root_object() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url == httpx.URL(
            "https://api.linkedin.com/rest/socialActions/urn%3Ali%3Acomment%3A%28urn%3Ali%3Ashare%3A123%2C456%29/comments"
        )
        payload = json.loads(request.content.decode("utf-8"))
        assert payload == {
            "actor": "urn:li:person:abc",
            "object": "urn:li:share:123",
            "message": {"text": "Nested reply"},
            "parentComment": "urn:li:comment:(urn:li:share:123,456)",
        }
        return httpx.Response(201, json={"id": "789", "message": {"text": "Nested reply"}})

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.create_comment(
        target_urn="urn:li:share:123",
        actor="urn:li:person:abc",
        text="Nested reply",
        parent_comment="urn:li:comment:(urn:li:share:123,456)",
    )

    assert result["id"] == "789"


def test_create_comment_reply_rejects_content_entities() -> None:
    client = LinkedInClient(
        access_token="test-token",
        transport=httpx.MockTransport(lambda request: httpx.Response(500)),
    )

    with pytest.raises(ValueError, match="Replies do not support content entities"):
        client.create_comment(
            target_urn="urn:li:share:123",
            actor="urn:li:person:abc",
            text="Nested reply",
            parent_comment="urn:li:comment:(urn:li:share:123,456)",
            content_image_urn="urn:li:image:123",
        )


def test_update_comment_uses_partial_update() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url == httpx.URL(
            "https://api.linkedin.com/rest/socialActions/urn%3Ali%3Ashare%3A123/comments/456?actor=urn%3Ali%3Aorganization%3A123"
        )
        assert request.headers["X-RestLi-Method"] == "PARTIAL_UPDATE"
        payload = json.loads(request.content.decode("utf-8"))
        assert payload == {
            "patch": {
                "message": {
                    "$set": {
                        "text": "Updated comment",
                        "attributes": [{"start": 0, "length": 7, "value": {"member": "urn:li:person:def"}}],
                    }
                }
            }
        }
        return httpx.Response(204)

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    client.update_comment(
        target_urn="urn:li:share:123",
        comment_id="456",
        text="Updated comment",
        actor="urn:li:organization:123",
        attributes=[{"start": 0, "length": 7, "value": {"member": "urn:li:person:def"}}],
    )


def test_delete_comment_uses_social_actions_comment_endpoint() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url == httpx.URL(
            "https://api.linkedin.com/rest/socialActions/urn%3Ali%3Ashare%3A123/comments/456?actor=urn%3Ali%3Aorganization%3A123"
        )
        return httpx.Response(204)

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    client.delete_comment(
        target_urn="urn:li:share:123",
        comment_id="456",
        actor="urn:li:organization:123",
    )


def test_create_reaction_uses_rest_reactions_api() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/reactions?actor=urn%3Ali%3Aperson%3Aabc")
        payload = json.loads(request.content.decode("utf-8"))
        assert payload == {"root": "urn:li:share:123", "reactionType": "LIKE"}
        return httpx.Response(201, json={"id": "urn:li:reaction:(urn:li:person:abc,urn:li:share:123)"})

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.create_reaction(
        actor="urn:li:person:abc",
        root="urn:li:share:123",
        reaction_type="LIKE",
    )

    assert result["id"].startswith("urn:li:reaction:")


def test_get_reaction_uses_rest_reactions_entity_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL(
            "https://api.linkedin.com/rest/reactions/(actor:urn%3Ali%3Aperson%3Aabc,entity:urn%3Ali%3Ashare%3A123)"
        )
        return httpx.Response(200, json={"id": "urn:li:reaction:(urn:li:person:abc,urn:li:share:123)"})

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.get_reaction(
        actor="urn:li:person:abc",
        entity="urn:li:share:123",
    )

    assert result["id"].startswith("urn:li:reaction:")


def test_batch_get_reactions_uses_restli_batch_get() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL(
            "https://api.linkedin.com/rest/reactions"
            "?ids=List((actor:urn%3Ali%3Aperson%3Aabc,entity:urn%3Ali%3Ashare%3A123),(actor:urn%3Ali%3Aorganization%3A456,entity:urn%3Ali%3Acomment%3A%28urn%3Ali%3Ashare%3A123%2C789%29))"
        )
        assert request.headers["X-RestLi-Method"] == "BATCH_GET"
        return httpx.Response(
            200,
            json={
                "results": {
                    "(actor:urn%3Ali%3Aperson%3Aabc,entity:urn%3Ali%3Ashare%3A123)": {"id": "urn:li:reaction:(urn:li:person:abc,urn:li:share:123)"}
                }
            },
        )

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.batch_get_reactions(
        [
            ("urn:li:person:abc", "urn:li:share:123"),
            ("urn:li:organization:456", "urn:li:comment:(urn:li:share:123,789)"),
        ]
    )

    assert next(iter(result["results"].values()))["id"].startswith("urn:li:reaction:")


def test_list_reactions_uses_entity_finder() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL(
            "https://api.linkedin.com/rest/reactions/(entity:urn%3Ali%3Ashare%3A123)"
            "?q=entity&sort=(value:RELEVANCE)&count=25&start=10"
        )
        assert request.headers["X-RestLi-Method"] == "FINDER"
        return httpx.Response(200, json={"elements": [{"id": "urn:li:reaction:(urn:li:person:abc,urn:li:share:123)"}]})

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.list_reactions(
        entity="urn:li:share:123",
        count=25,
        start=10,
        sort="RELEVANCE",
    )

    assert result["elements"][0]["id"].startswith("urn:li:reaction:")


def test_delete_reaction_uses_rest_delete() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url == httpx.URL(
            "https://api.linkedin.com/rest/reactions/(actor:urn%3Ali%3Aperson%3Aabc,entity:urn%3Ali%3Ashare%3A123)"
        )
        return httpx.Response(204)

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    client.delete_reaction(
        actor="urn:li:person:abc",
        entity="urn:li:share:123",
    )


def test_get_social_metadata_uses_rest_social_metadata_api() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/socialMetadata/urn%3Ali%3Ashare%3A123")
        return httpx.Response(200, json={"entity": "urn:li:share:123", "commentsState": "OPEN"})

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.get_social_metadata("urn:li:share:123")

    assert result["commentsState"] == "OPEN"


def test_batch_get_social_metadata_uses_restli_batch_get() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL(
            "https://api.linkedin.com/rest/socialMetadata"
            "?ids=List(urn%3Ali%3Ashare%3A123,urn%3Ali%3Acomment%3A%28urn%3Ali%3Ashare%3A123%2C456%29)"
        )
        assert request.headers["X-RestLi-Method"] == "BATCH_GET"
        return httpx.Response(
            200,
            json={
                "results": {
                    "urn:li:share:123": {"commentsState": "OPEN"},
                    "urn:li:comment:(urn:li:share:123,456)": {"commentsState": "CLOSED"},
                }
            },
        )

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.batch_get_social_metadata(
        ["urn:li:share:123", "urn:li:comment:(urn:li:share:123,456)"]
    )

    assert result["results"]["urn:li:comment:(urn:li:share:123,456)"]["commentsState"] == "CLOSED"


def test_update_social_metadata_comments_state_uses_partial_update() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url == httpx.URL(
            "https://api.linkedin.com/rest/socialMetadata/urn%3Ali%3Ashare%3A123?actor=urn%3Ali%3Aperson%3Aabc"
        )
        assert request.headers["X-RestLi-Method"] == "PARTIAL_UPDATE"
        payload = json.loads(request.content.decode("utf-8"))
        assert payload == {"patch": {"$set": {"commentsState": "CLOSED"}}}
        return httpx.Response(204)

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    client.update_social_metadata_comments_state(
        entity_urn="urn:li:share:123",
        actor="urn:li:person:abc",
        comments_state="CLOSED",
    )


def test_update_comment_rejects_comment_urn_target() -> None:
    client = LinkedInClient(
        access_token="test-token",
        transport=httpx.MockTransport(lambda request: httpx.Response(500)),
    )

    with pytest.raises(ValueError, match="share or ugcPost URN"):
        client.update_comment(
            target_urn="urn:li:comment:(urn:li:share:123,456)",
            comment_id="456",
            text="Updated",
        )


def test_delete_comment_rejects_comment_urn_target() -> None:
    client = LinkedInClient(
        access_token="test-token",
        transport=httpx.MockTransport(lambda request: httpx.Response(500)),
    )

    with pytest.raises(ValueError, match="share or ugcPost URN"):
        client.delete_comment(
            target_urn="urn:li:comment:(urn:li:share:123,456)",
            comment_id="456",
        )


def test_update_social_metadata_comments_state_rejects_comment_urn_target() -> None:
    client = LinkedInClient(
        access_token="test-token",
        transport=httpx.MockTransport(lambda request: httpx.Response(500)),
    )

    with pytest.raises(ValueError, match="thread URN"):
        client.update_social_metadata_comments_state(
            entity_urn="urn:li:comment:(urn:li:share:123,456)",
            actor="urn:li:person:abc",
            comments_state="CLOSED",
        )

def test_delete_post_uses_rest_posts_api() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/posts/urn%3Ali%3Ashare%3A987")
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["Linkedin-Version"] == "202505"
        assert request.headers["X-RestLi-Method"] == "DELETE"
        return httpx.Response(204)

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    client.delete_post("urn:li:share:987")


def test_update_post_uses_restli_partial_update() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/posts/urn%3Ali%3Ashare%3A987")
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["Linkedin-Version"] == "202505"
        assert request.headers["X-RestLi-Method"] == "PARTIAL_UPDATE"
        payload = json.loads(request.content.decode("utf-8"))
        assert payload == {
            "patch": {
                "$set": {
                    "commentary": "Edited text",
                    "contentCallToActionLabel": "LEARN_MORE",
                    "contentLandingPage": "https://example.com",
                }
            }
        }
        return httpx.Response(204)

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    client.update_post(
        "urn:li:share:987",
        commentary="Edited text",
        content_call_to_action_label="LEARN_MORE",
        content_landing_page="https://example.com",
    )


def test_update_post_can_set_lifecycle_state() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/posts/urn%3Ali%3Ashare%3A987")
        assert request.headers["X-RestLi-Method"] == "PARTIAL_UPDATE"
        payload = json.loads(request.content.decode("utf-8"))
        assert payload == {"patch": {"$set": {"lifecycleState": "PUBLISHED"}}}
        return httpx.Response(204)

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    client.update_post(
        "urn:li:share:987",
        lifecycle_state="PUBLISHED",
    )


def test_get_image_uses_rest_images_api() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/images/urn%3Ali%3Aimage%3A123")
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["Linkedin-Version"] == "202505"
        return httpx.Response(200, json={"id": "urn:li:image:123", "status": "AVAILABLE"})

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.get_image("urn:li:image:123")

    assert result["id"] == "urn:li:image:123"


def test_batch_get_images_uses_restli_batch_get() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL(
            "https://api.linkedin.com/rest/images"
            "?ids=List(urn%3Ali%3Aimage%3A123,urn%3Ali%3Aimage%3A456)"
        )
        assert request.headers["X-RestLi-Method"] == "BATCH_GET"
        return httpx.Response(
            200,
            json={
                "results": {
                    "urn:li:image:123": {"id": "urn:li:image:123"},
                    "urn:li:image:456": {"id": "urn:li:image:456"},
                }
            },
        )

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.batch_get_images(["urn:li:image:123", "urn:li:image:456"])

    assert result["results"]["urn:li:image:456"]["id"] == "urn:li:image:456"


def test_get_video_uses_rest_videos_api() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/videos/urn%3Ali%3Avideo%3A123")
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["Linkedin-Version"] == "202505"
        return httpx.Response(200, json={"id": "urn:li:video:123", "status": "AVAILABLE"})

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.get_video("urn:li:video:123")

    assert result["id"] == "urn:li:video:123"


def test_batch_get_videos_uses_restli_batch_get() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL(
            "https://api.linkedin.com/rest/videos"
            "?ids=List(urn%3Ali%3Avideo%3A123,urn%3Ali%3Avideo%3A456)"
        )
        assert request.headers["X-RestLi-Method"] == "BATCH_GET"
        return httpx.Response(
            200,
            json={
                "results": {
                    "urn:li:video:123": {"id": "urn:li:video:123"},
                    "urn:li:video:456": {"id": "urn:li:video:456"},
                }
            },
        )

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.batch_get_videos(["urn:li:video:123", "urn:li:video:456"])

    assert result["results"]["urn:li:video:123"]["id"] == "urn:li:video:123"


def test_create_image_post_from_existing_asset_uses_media_urn() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/posts")
        payload = json.loads(request.content.decode("utf-8"))
        assert payload == {
            "author": "urn:li:person:abc123",
            "commentary": "Hello with reused image",
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "content": {
                "media": {
                    "id": "urn:li:image:123",
                    "altText": "Bitdevs banner",
                }
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        return httpx.Response(
            201,
            headers={"x-restli-id": "urn:li:share:456"},
            json={"id": "urn:li:share:456"},
        )

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.create_image_post_from_asset(
        author="urn:li:person:abc123",
        commentary="Hello with reused image",
        image_urn="urn:li:image:123",
        alt_text="Bitdevs banner",
    )

    assert result.post_id == "urn:li:share:456"


def test_create_video_post_from_existing_asset_uses_media_urn() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/posts")
        payload = json.loads(request.content.decode("utf-8"))
        assert payload == {
            "author": "urn:li:person:abc123",
            "commentary": "Hello with reused video",
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "content": {
                "media": {
                    "id": "urn:li:video:123",
                    "title": "Linus clip",
                }
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        return httpx.Response(
            201,
            headers={"x-restli-id": "urn:li:share:654"},
            json={"id": "urn:li:share:654"},
        )

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.create_video_post_from_asset(
        author="urn:li:person:abc123",
        commentary="Hello with reused video",
        video_urn="urn:li:video:123",
        title="Linus clip",
    )

    assert result.post_id == "urn:li:share:654"


def test_get_userinfo_uses_linkedin_oidc_endpoint() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL("https://api.linkedin.com/v2/userinfo")
        assert request.headers["Authorization"] == "Bearer test-token"
        return httpx.Response(
            200,
            json={
                "sub": "abc123",
                "name": "Breno Brito",
                "email": "breno@example.com",
            },
        )

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.get_userinfo()

    assert result["sub"] == "abc123"


def test_get_profile_identity_uses_profile_api_me_endpoint() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL("https://api.linkedin.com/v2/me")
        assert request.headers["Authorization"] == "Bearer test-token"
        return httpx.Response(200, json={"id": "abc123", "localizedFirstName": "Breno"})

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.get_profile_identity()

    assert result["id"] == "abc123"


def test_create_text_post_raises_clear_error_on_api_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Invalid access token"})

    client = LinkedInClient(
        access_token="bad-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(LinkedInApiError, match="401"):
        client.create_text_post(
            author="urn:li:person:abc123",
            commentary="Hello from tests",
        )


def test_create_image_post_initializes_upload_uploads_binary_and_creates_post(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "banner.png"
    image_bytes = b"\x89PNG\r\n\x1a\nfakepng"
    image_path.write_bytes(image_bytes)
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)

        if request.url == httpx.URL("https://api.linkedin.com/rest/images?action=initializeUpload"):
            payload = json.loads(request.content.decode("utf-8"))
            assert payload == {
                "initializeUploadRequest": {
                    "owner": "urn:li:person:abc123",
                }
            }
            return httpx.Response(
                200,
                json={
                    "value": {
                        "uploadUrl": "https://www.linkedin.com/dms-uploads/example/uploaded-image/0",
                        "image": "urn:li:image:123",
                    }
                },
            )

        if request.url == httpx.URL("https://www.linkedin.com/dms-uploads/example/uploaded-image/0"):
            assert request.method == "PUT"
            assert request.headers["Content-Type"] == "image/png"
            assert request.extensions["timeout"]["write"] == 300.0
            assert request.content == image_bytes
            return httpx.Response(201)

        if request.url == httpx.URL("https://api.linkedin.com/rest/posts"):
            payload = json.loads(request.content.decode("utf-8"))
            assert payload == {
                "author": "urn:li:person:abc123",
                "commentary": "Hello with image",
                "visibility": "PUBLIC",
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": [],
                },
                "content": {
                    "media": {
                        "id": "urn:li:image:123",
                        "altText": "Bitdevs banner",
                    }
                },
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": False,
            }
            return httpx.Response(
                201,
                headers={"x-restli-id": "urn:li:share:456"},
                json={"id": "urn:li:share:456"},
            )

        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.create_image_post(
        author="urn:li:person:abc123",
        commentary="Hello with image",
        image_path=image_path,
        alt_text="Bitdevs banner",
    )

    assert result.post_id == "urn:li:share:456"
    assert result.response["id"] == "urn:li:share:456"
    assert [request.url for request in requests] == [
        httpx.URL("https://api.linkedin.com/rest/images?action=initializeUpload"),
        httpx.URL("https://www.linkedin.com/dms-uploads/example/uploaded-image/0"),
        httpx.URL("https://api.linkedin.com/rest/posts"),
    ]


def test_create_image_post_raises_clear_error_when_upload_init_fails(tmp_path: Path) -> None:
    image_path = tmp_path / "banner.png"
    image_path.write_bytes(b"fakepng")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url == httpx.URL("https://api.linkedin.com/rest/images?action=initializeUpload"):
            return httpx.Response(403, json={"message": "Not enough permissions"})
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(LinkedInApiError, match="403"):
        client.create_image_post(
            author="urn:li:person:abc123",
            commentary="Hello with image",
            image_path=image_path,
        )


def test_create_video_post_initializes_upload_uploads_parts_finalizes_and_creates_post(
    tmp_path: Path,
) -> None:
    video_path = tmp_path / "clip.mp4"
    video_bytes = b"abcdefgh"
    video_path.write_bytes(video_bytes)
    requests: list[httpx.Request] = []
    status_polls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal status_polls
        requests.append(request)

        if request.url == httpx.URL("https://api.linkedin.com/rest/videos?action=initializeUpload"):
            payload = json.loads(request.content.decode("utf-8"))
            assert payload == {
                "initializeUploadRequest": {
                    "owner": "urn:li:person:abc123",
                    "fileSizeBytes": 8,
                    "uploadCaptions": False,
                    "uploadThumbnail": False,
                }
            }
            return httpx.Response(
                200,
                json={
                    "value": {
                        "video": "urn:li:video:123",
                        "uploadToken": "upload-token",
                        "uploadInstructions": [
                            {
                                "uploadUrl": "https://www.linkedin.com/dms-uploads/example/uploaded-video/0",
                                "firstByte": 0,
                                "lastByte": 3,
                            },
                            {
                                "uploadUrl": "https://www.linkedin.com/dms-uploads/example/uploaded-video/1",
                                "firstByte": 4,
                                "lastByte": 7,
                            },
                        ],
                    }
                },
            )

        if request.url == httpx.URL("https://www.linkedin.com/dms-uploads/example/uploaded-video/0"):
            assert request.method == "PUT"
            assert request.headers["Content-Type"] == "application/octet-stream"
            assert request.extensions["timeout"]["write"] == 300.0
            assert request.content == b"abcd"
            return httpx.Response(200, headers={"ETag": '/ambry-videoei/signedId/part-1.bin'})

        if request.url == httpx.URL("https://www.linkedin.com/dms-uploads/example/uploaded-video/1"):
            assert request.method == "PUT"
            assert request.headers["Content-Type"] == "application/octet-stream"
            assert request.extensions["timeout"]["write"] == 300.0
            assert request.content == b"efgh"
            return httpx.Response(200, headers={"ETag": '/ambry-videoei/signedId/part-2.bin'})

        if request.url == httpx.URL("https://api.linkedin.com/rest/videos?action=finalizeUpload"):
            payload = json.loads(request.content.decode("utf-8"))
            assert payload == {
                "finalizeUploadRequest": {
                    "video": "urn:li:video:123",
                    "uploadToken": "upload-token",
                    "uploadedPartIds": [
                        "/ambry-videoei/signedId/part-1.bin",
                        "/ambry-videoei/signedId/part-2.bin",
                    ],
                }
            }
            return httpx.Response(200, json={})

        if request.url == httpx.URL("https://api.linkedin.com/rest/videos/urn%3Ali%3Avideo%3A123"):
            status_polls += 1
            if status_polls == 1:
                return httpx.Response(200, json={"id": "urn:li:video:123", "status": "PROCESSING"})
            return httpx.Response(200, json={"id": "urn:li:video:123", "status": "AVAILABLE"})

        if request.url == httpx.URL("https://api.linkedin.com/rest/posts"):
            payload = json.loads(request.content.decode("utf-8"))
            assert payload == {
                "author": "urn:li:person:abc123",
                "commentary": "Hello with video",
                "visibility": "PUBLIC",
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": [],
                },
                "content": {
                    "media": {
                        "id": "urn:li:video:123",
                        "title": "Linus clip",
                    }
                },
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": False,
            }
            return httpx.Response(
                201,
                headers={"x-restli-id": "urn:li:share:654"},
                json={"id": "urn:li:share:654"},
            )

        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
        video_wait_interval=0.0,
    )

    result = client.create_video_post(
        author="urn:li:person:abc123",
        commentary="Hello with video",
        video_path=video_path,
        title="Linus clip",
    )

    assert result.post_id == "urn:li:share:654"
    assert result.response["id"] == "urn:li:share:654"
    assert [request.url for request in requests] == [
        httpx.URL("https://api.linkedin.com/rest/videos?action=initializeUpload"),
        httpx.URL("https://www.linkedin.com/dms-uploads/example/uploaded-video/0"),
        httpx.URL("https://www.linkedin.com/dms-uploads/example/uploaded-video/1"),
        httpx.URL("https://api.linkedin.com/rest/videos?action=finalizeUpload"),
        httpx.URL("https://api.linkedin.com/rest/videos/urn%3Ali%3Avideo%3A123"),
        httpx.URL("https://api.linkedin.com/rest/videos/urn%3Ali%3Avideo%3A123"),
        httpx.URL("https://api.linkedin.com/rest/posts"),
    ]


def test_get_employment_history_uses_profile_api_projection() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/v2/me"
        assert request.url.params["projection"] == "(positions)"
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["X-Restli-Protocol-Version"] == "2.0.0"
        return httpx.Response(
            200,
            json={
                "positions": {
                    "elements": [
                        {
                            "companyName": {
                                "localized": {
                                    "en_US": "FACTORED",
                                },
                                "preferredLocale": {
                                    "country": "US",
                                    "language": "en",
                                },
                            },
                            "title": {
                                "localized": {
                                    "en_US": "AI Engineer",
                                },
                                "preferredLocale": {
                                    "country": "US",
                                    "language": "en",
                                },
                            },
                            "startMonthYear": {
                                "month": 1,
                                "year": 2024,
                            },
                        }
                    ]
                }
            },
        )

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.get_employment_history()

    assert result == [
        {
            "employer_name": "FACTORED",
            "job_title": "AI Engineer",
            "start_date": "2024-01",
            "end_date": None,
            "is_current": True,
        }
    ]


def test_get_current_employment_uses_identity_me() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/identityMe")
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["Linkedin-Version"] == "202510.03"
        return httpx.Response(
            200,
            json={
                "primaryCurrentPosition": {
                    "title": {
                        "localized": {
                            "en_US": "Senior Software Engineer",
                        },
                        "preferredLocale": {
                            "country": "US",
                            "language": "en",
                        },
                    },
                    "companyName": {
                        "localized": {
                            "en_US": "LinkedIn",
                        },
                        "preferredLocale": {
                            "country": "US",
                            "language": "en",
                        },
                    },
                    "startedOn": {
                        "month": 1,
                        "year": 2022,
                    },
                }
            },
        )

    client = LinkedInClient(
        access_token="test-token",
        api_version="202606",
        identity_api_version="202510.03",
        transport=httpx.MockTransport(handler),
    )

    result = client.get_current_employment()

    assert result == [
        {
            "employer_name": "LinkedIn",
            "job_title": "Senior Software Engineer",
            "start_date": "2022-01",
            "end_date": None,
            "is_current": True,
        }
    ]


def test_get_identity_profile_uses_configured_identity_api_version() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/identityMe")
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["Linkedin-Version"] == "202510.03"
        return httpx.Response(200, json={"id": "abc123"})

    client = LinkedInClient(
        access_token="test-token",
        api_version="202606",
        identity_api_version="202510.03",
        transport=httpx.MockTransport(handler),
    )

    result = client.get_identity_profile()

    assert result["id"] == "abc123"


def test_get_identity_profile_requires_identity_api_version() -> None:
    client = LinkedInClient(
        access_token="test-token",
        api_version="202606",
        identity_api_version=None,
        transport=httpx.MockTransport(lambda request: httpx.Response(500)),
    )

    with pytest.raises(ValueError, match="identity API version"):
        client.get_identity_profile()
