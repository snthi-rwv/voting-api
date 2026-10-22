import pytest


def make_candidate(client, name, party=None):
    response = client.post("/candidates", json={"name": name, "party": party})
    assert response.status_code == 201
    return response.json()


def make_voter(client, name, email):
    response = client.post("/voters", json={"name": name, "email": email})
    assert response.status_code == 201
    return response.json()

#Candidatos

def test_filter_candidates_by_name_is_partial_and_case_insensitive(client):
    make_candidate(client, "Carlos Ruiz", "Verde")
    make_candidate(client, "Laura Mejía", "Azul")

    response = client.get("/candidates", params={"name": "CARL"})

    assert [c["name"] for c in response.json()] == ["Carlos Ruiz"]


def test_filter_candidates_by_party(client):
    make_candidate(client, "Carlos Ruiz", "Partido Verde")
    make_candidate(client, "Laura Mejía", "Alianza Azul")
    make_candidate(client, "Pedro Salazar")  # sin partido

    response = client.get("/candidates", params={"party": "verde"})

    assert [c["name"] for c in response.json()] == ["Carlos Ruiz"]


def test_candidates_combined_filters_and_pagination_header(client):
    for i in range(5):
        make_candidate(client, f"Candidato {i}", "Verde")
    make_candidate(client, "Otro", "Azul")

    response = client.get("/candidates", params={"party": "verde", "skip": 1, "limit": 2})

    assert [c["name"] for c in response.json()] == ["Candidato 1", "Candidato 2"]
    assert response.headers["X-Total-Count"] == "5"  # total sin paginar


def test_wildcards_in_search_are_treated_as_plain_text(client):
    make_candidate(client, "Carlos Ruiz")

    assert client.get("/candidates", params={"name": "%"}).json() == []
    assert client.get("/candidates", params={"name": "_"}).json() == []


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 201}, {"skip": -1}])
def test_invalid_pagination_returns_422(client, params):
    assert client.get("/candidates", params=params).status_code == 422


#Votantes

def test_list_voters_with_filters(client):
    ana = make_voter(client, "Ana Gómez", "ana@mail.com")
    make_voter(client, "Luis Pérez", "luis@correo.com")
    candidate = make_candidate(client, "Carlos Ruiz")
    client.post("/votes", json={"voter_id": ana["id"], "candidate_id": candidate["id"]})

    by_name = client.get("/voters", params={"name": "luis"}).json()
    by_email = client.get("/voters", params={"email": "correo.com"}).json()
    voted = client.get("/voters", params={"has_voted": True}).json()
    not_voted = client.get("/voters", params={"has_voted": False}).json()

    assert [v["name"] for v in by_name] == ["Luis Pérez"]
    assert [v["name"] for v in by_email] == ["Luis Pérez"]
    assert [v["name"] for v in voted] == ["Ana Gómez"]
    assert [v["name"] for v in not_voted] == ["Luis Pérez"]


def test_voters_pagination_and_total_header(client):
    for i in range(4):
        make_voter(client, f"Votante {i}", f"v{i}@mail.com")

    response = client.get("/voters", params={"skip": 2, "limit": 1})

    assert [v["name"] for v in response.json()] == ["Votante 2"]
    assert response.headers["X-Total-Count"] == "4"