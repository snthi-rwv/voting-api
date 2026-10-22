from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session


def contains_pattern(text: str) -> str:
    """Patrón LIKE de 'contiene', escapando % y _ para que no actúen como comodines."""
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def count_rows(db: Session, query: Select) -> int:
    """Cuenta cuántas filas devuelve una consulta, sin paginar."""
    return db.scalar(select(func.count()).select_from(query.subquery()))