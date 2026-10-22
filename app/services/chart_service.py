from io import BytesIO
from typing import Optional

import pandas as pd
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Candidate, Vote


def build_votes_chart(db: Session) -> Optional[bytes]:
    """Genera un PNG de barras con los votos actuales de cada candidato.

    Devuelve None si todavía no hay candidatos registrados.
    """
    rows = db.execute(
        select(Candidate.name, func.count(Vote.id))
        .outerjoin(Vote, Vote.candidate_id == Candidate.id)
        .group_by(Candidate.id)
        .order_by(Candidate.id)
    ).all()

    if not rows:
        return None

    df = pd.DataFrame([tuple(row) for row in rows], columns=["candidate", "votes"])

    fig = Figure(figsize=(8, 5))
    ax = fig.subplots()

    # Candidatos en el eje X, votos en el eje Y
    df.plot.bar(x="candidate", y="votes", ax=ax, legend=False, color="#4C78A8", rot=0)
    ax.bar_label(ax.containers[0])  # número encima de cada barra

    ax.set_title(f"Votos por candidato (total: {int(df['votes'].sum())})")
    ax.set_xlabel("Candidato")
    ax.set_ylabel("Cantidad de votos")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))  # solo enteros
    ax.set_ylim(bottom=0, top=max(1, int(df["votes"].max()) * 1.15))

    buffer = BytesIO()
    fig.tight_layout()
    fig.savefig(buffer, format="png", dpi=120)
    return buffer.getvalue()