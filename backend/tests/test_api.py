"""
Regression tests for the medicine API. Every test runs against a temporary
data file, so the real data.json is never read or changed.
Run from the backend folder with: python -m pytest
"""
import json

import pytest
from fastapi.testclient import TestClient

import main

SAMPLE_DATA = {
    "medicines": [
        {"name": "Healix", "price": 4.99},
        {"name": "", "price": 15.49},
        {"name": "Tonicast", "price": None},
        {"name": "Twin", "price": 1.0},
        {"name": "Twin", "price": 2.0},
    ]
}


@pytest.fixture
def data_file(tmp_path, monkeypatch):
    path = tmp_path / "data.json"
    path.write_text(json.dumps(SAMPLE_DATA))
    monkeypatch.setattr(main, "DATA_FILE", path)
    return path


@pytest.fixture
def client(data_file):
    return TestClient(main.app)


def stored(data_file):
    return json.loads(data_file.read_text())["medicines"]


def by_name(client, name):
    return [med for med in client.get("/medicines").json()["medicines"] if med["name"] == name]


# ---- Stable ids ----

def test_existing_records_get_ids_without_other_changes(client, data_file):
    medicines = client.get("/medicines").json()["medicines"]
    assert all(med["id"] for med in medicines)
    assert len({med["id"] for med in medicines}) == len(SAMPLE_DATA["medicines"])
    without_ids = [{"name": med["name"], "price": med["price"]} for med in stored(data_file)]
    assert without_ids == SAMPLE_DATA["medicines"]


def test_ids_stay_the_same_between_requests(client):
    first = client.get("/medicines").json()
    assert client.get("/medicines").json() == first


def test_original_file_is_backed_up_once(client, data_file):
    client.get("/medicines")
    backup = data_file.with_suffix(".json.bak")
    assert json.loads(backup.read_text()) == SAMPLE_DATA

    data = json.loads(data_file.read_text())
    data["medicines"].append({"name": "Added By Hand", "price": 1})
    data_file.write_text(json.dumps(data))
    client.get("/medicines")
    assert json.loads(backup.read_text()) == SAMPLE_DATA


# ---- Reading ----

def test_get_single_medicine(client):
    response = client.get("/medicines/Healix")
    assert response.status_code == 200
    assert response.json()["price"] == 4.99


def test_get_missing_medicine_returns_404(client):
    response = client.get("/medicines/Nothing")
    assert response.status_code == 404
    assert response.json()["detail"] == "Medicine not found"


def test_get_ambiguous_name_returns_409(client):
    assert client.get("/medicines/Twin").status_code == 409


# ---- Creating ----

def test_create_persists_and_returns_the_record(client, data_file):
    response = client.post("/create", data={"name": "  Newmed  ", "price": "3.5"})
    assert response.status_code == 200
    created = response.json()["medicine"]
    assert created["name"] == "Newmed"
    assert created in stored(data_file)


def test_create_accepts_a_zero_price(client):
    assert client.post("/create", data={"name": "Freebie", "price": "0"}).status_code == 200


@pytest.mark.parametrize("price", ["-0.01", "-5", "abc", "nan", "inf", "-inf", ""])
def test_create_rejects_invalid_prices(client, data_file, price):
    response = client.post("/create", data={"name": "Badprice", "price": price})
    assert response.status_code == 422
    assert response.json()["detail"] == main.FIELD_ERRORS["price"]
    assert client.get("/medicines").status_code == 200
    assert not [med for med in stored(data_file) if med["name"] == "Badprice"]


@pytest.mark.parametrize("name", ["", "   ", "ab", "x" * 51])
def test_create_rejects_invalid_names(client, data_file, name):
    response = client.post("/create", data={"name": name, "price": "1"})
    assert response.status_code == 422
    assert response.json()["detail"] == main.FIELD_ERRORS["name"]
    assert len(stored(data_file)) == len(SAMPLE_DATA["medicines"])


@pytest.mark.parametrize("name", ["Healix", "healix", " HEALIX "])
def test_create_rejects_duplicate_names(client, data_file, name):
    response = client.post("/create", data={"name": name, "price": "1"})
    assert response.status_code == 409
    assert len(stored(data_file)) == len(SAMPLE_DATA["medicines"])


# ---- Updating ----

def test_update_by_id_changes_only_that_duplicate(client):
    first, second = by_name(client, "Twin")
    response = client.post("/update", data={"id": second["id"], "price": "9"})
    assert response.status_code == 200
    after = {med["id"]: med["price"] for med in by_name(client, "Twin")}
    assert after == {first["id"]: 1.0, second["id"]: 9.0}


def test_update_by_name_still_works(client):
    assert client.post("/update", data={"name": "Healix", "price": "6"}).status_code == 200
    assert client.get("/medicines/Healix").json()["price"] == 6.0


def test_update_by_ambiguous_name_changes_nothing(client):
    response = client.post("/update", data={"name": "Twin", "price": "9"})
    assert response.status_code == 409
    assert sorted(med["price"] for med in by_name(client, "Twin")) == [1.0, 2.0]


def test_update_can_fill_a_missing_price(client):
    tonicast = by_name(client, "Tonicast")[0]
    client.post("/update", data={"id": tonicast["id"], "price": "2.5"})
    assert client.get("/medicines/Tonicast").json()["price"] == 2.5


def test_update_can_target_the_unnamed_record(client):
    unnamed = by_name(client, "")[0]
    response = client.post("/update", data={"id": unnamed["id"], "price": "1"})
    assert response.status_code == 200
    assert "Unknown Med" in response.json()["message"]


@pytest.mark.parametrize("price", ["-1", "abc", "nan", "inf"])
def test_update_rejects_invalid_prices(client, price):
    response = client.post("/update", data={"name": "Healix", "price": price})
    assert response.status_code == 422
    assert client.get("/medicines/Healix").json()["price"] == 4.99


def test_update_missing_medicine_returns_404(client):
    assert client.post("/update", data={"name": "Nothing", "price": "1"}).status_code == 404
    assert client.post("/update", data={"id": "not-an-id", "price": "1"}).status_code == 404


def test_update_without_a_target_returns_422(client):
    assert client.post("/update", data={"price": "1"}).status_code == 422


# ---- Deleting ----

def test_delete_by_id_removes_only_that_duplicate(client):
    first, second = by_name(client, "Twin")
    assert client.request("DELETE", "/delete", data={"id": first["id"]}).status_code == 200
    assert [med["id"] for med in by_name(client, "Twin")] == [second["id"]]


def test_delete_can_target_the_unnamed_record(client):
    unnamed = by_name(client, "")[0]
    assert client.request("DELETE", "/delete", data={"id": unnamed["id"]}).status_code == 200
    assert by_name(client, "") == []


def test_delete_by_ambiguous_name_removes_nothing(client):
    assert client.request("DELETE", "/delete", data={"name": "Twin"}).status_code == 409
    assert len(by_name(client, "Twin")) == 2


def test_delete_missing_medicine_returns_404(client, data_file):
    assert client.request("DELETE", "/delete", data={"name": "Nothing"}).status_code == 404
    assert len(stored(data_file)) == len(SAMPLE_DATA["medicines"])


def test_delete_without_a_target_returns_422(client):
    assert client.request("DELETE", "/delete", data={"name": ""}).status_code == 422


# ---- Average price ----

def test_average_uses_only_valid_prices(client):
    body = client.get("/average-price").json()
    assert body["average_price"] == round((4.99 + 15.49 + 1.0 + 2.0) / 4, 2)
    assert body["total_medicines"] == 5
    assert body["medicines_with_valid_prices"] == 4


def test_average_ignores_invalid_stored_prices(client, data_file):
    data_file.write_text(json.dumps({"medicines": [
        {"name": "One", "price": 10},
        {"name": "Two", "price": -10},
        {"name": "Three", "price": "12"},
        {"name": "Four", "price": True},
    ]}))
    body = client.get("/average-price").json()
    assert body["average_price"] == 10
    assert body["medicines_with_valid_prices"] == 1


def test_average_of_zero_is_reported(client, data_file):
    data_file.write_text(json.dumps({"medicines": [{"name": "Free", "price": 0}]}))
    assert client.get("/average-price").json()["average_price"] == 0


def test_average_with_no_valid_prices(client, data_file):
    data_file.write_text(json.dumps({"medicines": []}))
    response = client.get("/average-price")
    assert response.status_code == 200
    assert response.json()["average_price"] is None


# ---- Data file ----

def test_changes_are_saved_for_later_requests(client, data_file):
    client.post("/create", data={"name": "Keeper", "price": "1"})
    assert TestClient(main.app).get("/medicines/Keeper").status_code == 200


def test_missing_data_file_returns_500(client, data_file):
    data_file.unlink()
    response = client.get("/medicines")
    assert response.status_code == 500
    assert response.json()["detail"] == "The data file could not be found."


def test_corrupt_data_file_returns_500_and_is_left_alone(client, data_file):
    data_file.write_text("{not json")
    assert client.get("/medicines").status_code == 500
    assert data_file.read_text() == "{not json"
