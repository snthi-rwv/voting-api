# Voting API

Prueba Técnica de NewInntech: Una API para manejar una votación: registrar votantes y candidatos, votar (una sola vez por persona), ver los resultados y generar una gráfica con los votos de cada candidato.

**Hecho con:** Python · FastAPI · PostgreSQL · pandas

## Contenido

1. [¿Qué puede hacer?](#qué-puede-hacer)
2. [Cómo ejecutarlo en tu computador](#cómo-ejecutarlo-en-tu-computador)
3. [Probarlo](#probarlo)
4. [Endpoints disponibles](#endpoints-disponibles)
5. [Acceso con usuario y clave](#acceso-con-usuario-y-clave)
7. [Filtros y paginación](#filtros-y-paginación)
8. [Capturas](#capturas)
9. [Reglas de la votación](#reglas-de-la-votación)
10. [Errores que puede devolver la API](#errores-que-puede-devolver-la-api)
11. [Pruebas automáticas](#pruebas-automáticas)
12. [Estructura del proyecto](#estructura-del-proyecto)
13. [Problemas comunes](#problemas-comunes)

## ¿Qué puede hacer?

- Registrar votantes y candidatos.
- Registrar votos. Cada votante solo puede votar una vez.
- Impedir que una misma persona sea votante y candidato a la vez.
- Mostrar estadísticas: votos por candidato, porcentajes y cuántas personas ya votaron.
- Generar una gráfica de barras con los votos actuales (hecha con pandas).
- Buscar y paginar las listas de votantes y candidatos.
- Proteger las funciones de gestión con usuario y clave (JWT).
- Incluir documentación interactiva (Swagger) para probar todo desde el navegador.

## Cómo ejecutarlo en tu computador

### Lo que necesitas

- Python 3.12 o superior (se desarrolló con 3.14).
- PostgreSQL instalado y funcionando.

### Paso a paso

**1. Descarga el proyecto**

```bash
git clone https://github.com/snthi-rwv/voting-api.git
cd voting-api
```

**2. Crea un entorno virtual** (una "caja" aparte para las librerías del proyecto)

```bash
python -m venv venv
```

Actívalo:

```bash
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac y Linux
```

**3. Instala las librerías**

```bash
pip install -r requirements.txt
```

**4. Crea la base de datos**

En PostgreSQL (por ejemplo desde pgAdmin) crea una base de datos vacía llamada `voting_db`. Las tablas se crean solas al iniciar la API.

**5. Configura tus datos**

Copia el archivo `.env.example` y llámalo `.env`:

```bash
copy .env.example .env         # Windows
cp .env.example .env           # Mac y Linux
```

Abre `.env` y cambia `usuario` y `password` por los de tu PostgreSQL:

```
DATABASE_URL=postgresql+psycopg://usuario:password@localhost:5432/voting_db
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin12345
JWT_SECRET=change-me-please-use-a-long-random-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Qué significa cada línea:

| Variable | Para qué sirve |
|---|---|
| `DATABASE_URL` | Cómo conectarse a tu base de datos |
| `ADMIN_USERNAME` y `ADMIN_PASSWORD` | Usuario y clave para entrar a la API |
| `JWT_SECRET` | Texto secreto con el que se firman los tokens de acceso |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Minutos que dura el acceso antes de pedir login otra vez |

> Los valores de ejemplo sirven para probar en tu computador. Si usas el proyecto en otro lugar, cambia la clave y el secreto.

**6. Inicia la API**

```bash
uvicorn app.main:app --reload
```

Ya está funcionando:

- API: http://127.0.0.1:8000
- Documentación interactiva: http://127.0.0.1:8000/docs

## Probarlo en 2 minutos

La forma más fácil es desde el navegador, sin instalar nada más:

1. Abre http://127.0.0.1:8000/docs
2. Pulsa el botón **Authorize** (arriba a la derecha), escribe el usuario y la clave de tu `.env` (con el ejemplo: `admin` y `admin12345`) y confirma.
3. Crea un votante con `POST /voters` y un candidato con `POST /candidates`. Usa el botón **Try it out**.
4. Registra un voto con `POST /votes`.
5. Mira los resultados en `GET /votes/statistics` y la gráfica en http://127.0.0.1:8000/votes/chart

## Endpoints disponibles

Un endpoint es una dirección de la API a la que se le pide o se le envía información.

| Método | Dirección | Qué hace | ¿Pide acceso? |
|---|---|---|---|
| POST | `/auth/login` | Entrar con usuario y clave y recibir un token | No |
| POST | `/voters` | Registrar un votante | Sí |
| GET | `/voters` | Listar votantes (con filtros) | Sí |
| DELETE | `/voters/{id}` | Eliminar un votante | Sí |
| POST | `/candidates` | Registrar un candidato | Sí |
| GET | `/candidates` | Listar candidatos (con filtros) | Sí |
| POST | `/votes` | Registrar un voto | Sí |
| GET | `/votes` | Ver todos los votos emitidos | Sí |
| GET | `/votes/statistics` | Ver estadísticas de la votación | No |
| GET | `/votes/chart` | Ver la gráfica de votos (imagen PNG) | No |

Los resultados (estadísticas y gráfica) son públicos a propósito: en una elección, cualquiera debería poder ver cómo va.

### Datos que se guardan

**Votante:** `id`, `name` (obligatorio), `email` (obligatorio y único), `has_voted` (empieza en `false`).

**Candidato:** `id`, `name` (obligatorio), `party` (opcional), `votes` (empieza en 0).

**Voto:** `id`, `voter_id` (quién votó) y `candidate_id` (por quién votó).

## Acceso con usuario y clave

Las funciones de gestión necesitan que te identifiques. El proceso es:

1. Envías tu usuario y clave a `/auth/login`.
2. La API te devuelve un **token**, que es como una llave temporal.
3. Envías ese token en cada petición protegida.

Si no envías token, o está vencido o es falso, la API responde con error `401`.

El usuario y la clave se definen en el archivo `.env`. Si usaste el `.env.example`, son `admin` y `admin12345`.

## Filtros y paginación

Las listas de votantes y candidatos se pueden filtrar y dividir en páginas.

**Paginación (en todas las listas):**

- `skip`: cuántos resultados saltar (por defecto 0).
- `limit`: cuántos resultados traer (por defecto 50, máximo 200).
- El total de resultados, sin dividir en páginas, viene en el encabezado de la respuesta `X-Total-Count`.

**Filtros disponibles:**

| Lista | Filtros |
|---|---|
| `GET /candidates` | `name` y `party`: buscan texto parcial, sin importar mayúsculas |
| `GET /voters` | `name` y `email`: buscan texto parcial. `has_voted`: `true` o `false` |

**Ejemplos:**

```bash
# Candidatos del partido "verde", primeros 10
curl "http://127.0.0.1:8000/candidates?party=verde&skip=0&limit=10" \
  -H "Authorization: Bearer $TOKEN"

# Votantes que todavía no han votado y cuyo nombre contiene "ana"
curl "http://127.0.0.1:8000/voters?has_voted=false&name=ana" \
  -H "Authorization: Bearer $TOKEN"
```

## Capturas

### Estadísticas

<img width="1593" height="495" alt="image" src="https://github.com/user-attachments/assets/137fa04a-8cae-4d40-a5b6-90acfd72d334" />


### Gráfica de votos

La gráfica muestra a los candidatos en el eje horizontal (X) y la cantidad de votos en el eje vertical (Y). Siempre refleja el estado actual de la votación, y los candidatos sin votos aparecen con una barra en cero.

<img width="1207" height="757" alt="image" src="https://github.com/user-attachments/assets/ce307f4d-c088-4939-83ea-8dcb5e4ec488" />


## Reglas de la votación

- **Un voto por persona.** Si alguien intenta votar de nuevo, la API lo rechaza. Esto está protegido en el código y también en la base de datos, para que ni dos peticiones simultáneas puedan duplicar un voto.
- **Todo o nada.** Al votar, se guarda el voto, se marca al votante como "ya votó" y se suma 1 al candidato. Estas tres cosas ocurren juntas: si una falla, ninguna se guarda.
- **Votante o candidato, no ambos.** Como el candidato no tiene correo, la API compara los nombres (sin importar mayúsculas ni espacios de más). Limitación: dos personas distintas con el mismo nombre se bloquearían entre sí.
- **Si se elimina un votante que ya votó,** su voto también se elimina y se resta al candidato, para que los resultados sigan siendo reales.
- **Las estadísticas y la gráfica se calculan con los votos registrados,** no con números guardados aparte.

## Errores que puede devolver la API

| Código | Significa | Ejemplo |
|---|---|---|
| 200 | Todo salió bien | Consultar candidatos |
| 201 | Se creó correctamente | Registrar un votante |
| 204 | Se eliminó correctamente | Eliminar un votante |
| 401 | Falta el token o no es válido | Pedir `/candidates` sin hacer login |
| 404 | No existe lo que se busca | Votar por un candidato que no existe |
| 409 | Conflicto con algo existente | Votar dos veces, o repetir un email |
| 422 | Los datos enviados no son válidos | Email mal escrito o nombre vacío |

Los errores traen un mensaje explicando qué pasó, por ejemplo: `{"detail": "Este votante ya emitió su voto"}`.

## Pruebas automáticas

El proyecto incluye pruebas que verifican las reglas importantes: votos únicos, candidato inexistente, filtros, paginación, acceso con token y gráfica.

```bash
pytest -v
```

Estas pruebas usan una base de datos temporal en memoria, así que no tocan tu base de datos real ni necesitan tu archivo `.env`.

## Estructura del proyecto

```
voting-api/
├── app/
│   ├── main.py          # Arranque de la aplicación
│   ├── config.py        # Lectura de la configuración (.env)
│   ├── database.py      # Conexión a la base de datos
│   ├── models.py        # Tablas: votantes, candidatos y votos
│   ├── schemas.py       # Forma de los datos que entran y salen
│   ├── security.py      # Login y verificación del token
│   ├── utils.py         # Ayudas para búsquedas y conteos
│   ├── routers/         # Los endpoints, uno por tema
│   │   ├── auth.py
│   │   ├── voters.py
│   │   ├── candidates.py
│   │   └── votes.py
│   └── services/
│       └── chart_service.py   # Genera la gráfica con pandas
├── tests/               # Pruebas automáticas
├── docs/                # Capturas para este README
├── .env.example         # Plantilla de configuración
├── requirements.txt     # Lista de librerías
└── pytest.ini           # Configuración de las pruebas
```

## Problemas comunes

**Al iniciar sale un error que menciona `admin_username` o `jwt_secret`.**
Falta alguna línea en tu `.env`. Compáralo con `.env.example` y copia las líneas que falten.

**Sale `password authentication failed` o `connection refused`.**
El usuario o la clave de `DATABASE_URL` no coinciden con tu PostgreSQL, o PostgreSQL no está encendido.

**Sale `database "voting_db" does not exist`.**
Falta crear la base de datos vacía (paso 4).

**Todas las peticiones dan `401`.**
Falta el token. Haz login y envía el encabezado `Authorization: Bearer TU_TOKEN`, o usa el botón **Authorize** en `/docs`.

**Cambié un modelo y las tablas no se actualizan.**
Las tablas solo se crean la primera vez. Durante el desarrollo, borra las tablas en PostgreSQL y reinicia la API para que se creen de nuevo.
