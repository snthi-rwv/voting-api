from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import Candidate, Voter

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