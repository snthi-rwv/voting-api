from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import Candidate, Vote, Voter
from app.services.chart_service import build_votes_chart

router = APIRouter(prefix="/votes", tags=["Votes"])


@router.post("", response_model=schemas.VoteOut, status_code=status.HTTP_201_CREATED)
def create_vote(data: schemas.VoteCreate, db: Session = Depends(get_db)):
    # Validación: el votante y el candidato deben existir
    if not db.get(Voter, data.voter_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Votante no encontrado")
    if not db.get(Candidate, data.candidate_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Candidato no encontrado")

    # Marcar has_voted de forma atómica: solo prospera si todavía era false.
    # Así, dos peticiones simultáneas del mismo votante no pueden votar las dos.
    claimed = db.execute(
        update(Voter)
        .where(Voter.id == data.voter_id, Voter.has_voted.is_(False))
        .values(has_voted=True)
    )
    if claimed.rowcount == 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "Este votante ya emitió su voto")

    vote = Vote(voter_id=data.voter_id, candidate_id=data.candidate_id)
    db.add(vote)

    # Incremento en la base de datos (votes = votes + 1), no en Python,
    # para no perder votos si llegan varios a la vez
    db.execute(
        update(Candidate)
        .where(Candidate.id == data.candidate_id)
        .values(votes=Candidate.votes + 1)
    )

    try:
        db.commit()  # voto + has_voted + contador: todo o nada
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "No se pudo registrar el voto")

    db.refresh(vote)
    return vote


@router.get("", response_model=list[schemas.VoteOut])
def list_votes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return db.scalars(select(Vote).order_by(Vote.id).offset(skip).limit(limit)).all()


@router.get("/statistics", response_model=schemas.VoteStatistics)
def vote_statistics(db: Session = Depends(get_db)):
    # outerjoin: los candidatos sin votos también aparecen, con 0
    rows = db.execute(
        select(
            Candidate.id,
            Candidate.name,
            Candidate.party,
            func.count(Vote.id).label("votes"),
        )
        .outerjoin(Vote, Vote.candidate_id == Candidate.id)
        .group_by(Candidate.id)
        .order_by(func.count(Vote.id).desc(), Candidate.id)
    ).all()

    total_votes = sum(row.votes for row in rows)

    return schemas.VoteStatistics(
        total_votes=total_votes,
        total_voters_who_voted=db.scalar(select(func.count(func.distinct(Vote.voter_id)))),
        total_registered_voters=db.scalar(select(func.count(Voter.id))),
        candidates=[
            schemas.CandidateStats(
                candidate_id=row.id,
                name=row.name,
                party=row.party,
                votes=row.votes,
                percentage=round(row.votes / total_votes * 100, 2) if total_votes else 0.0,
            )
            for row in rows
        ],
    )
@router.get(
    "/chart",
    response_class=Response,
    responses={200: {"content": {"image/png": {}}, "description": "Gráfica de barras en PNG"}},
)
def votes_chart(db: Session = Depends(get_db)):
    png = build_votes_chart(db)
    if png is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No hay candidatos registrados")
    return Response(content=png, media_type="image/png")