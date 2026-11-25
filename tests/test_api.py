from copy import deepcopy
from urllib.parse import quote

import pytest


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_list_activities(client, activity_data):
    # Arrange
    expected = deepcopy(activity_data)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected


def test_signup_adds_participant(client, activity_data):
    # Arrange
    activity = "Chess Club"
    email = "new@example.com"

    # Act
    response = client.post(
        f"/activities/{quote(activity, safe='')}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity}"}
    assert activity_data[activity]["participants"] == ["existing@example.com", email]


@pytest.mark.parametrize(
    ("activity", "params", "status_code", "detail"),
    [
        ("Unknown Club", {"email": "new@example.com"}, 404, "Activity not found"),
        (
            "Chess Club",
            {"email": "existing@example.com"},
            400,
            "Student already signed up for this activity",
        ),
        ("Chess Club", {}, 422, None),
    ],
)
def test_signup_errors_do_not_change_activities(
    client, activity_data, activity, params, status_code, detail
):
    # Arrange
    original = deepcopy(activity_data)

    # Act
    response = client.post(
        f"/activities/{quote(activity, safe='')}/signup", params=params
    )

    # Assert
    assert response.status_code == status_code
    if detail is None:
        assert response.json()["detail"][0]["loc"] == ["query", "email"]
    else:
        assert response.json() == {"detail": detail}
    assert activity_data == original


def test_unregister_removes_participant(client, activity_data):
    # Arrange
    activity = "Chess Club"
    email = "existing@example.com"

    # Act
    response = client.delete(
        f"/activities/{quote(activity, safe='')}/participants", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity}"}
    assert activity_data[activity]["participants"] == []


@pytest.mark.parametrize(
    ("activity", "params", "status_code", "detail"),
    [
        ("Unknown Club", {"email": "existing@example.com"}, 404, "Activity not found"),
        (
            "Chess Club",
            {"email": "missing@example.com"},
            404,
            "Student is not signed up for this activity",
        ),
        ("Chess Club", {}, 422, None),
    ],
)
def test_unregister_errors_do_not_change_activities(
    client, activity_data, activity, params, status_code, detail
):
    # Arrange
    original = deepcopy(activity_data)

    # Act
    response = client.delete(
        f"/activities/{quote(activity, safe='')}/participants", params=params
    )

    # Assert
    assert response.status_code == status_code
    if detail is None:
        assert response.json()["detail"][0]["loc"] == ["query", "email"]
    else:
        assert response.json() == {"detail": detail}
    assert activity_data == original
