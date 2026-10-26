"""FR-4: delete meal entries."""

from tests.conftest import create_meal


def test_deleted_meal_disappears_everywhere(client, alice):
    meal = create_meal(client, alice, description="donut", portion="large")
    keep = create_meal(client, alice, description="apple")
    assert client.delete(f"/v1/meals/{meal['id']}", headers=alice).status_code == 204

    assert client.get(f"/v1/meals/{meal['id']}", headers=alice).status_code == 404
    day = client.get("/v1/meals?date=2026-10-26", headers=alice).json()["items"]
    rng = client.get("/v1/meals?from=2026-10-01&to=2026-10-26", headers=alice).json()["items"]
    assert [m["id"] for m in day] == [m["id"] for m in rng] == [keep["id"]]
    recent = client.get("/v1/meals/recent-descriptions", headers=alice).json()["items"]
    assert recent == ["apple"]
    summary = client.get("/v1/summaries/weekly?start=2026-10-20", headers=alice).json()
    assert summary["portion_counts"]["large"] == 0
    assert sum(d["count"] for d in summary["daily_counts"]) == 1


def test_deleting_twice_is_not_a_server_error(client, alice):
    meal = create_meal(client, alice)
    assert client.delete(f"/v1/meals/{meal['id']}", headers=alice).status_code == 204
    again = client.delete(f"/v1/meals/{meal['id']}", headers=alice)
    assert again.status_code == 404
    assert again.json()["error"]["code"] == "not_found"


def test_cannot_delete_other_users_meal(client, alice, bob):
    meal = create_meal(client, alice)
    assert client.delete(f"/v1/meals/{meal['id']}", headers=bob).status_code == 404
    assert client.get(f"/v1/meals/{meal['id']}", headers=alice).status_code == 200
