"""FR-1: authenticated access only, per-user data isolation."""

import pytest

from tests.conftest import create_meal

FAKE_ID = "0" * 32


@pytest.mark.parametrize(
    "method, path, body",
    [
        ("POST", "/v1/meals", {"description": "rice"}),
        ("GET", "/v1/meals?date=2026-10-26", None),
        ("GET", "/v1/meals/{id}", None),
        ("PATCH", "/v1/meals/{id}", {"description": "changed"}),
        ("DELETE", "/v1/meals/{id}", None),
        ("GET", "/v1/meals/recent-descriptions", None),
        ("GET", "/v1/summaries/weekly?start=2026-10-20", None),
        ("GET", "/v1/me", None),
        ("DELETE", "/v1/me", {"password": "x"}),
    ],
)
@pytest.mark.parametrize(
    "auth", [None, {"Authorization": "Bearer not-a-real-token"}, {"Authorization": "Basic abc"}]
)
def test_requests_without_valid_auth_are_rejected_and_change_nothing(
    client, alice, method, path, body, auth
):
    meal = create_meal(client, alice, description="original")
    r = client.request(method, path.format(id=meal["id"]), json=body, headers=auth or {})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthenticated"
    # data unchanged
    after = client.get(f"/v1/meals/{meal['id']}", headers=alice)
    assert after.status_code == 200
    assert after.json() == meal
    listed = client.get("/v1/meals?date=2026-10-26", headers=alice).json()["items"]
    assert len(listed) == 1


def test_other_users_meal_looks_exactly_like_missing_meal(client, alice, bob):
    meal = create_meal(client, alice)
    for method, body in [("GET", None), ("PATCH", {"description": "hacked"}), ("DELETE", None)]:
        foreign = client.request(method, f"/v1/meals/{meal['id']}", json=body, headers=bob)
        missing = client.request(method, f"/v1/meals/{FAKE_ID}", json=body, headers=bob)
        assert foreign.status_code == missing.status_code == 404
        assert foreign.json() == missing.json()
    # Alice's meal is untouched
    assert client.get(f"/v1/meals/{meal['id']}", headers=alice).json() == meal


def test_lists_and_aggregates_never_mix_users(client, alice, bob):
    create_meal(client, alice, description="alice food", portion="large")
    create_meal(client, bob, description="bob food")
    a_list = client.get("/v1/meals?date=2026-10-26", headers=alice).json()["items"]
    b_list = client.get("/v1/meals?from=2026-10-01&to=2026-10-26", headers=bob).json()["items"]
    assert [m["description"] for m in a_list] == ["alice food"]
    assert [m["description"] for m in b_list] == ["bob food"]
    a_recent = client.get("/v1/meals/recent-descriptions", headers=alice).json()["items"]
    assert a_recent == ["alice food"]
    b_summary = client.get("/v1/summaries/weekly?start=2026-10-20", headers=bob).json()
    assert b_summary["portion_counts"]["large"] == 0
    assert sum(d["count"] for d in b_summary["daily_counts"]) == 1


def test_owner_is_taken_from_token_not_body(client, alice):
    r = client.post("/v1/meals", json={"description": "x", "user_id": "someone"}, headers=alice)
    assert r.status_code == 422
