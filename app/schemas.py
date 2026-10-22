from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

# Texto sin espacios sobrantes, no vacío, máximo 100 caracteres
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class VoterCreate(BaseModel):
    name: Name
    email: EmailStr


class VoterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    has_voted: bool


class CandidateCreate(BaseModel):
    name: Name
    party: Optional[Name] = None


class CandidateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    party: Optional[str]
    votes: int


class VoteCreate(BaseModel):
    voter_id: int = Field(gt=0)
    candidate_id: int = Field(gt=0)


class VoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    voter_id: int
    candidate_id: int


class CandidateStats(BaseModel):
    candidate_id: int
    name: str
    party: Optional[str]
    votes: int
    percentage: float


class VoteStatistics(BaseModel):
    total_votes: int
    total_voters_who_voted: int
    total_registered_voters: int
    candidates: list[CandidateStats]