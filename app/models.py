from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Voter(Base):
    __tablename__ = "voters"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    has_voted: Mapped[bool] = mapped_column(default=False, server_default="false")

    # cascade: al borrar el votante se borra también su voto
    vote: Mapped[Optional["Vote"]] = relationship(
        back_populates="voter", cascade="all, delete-orphan"
    )


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    party: Mapped[Optional[str]] = mapped_column(String(100))
    votes: Mapped[int] = mapped_column(default=0, server_default="0")

    received_votes: Mapped[list["Vote"]] = relationship(back_populates="candidate")


class Vote(Base):
    __tablename__ = "votes"

    id: Mapped[int] = mapped_column(primary_key=True)
    # unique=True: la base de datos misma impide que un votante tenga 2 votos
    voter_id: Mapped[int] = mapped_column(ForeignKey("voters.id"), unique=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), index=True)

    voter: Mapped["Voter"] = relationship(back_populates="vote")
    candidate: Mapped["Candidate"] = relationship(back_populates="received_votes")