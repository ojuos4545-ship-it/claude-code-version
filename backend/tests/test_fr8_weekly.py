"""FR-8 (Should): weekly summary."""

from tests.conftest import create_meal


def test_summary_counts_match_listing(client, alice):
    create_meal(client, alice, meal_date="2026-10-20", portion="small")
    create_meal(client, alice, meal_date="2026-10-20", portion="large")
    create_meal(client, alice, meal_date="2026-10-22")
    create_meal(client, alice, meal_date="2026-10-26", portion="medium")
    create_meal(client, alice, meal_date="2026-10-19")  # outside the week
    r = client.get("/v1/summaries/weekly?start=2026-10-20", headers=alice)
    assert r.status_code == 200
    s = r.json()
    assert s["start"] == "2026-10-20" and s["end"] == "2026-10-26"
    assert s["days_logged"] == 3
    assert s["daily_counts"] == [
        {"date": "2026-10-20", "count": 2},
        {"date": "2026-10-21", "count": 0},
        {"date": "2026-10-22", "count": 1},
        {"date": "2026-10-23", "count": 0},
        {"date": "2026-10-24", "count": 0},
        {"date": "2026-10-25", "count": 0},
        {"date": "2026-10-26", "count": 1},
    ]
    assert s["portion_counts"] == {"small": 1, "medium": 1, "large": 1, "none": 1}
    listed = client.get("/v1/meals?from=2026-10-20&to=2026-10-26", headers=alice).json()["items"]
    assert len(listed) == sum(d["count"] for d in s["daily_counts"])
    # no evaluative fields
    assert set(s) == {"start", "end", "days_logged", "daily_counts", "portion_counts"}


def test_empty_week(client, alice):
    s = client.get("/v1/summaries/weekly?start=2026-01-05", headers=alice).json()
    assert s["days_logged"] == 0
    assert all(d["count"] == 0 for d in s["daily_counts"])


def test_invalid_start(client, alice):
    assert client.get("/v1/summaries/weekly?start=bad", headers=alice).status_code == 422
    assert client.get("/v1/summaries/weekly", headers=alice).status_code == 422


def test_start_out_of_range_is_422_not_500(client, alice):
    for start in ("9999-12-30", "9999-12-26", "1999-12-31"):
        r = client.get(f"/v1/summaries/weekly?start={start}", headers=alice)
        assert r.status_code == 422, start
        assert r.json()["error"]["details"][0]["field"] == "start"
    assert client.get("/v1/summaries/weekly?start=9999-12-25", headers=alice).status_code == 200
