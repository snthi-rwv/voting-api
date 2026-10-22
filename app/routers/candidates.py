from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import Candidate, Voter
from app.utils import contains_pattern, count_rows

router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.post("", response_model=schemas.CandidateOut, status_code=status.HTTP_201_CREATED)
def create_candidate(data: schemas.CandidateCreate, db: Session = Depends(get_db)):
    # Regla 1 (la otra dirección): un votante no puede ser candidato
    is_voter = db.scalar(
        select(Voter).where(func.lower(func.trim(Voter.name)) == data.name.lower())
    )
    if is_voter:
        raise HTTPException(status.HTTP_409_CONFLICT, "Esta persona ya está registrada como votante")

    candidate = Candidate(name=data.name, party=data.party)
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


@router.get("", response_model=list[schemas.CandidateOut])
def list_candidates(
    response: Response,
    name: Optional[str] = Query(None, min_length=1, description="Búsqueda parcial por nombre"),
    party: Optional[str] = Query(None, min_length=1, description="Búsqueda parcial por partido"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = select(Candidate)
    if name:
        query = query.where(Candidate.name.ilike(contains_pattern(name), escape="\\"))
    if party:
        query = query.where(Candidate.party.ilike(contains_pattern(party), escape="\\"))

    # Total de resultados (antes de paginar), útil para que el cliente arme su paginación
    response.headers["X-Total-Count"] = str(count_rows(db, query))
    return db.scalars(query.order_by(Candidate.id).offset(skip).limit(limit)).all()