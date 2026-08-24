# SecureLedger Vault — Personal Expense Tracker API

A production-ready FastAPI application for tracking personal income and expenses. Users register, authenticate with JWT, and manage their own transactions with full CRUD and filtering support.

## Features

- User registration and JWT-based login
- Password hashing with Passlib/Bcrypt
- Transaction CRUD (create, read, update, delete)
- Ownership enforcement — users can only access their own transactions
- Filter transactions by type, category, and amount range
- PostgreSQL persistence via SQLAlchemy ORM (Supabase)
- Fully dockerized — runs on port 4000

## Project Structure

```
app/
  core/           # Settings and security (JWT, password hashing)
  database/       # SQLAlchemy engine, session, base
  models/         # User and Transaction ORM models
  schemas/        # Pydantic v2 request/response models
  crud/           # Database operations
  dependencies/   # Auth dependencies (get_current_user)
  routers/        # API route handlers
  main.py         # FastAPI application entry point
tests/            # Pytest test suite
plan/             # Architecture notes (gitignored)
```

## Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose
- A [Supabase](https://supabase.com) project with PostgreSQL

## Supabase Database Setup

1. Create a project at [supabase.com](https://supabase.com)
2. Go to **Project Settings → Database → Connection string**
3. Copy the **URI** connection string (Session or Transaction pooler mode)
4. Replace `[YOUR-PASSWORD]` with your database password
5. If connection fails, append `?sslmode=require` to the URL

## Environment Variables

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Supabase PostgreSQL connection string |
| `SECRET_KEY` | Random secret for JWT signing |
| `ALGORITHM` | JWT algorithm (default: `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry in minutes (default: `30`) |

Example `.env`:

```env
DATABASE_URL=postgresql://postgres.xxxx:yourpassword@aws-0-us-east-1.pooler.supabase.com:6543/postgres
SECRET_KEY=your-super-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Run with Docker Compose

```bash
docker compose up --build
```

The API will be available at:

- **API:** http://localhost:4000
- **Swagger UI:** http://localhost:4000/docs
- **Health check:** http://localhost:4000/health

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login and receive JWT token |

### Transactions (JWT required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/transactions` | Create a transaction |
| GET | `/transactions` | List all user's transactions |
| GET | `/transactions/filter` | Filter by type, category, amount |
| GET | `/transactions/{id}` | Get a specific transaction |
| PUT | `/transactions/{id}` | Update a transaction |
| DELETE | `/transactions/{id}` | Delete a transaction |

## Example Usage

**Register:**

```bash
curl -X POST http://localhost:4000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "email": "john@example.com", "password": "secret123"}'
```

**Login:**

```bash
curl -X POST http://localhost:4000/auth/login \
  -d "username=john&password=secret123"
```

**Create transaction:**

```bash
curl -X POST http://localhost:4000/transactions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Groceries", "amount": 150, "type": "expense", "category": "Food", "date": "2026-01-15"}'
```

**Filter transactions:**

```bash
curl "http://localhost:4000/transactions/filter?type=expense&category=Food&minimum_amount=100" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Running Tests

Tests use an in-memory SQLite database by default (no Supabase required):

```bash
pip install -r requirements.txt
pytest -v
```

Or inside Docker:

```bash
docker compose run --rm api pytest -v
```

To run tests against a real PostgreSQL database, set `TEST_DATABASE_URL`:

```bash
TEST_DATABASE_URL=postgresql://... pytest -v
```

## Tech Stack

- **FastAPI** — Web framework
- **SQLAlchemy** — ORM
- **PostgreSQL (Supabase)** — Database
- **Pydantic v2** — Data validation
- **python-jose** — JWT tokens
- **Passlib + Bcrypt** — Password hashing
- **Pytest + httpx** — Testing
- **Docker** — Containerization
