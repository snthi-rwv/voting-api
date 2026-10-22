# Voting API

Prueba Tecnica para NewInntech: API REST para gestionar un sistema de votaciones: registro de votantes y candidatos, emisión de votos (uno por votante), estadísticas y una gráfica de resultados generada con pandas.

**Stack:** Python · FastAPI · PostgreSQL · SQLAlchemy · pandas / matplotlib · pytest

## Contenido

1. [Características](#características)
2. [Instalación y ejecución](#instalación-y-ejecución)
3. [Tests](#tests)
4. [Endpoints](#endpoints)
5. [Ejemplos de uso](#ejemplos-de-uso)
6. [Capturas](#capturas)
7. [Reglas y decisiones de diseño](#reglas-y-decisiones-de-diseño)
8. [Estructura del proyecto](#estructura-del-proyecto)

## Características

- Registro de votantes y candidatos con validación de datos.
- Una misma persona no puede ser votante y candidato a la vez.
- Cada votante vota una sola vez, garantizado en código y en la base de datos.
- Registrar un voto actualiza `has_voted` y el contador del candidato en una sola transacción.
- Estadísticas calculadas desde los votos reales registrados.
- Gráfica de barras de votos por candidato (pandas + matplotlib).
- Paginación en `GET /candidates` y `GET /votes`.
- Documentación interactiva con Swagger.

## Instalación y ejecución

### Requisitos

- Python 3.12 o superior (desarrollado con 3.14)
- PostgreSQL

### Pasos

1. Clonar el repositorio:

```bash
git clone https://github.com/snthi-rwv/voting-api.git
cd voting-api
```

2. Crear y activar el entorno virtual:

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Crear una base de datos vacía en PostgreSQL llamada `voting_db`.

5. Copiar `.env.example` a `.env` y ajustar usuario y contraseña:

```
DATABASE_URL=postgresql+psycopg://usuario:password@localhost:5432/voting_db
```

6. Iniciar el servidor (las tablas se crean automáticamente al arrancar):

```bash
uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- Documentación Swagger: http://127.0.0.1:8000/docs

## Tests

```bash
pytest -v
```

Los tests usan SQLite en memoria, por lo que no tocan la base de datos PostgreSQL. Cubren las reglas del sistema: votos únicos, candidato inexistente, exclusión votante/candidato, actualización de `has_voted` y contadores, estadísticas y gráfica.

## Endpoints

| Método | Endpoint | Descripción | Respuestas |
|---|---|---|---|
| POST | `/voters` | Registrar un votante | 201, 409, 422 |
| DELETE | `/voters/{id}` | Eliminar un votante | 204, 404 |
| POST | `/candidates` | Registrar un candidato | 201, 409, 422 |
| GET | `/candidates` | Listar candidatos (`skip`, `limit`) | 200 |
| POST | `/votes` | Registrar un voto | 201, 404, 409, 422 |
| GET | `/votes` | Listar votos (`skip`, `limit`) | 200 |
| GET | `/votes/statistics` | Estadísticas de la votación | 200 |
| GET | `/votes/chart` | Gráfica de votos (imagen PNG) | 200, 404 |

## Ejemplos de uso

### curl

```bash
# Registrar un votante
curl -X POST http://127.0.0.1:8000/voters \
  -H "Content-Type: application/json" \
  -d '{"name": "Ana Gómez", "email": "ana.gomez@mail.com"}'

# Registrar un candidato
curl -X POST http://127.0.0.1:8000/candidates \
  -H "Content-Type: application/json" \
  -d '{"name": "Carlos Ruiz", "party": "Partido Verde"}'

# Listar candidatos
curl "http://127.0.0.1:8000/candidates?skip=0&limit=10"

# Registrar un voto
curl -X POST http://127.0.0.1:8000/votes \
  -H "Content-Type: application/json" \
  -d '{"voter_id": 1, "candidate_id": 1}'

# Listar votos
curl http://127.0.0.1:8000/votes

# Estadísticas
curl http://127.0.0.1:8000/votes/statistics

# Descargar la gráfica
curl http://127.0.0.1:8000/votes/chart --output chart.png

# Eliminar un votante
curl -X DELETE http://127.0.0.1:8000/voters/1
```

> En Windows PowerShell usa `curl.exe` en lugar de `curl` y escapa las comillas del JSON (`"{\"name\": \"Ana\"}"`), o usa Swagger o Postman.

### Ejemplo de respuesta de `/votes/statistics`

```json
{
  "total_votes": 3,
  "total_voters_who_voted": 3,
  "total_registered_voters": 5,
  "candidates": [
    {"candidate_id": 1, "name": "Carlos Ruiz", "party": "Partido Verde", "votes": 2, "percentage": 66.67},
    {"candidate_id": 2, "name": "Laura Mejía", "party": "Alianza Ciudadana", "votes": 1, "percentage": 33.33},
    {"candidate_id": 3, "name": "Pedro Salazar", "party": null, "votes": 0, "percentage": 0.0}
  ]
}
```

## Capturas

### Estadísticas
<img width="1917" height="1015" alt="image" src="https://github.com/user-attachments/assets/1e2bd14f-4775-4814-9386-a687b540285f" />
<img width="1917" height="1017" alt="image" src="https://github.com/user-attachments/assets/a4ea03c2-2661-478e-8169-63b9afb2aca9" />

### Gráfica de votos

<img width="1917" height="1007" alt="image" src="https://github.com/user-attachments/assets/3f5e5ed7-d6f3-4b64-b314-efff88cef3a4" />


## Reglas y decisiones de diseño

- **Un voto por votante:** `has_voted` se marca con un `UPDATE ... WHERE has_voted = false` y además `votes.voter_id` es `UNIQUE`, así dos peticiones simultáneas no pueden duplicar el voto.
- **Consistencia:** el voto, `has_voted` y el contador del candidato se guardan en una sola transacción; si algo falla, no queda nada a medias. El contador se incrementa en la base de datos (`votes = votes + 1`), no en Python.
- **Votante y candidato no pueden ser la misma persona:** como el modelo del candidato no tiene email, la comparación se hace por nombre normalizado (sin espacios extra y sin distinguir mayúsculas). Limitación: dos personas distintas con el mismo nombre chocarían.
- **Eliminar un votante que ya votó:** se elimina también su voto y se descuenta del candidato, para que las estadísticas reflejen los votos reales.
- **Estadísticas y gráfica** se calculan desde la tabla `votes`; los candidatos sin votos aparecen con 0.
- **Códigos HTTP:** `201` creación, `204` borrado, `404` recurso inexistente, `409` conflicto (duplicados), `422` datos inválidos.

## Estructura del proyecto

```
app/
├── main.py            # aplicación FastAPI
├── config.py          # variables de entorno
├── database.py        # conexión y sesión
├── models.py          # modelos SQLAlchemy
├── schemas.py         # esquemas Pydantic
├── routers/           # endpoints (voters, candidates, votes)
└── services/          # generación de la gráfica (pandas)
tests/                 # tests con pytest
docs/                  # capturas
```
