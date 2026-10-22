from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import Candidate, Voter
from app.utils import contains_pattern, count_rows

router = APIRouter(prefix="/voters", tags=["Voters"])


@router.post("", response_model=schemas.VoterOut, status_code=status.HTTP_201_CREATED)
def create_voter(data: schemas.VoterCreate, db: Session = Depends(get_db)):
    email = data.email.lower()

    if db.scalar(select(Voter).where(Voter.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un votante con ese email")

    # Regla 1: la misma persona no puede ser votante y candidato
    is_candidate = db.scalar(
        select(Candidate).where(func.lower(func.trim(Candidate.name)) == data.name.lower())
    )
    if is_candidate:
        raise HTTPException(status.HTTP_409_CONFLICT, "Esta persona ya está registrada como candidato")

    voter = Voter(name=data.name, email=email)
    db.add(voter)
    try:
        db.commit()
    except IntegrityError:  # dos peticiones simultáneas con el mismo email
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un votante con ese email")
    db.refresh(voter)
    return voter


@router.get("", response_model=list[schemas.VoterOut])
def list_voters(
    response: Response,
    name: Optional[str] = Query(None, min_length=1, description="Búsqueda parcial por nombre"),
    email: Optional[str] = Query(None, min_length=1, description="Búsqueda parcial por email"),
    has_voted: Optional[bool] = Query(None, description="Filtrar por si ya votó o no"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = select(Voter)
    if name:
        query = query.where(Voter.name.ilike(contains_pattern(name), escape="\\"))
    if email:
        query = query.where(Voter.email.ilike(contains_pattern(email), escape="\\"))
    if has_voted is not None:
        query = query.where(Voter.has_voted.is_(has_voted))

    response.headers["X-Total-Count"] = str(count_rows(db, query))
    return db.scalars(query.order_by(Voter.id).offset(skip).limit(limit)).all()


@router.delete("/{voter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_voter(voter_id: int, db: Session = Depends(get_db)):
    voter = db.get(Voter, voter_id)
    if not voter:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Votante no encontrado")

    # Si ya votó, se descuenta su voto para que las estadísticas sigan siendo reales
    if voter.vote:
        db.execute(
            update(Candidate)
            .where(Candidate.id == voter.vote.candidate_id)
            .values(votes=Candidate.votes - 1)
        )

    db.delete(voter)  # el cascade borra también su voto
    db.commit()