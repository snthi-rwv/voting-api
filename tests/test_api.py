from app.models import Candidate, Voter


# ---------- helpers ----------

def make_voter(client, name="Ana Gómez", email="ana@mail.com"):
    response = client.post("/voters", json={"name": name, "email": email})
    assert response.status_code == 201
    return response.json()


def make_candidate(client, name="Carlos Ruiz", party="Partido Verde"):
    response = client.post("/candidates", json={"name": name, "party": party})
    assert response.status_code == 201
    return response.json()


def vote(client, voter_id, candidate_id):
    return client.post("/votes", json={"voter_id": voter_id, "candidate_id": candidate_id})


def voter_has_voted(session_factory, voter_id):
    with session_factory() as db:
        return db.get(Voter, voter_id).has_voted


def candidate_votes(session_factory, candidate_id):
    with session_factory() as db:
        return db.get(Candidate, candidate_id).votes


# ---------- votantes y candidatos ----------

def test_create_voter_defaults_has_voted_false(client):
    voter = make_voter(client)
    assert voter["has_voted"] is False


def test_duplicate_email_returns_409(client):
    make_voter(client, email="ana@mail.com")
    response = client.post("/voters", json={"name": "Otra Ana", "email": "ANA@mail.com"})
    assert response.status_code == 409


def test_invalid_email_returns_422(client):
    response = client.post("/voters", json={"name": "Test", "email": "no-es-email"})
    assert response.status_code == 422


def test_blank_name_returns_422(client):
    response = client.post("/voters", json={"name": "   ", "email": "t@mail.com"})
    assert response.status_code == 422


def test_voter_cannot_also_be_candidate(client):
    make_candidate(client, name="Carlos Ruiz")
    response = client.post("/voters", json={"name": "carlos ruiz", "email": "c@mail.com"})
    assert response.status_code == 409


def test_candidate_cannot_also_be_voter(client):
    make_voter(client, name="Ana Gómez")
    response = client.post("/candidates", json={"name": "ana gómez", "party": "X"})
    assert response.status_code == 409


def test_candidate_party_is_optional(client):
    response = client.post("/candidates", json={"name": "Pedro Salazar"})
    assert response.status_code == 201
    assert response.json()["party"] is None


def test_list_candidates_paginates(client):
    for i in range(3):
        make_candidate(client, name=f"Candidato {i}")
    response = client.get("/candidates", params={"skip": 1, "limit": 1})
    assert response.status_code == 200
    assert [c["name"] for c in response.json()] == ["Candidato 1"]


# ---------- votos ----------

def test_vote_updates_voter_and_candidate(client, session_factory):
    voter = make_voter(client)
    candidate = make_candidate(client)

    response = vote(client, voter["id"], candidate["id"])

    assert response.status_code == 201
    assert voter_has_voted(session_factory, voter["id"]) is True
    assert candidate_votes(session_factory, candidate["id"]) == 1


def test_voter_cannot_vote_twice(client, session_factory):
    voter = make_voter(client)
    c1 = make_candidate(client, name="Carlos Ruiz")
    c2 = make_candidate(client, name="Laura Mejía")

    assert vote(client, voter["id"], c1["id"]).status_code == 201
    assert vote(client, voter["id"], c1["id"]).status_code == 409
    assert vote(client, voter["id"], c2["id"]).status_code == 409  # ni por otro candidato

    assert candidate_votes(session_factory, c1["id"]) == 1
    assert candidate_votes(session_factory, c2["id"]) == 0


def test_vote_for_unknown_candidate_returns_404_and_changes_nothing(client, session_factory):
    voter = make_voter(client)

    response = vote(client, voter["id"], 999)

    assert response.status_code == 404
    assert voter_has_voted(session_factory, voter["id"]) is False


def test_vote_with_unknown_voter_returns_404(client):
    candidate = make_candidate(client)
    assert vote(client, 999, candidate["id"]).status_code == 404


def test_vote_with_invalid_ids_returns_422(client):
    assert vote(client, 0, 1).status_code == 422


def test_list_votes(client):
    voter = make_voter(client)
    candidate = make_candidate(client)
    vote(client, voter["id"], candidate["id"])

    response = client.get("/votes")

    assert response.status_code == 200
    assert response.json() == [
        {"id": response.json()[0]["id"], "voter_id": voter["id"], "candidate_id": candidate["id"]}
    ]


# ---------- estadísticas ----------

def test_statistics_reflect_real_votes(client):
    voters = [make_voter(client, name=f"Votante {i}", email=f"v{i}@mail.com") for i in range(4)]
    c1 = make_candidate(client, name="Carlos Ruiz")
    c2 = make_candidate(client, name="Laura Mejía")
    c3 = make_candidate(client, name="Pedro Salazar")  # sin votos

    vote(client, voters[0]["id"], c1["id"])
    vote(client, voters[1]["id"], c1["id"])
    vote(client, voters[2]["id"], c2["id"])

    stats = client.get("/votes/statistics").json()

    assert stats["total_votes"] == 3
    assert stats["total_voters_who_voted"] == 3
    assert stats["total_registered_voters"] == 4

    by_id = {c["candidate_id"]: c for c in stats["candidates"]}
    assert by_id[c1["id"]]["votes"] == 2
    assert by_id[c1["id"]]["percentage"] == 66.67
    assert by_id[c2["id"]]["percentage"] == 33.33
    assert by_id[c3["id"]]["votes"] == 0  # aparece aunque no tenga votos
    assert by_id[c3["id"]]["percentage"] == 0.0


def test_statistics_with_no_votes(client):
    make_candidate(client)
    stats = client.get("/votes/statistics").json()
    assert stats["total_votes"] == 0
    assert stats["candidates"][0]["percentage"] == 0.0


# ---------- borrar votante ----------

def test_delete_voter_who_voted_removes_their_vote(client, session_factory):
    voter = make_voter(client)
    candidate = make_candidate(client)
    vote(client, voter["id"], candidate["id"])

    assert client.delete(f"/voters/{voter['id']}").status_code == 204

    assert candidate_votes(session_factory, candidate["id"]) == 0
    assert client.get("/votes").json() == []
    assert client.get("/votes/statistics").json()["total_votes"] == 0


def test_delete_unknown_voter_returns_404(client):
    assert client.delete("/voters/999").status_code == 404


# ---------- gráfica ----------

def test_chart_returns_png(client):
    make_candidate(client)
    response = client.get("/votes/chart")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG")


def test_chart_without_candidates_returns_404(client):
    assert client.get("/votes/chart").status_code == 404