<div align="center">

# SecureLedger Vault

### Personal Expense Tracker API

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![JWT](https://img.shields.io/badge/JWT-Auth-black?style=for-the-badge&logo=jsonwebtokens)](https://jwt.io/)
[![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

**A production-ready, fully dockerized FastAPI backend for tracking personal income and expenses with JWT authentication, ownership enforcement, and advanced filtering.**

[Features](#-features) ·
[Tech Stack](#-tech-stack) ·
[Project Structure](#-project-structure) ·
[Docker Setup](#-docker-setup) ·
[API Reference](#-api-reference) ·
[Testing](#-testing) ·
[License](#-license)

---

</div>

## Overview

**SecureLedger Vault** is a modular Personal Expense Tracker API built with FastAPI and PostgreSQL (Supabase). Users can register, authenticate via JWT, and manage their own income and expense records with full CRUD operations, query-based filtering, and strict data isolation — each user can only access their own transactions.

Designed for real-world deployment with Docker Compose, environment-based configuration, and a comprehensive pytest suite.

---

## Features

| Category | Capability |
|----------|------------|
| **Authentication** | User registration, JWT login, bcrypt password hashing |
| **Authorization** | Per-user ownership — users can only read/write their own data |
| **Transactions** | Full CRUD — create, list, get by ID, update, delete |
| **Filtering** | Query by `type`, `category`, `minimum_amount`, `maximum_amount` |
| **Validation** | Pydantic v2 schemas with strict field validation |
| **Database** | SQLAlchemy ORM with PostgreSQL (Supabase remote) |
| **DevOps** | Dockerized — single command launch on port `4000` |
| **Testing** | 25 pytest cases covering auth, CRUD, ownership, and filters |
| **Docs** | Auto-generated Swagger UI at `/docs` |

---

## Tech Stack

<div align="center">

| | Technology | Role |
|:---:|:---|:---|
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/fastapi/fastapi-original.svg" width="32" alt="FastAPI"/> | **FastAPI** | High-performance async web framework |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" width="32" alt="Python"/> | **Python 3.11+** | Core runtime |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/postgresql/postgresql-original.svg" width="32" alt="PostgreSQL"/> | **PostgreSQL** | Relational database (via Supabase) |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/sqlalchemy/sqlalchemy-original.svg" width="32" alt="SQLAlchemy"/> | **SQLAlchemy** | ORM and database abstraction |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/docker/docker-original.svg" width="32" alt="Docker"/> | **Docker** | Containerization and deployment |
| | **Pydantic v2** | Request/response data validation |
| | **python-jose** | JWT token creation and verification |
| | **Passlib + Bcrypt** | Secure password hashing |
| | **Uvicorn** | ASGI production server |
| | **Pytest + httpx** | Automated API testing |

</div>

---

## Project Structure

```
SecureLedger-Vault-FastAPI-Financial-Governance-Engine/
│
├── app/                              # Application source code
│   ├── __init__.py
│   ├── main.py                       # FastAPI app entry point, lifespan, routers
│   │
│   ├── core/                         # Core configuration and security
│   │   ├── __init__.py
│   │   ├── config.py                 # pydantic-settings (DATABASE_URL, JWT secrets)
│   │   └── security.py               # Password hashing, JWT encode/decode
│   │
│   ├── database/                     # Database engine and session management
│   │   ├── __init__.py
│   │   ├── base.py                   # SQLAlchemy declarative Base
│   │   └── session.py                # Engine, SessionLocal, get_db dependency
│   │
│   ├── models/                       # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py                   # User table (id, username, email, hashed_password)
│   │   └── transaction.py            # Transaction table (title, amount, type, category, date, owner_id)
│   │
│   ├── schemas/                      # Pydantic v2 request/response schemas
│   │   ├── __init__.py
│   │   ├── user.py                   # UserCreate, UserResponse, Token, TokenData
│   │   └── transaction.py            # TransactionCreate, Update, Response, MessageResponse
│   │
│   ├── crud/                         # Database CRUD operations
│   │   ├── __init__.py
│   │   ├── user.py                   # get_user_by_username, create_user, etc.
│   │   └── transaction.py            # create, get, update, delete, filter
│   │
│   ├── dependencies/                 # FastAPI dependency injection
│   │   ├── __init__.py
│   │   └── auth.py                   # OAuth2PasswordBearer, get_current_user
│   │
│   └── routers/                      # API route handlers
│       ├── __init__.py
│       ├── auth.py                   # POST /auth/register, POST /auth/login
│       └── transactions.py           # CRUD + GET /transactions/filter
│
├── tests/                            # Pytest test suite
│   ├── __init__.py
│   ├── conftest.py                   # Fixtures: client, db, auth_headers
│   ├── test_auth.py                  # Register + login tests
│   └── test_transactions.py          # CRUD, ownership, filter tests
│
├── plan/                             # Architecture notes (gitignored)
│   └── ARCHITECTURE.md
│
├── .env.example                      # Environment variable template
├── .gitignore                        # Git ignore rules
├── docker-compose.yml                # Docker Compose service definition
├── Dockerfile                        # Multi-stage-ready container build
├── LICENSE                           # MIT License
├── README.md                         # Project documentation
└── requirements.txt                  # Python dependencies
```

---

## Architecture

```mermaid
flowchart LR
    Client["Client / Swagger UI"] -->|"HTTP :4000"| API["FastAPI App"]
    API --> Auth["Auth Router"]
    API --> Txn["Transactions Router"]
    Auth --> Security["JWT + Bcrypt"]
    Txn --> Deps["get_current_user"]
    Deps --> Security
    Auth --> CRUD["CRUD Layer"]
    Txn --> CRUD
    CRUD --> ORM["SQLAlchemy Models"]
    ORM --> DB[("Supabase PostgreSQL")]
```

**Request flow:** Client authenticates → receives JWT → sends Bearer token on protected routes → FastAPI validates token → CRUD operations scoped to `owner_id`.

---

## Prerequisites

Before you begin, ensure the following are installed:

| Tool | Version | Purpose |
|------|---------|---------|
| [Docker](https://www.docker.com/get-started/) | Latest | Container runtime |
| [Docker Compose](https://docs.docker.com/compose/) | v2+ | Multi-container orchestration |
| [Supabase Account](https://supabase.com) | Free tier works | Remote PostgreSQL database |
| [Git](https://git-scm.com/) | Latest | Clone the repository |

---

## Docker Setup

### Step 1 — Clone the Repository

```bash
git clone https://github.com/your-username/SecureLedger-Vault-FastAPI-Financial-Governance-Engine.git
cd SecureLedger-Vault-FastAPI-Financial-Governance-Engine
```

### Step 2 — Configure Supabase Database

1. Sign in at [supabase.com](https://supabase.com) and create a new project
2. Navigate to **Project Settings → Database → Connection string**
3. Select **URI** format (Transaction pooler recommended for serverless)
4. Copy the connection string and replace `[YOUR-PASSWORD]` with your database password
5. If SSL errors occur, append `?sslmode=require` to the URL

### Step 3 — Create Environment File

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
DATABASE_URL=postgresql://postgres.xxxx:yourpassword@aws-0-us-east-1.pooler.supabase.com:6543/postgres
SECRET_KEY=your-super-secret-key-minimum-32-characters-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

| Variable | Required | Description |
|----------|:--------:|-------------|
| `DATABASE_URL` | Yes | Supabase PostgreSQL connection URI |
| `SECRET_KEY` | Yes | Random secret for signing JWT tokens |
| `ALGORITHM` | No | JWT algorithm (default: `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Token lifetime in minutes (default: `30`) |

### Step 4 — Build and Run

```bash
docker compose up --build
```

Expected output:

```
api-1  | INFO:     Uvicorn running on http://0.0.0.0:4000
api-1  | INFO:     Application startup complete.
```

### Step 5 — Verify the Deployment

| Endpoint | URL |
|----------|-----|
| Health Check | http://localhost:4000/health |
| Swagger UI | http://localhost:4000/docs |
| ReDoc | http://localhost:4000/redoc |
| OpenAPI JSON | http://localhost:4000/openapi.json |

### Docker Commands Reference

```bash
# Start in detached (background) mode
docker compose up --build -d

# View container logs
docker compose logs -f api

# Stop all services
docker compose down

# Rebuild after code changes
docker compose up --build

# Run tests inside the container
docker compose run --rm api pytest -v
```

---

## API Reference

### Authentication

| Method | Endpoint | Auth | Description |
|:------:|----------|:----:|-------------|
| `POST` | `/auth/register` | No | Register a new user account |
| `POST` | `/auth/login` | No | Login and receive a JWT access token |

### Transactions

| Method | Endpoint | Auth | Description |
|:------:|----------|:----:|-------------|
| `POST` | `/transactions` | Yes | Create a new transaction |
| `GET` | `/transactions` | Yes | List all transactions for the current user |
| `GET` | `/transactions/filter` | Yes | Filter by type, category, amount range |
| `GET` | `/transactions/{id}` | Yes | Get a specific transaction by ID |
| `PUT` | `/transactions/{id}` | Yes | Update an existing transaction |
| `DELETE` | `/transactions/{id}` | Yes | Delete a transaction |

### Filter Query Parameters

| Parameter | Type | Example | Description |
|-----------|------|---------|-------------|
| `type` | string | `expense` | Filter by `"income"` or `"expense"` |
| `category` | string | `Food` | Filter by category name |
| `minimum_amount` | float | `100` | Minimum transaction amount |
| `maximum_amount` | float | `5000` | Maximum transaction amount |

---

## Example Usage

<details>
<summary><strong>Register a new user</strong></summary>

```bash
curl -X POST http://localhost:4000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "email": "john@example.com",
    "password": "secret123"
  }'
```

**Response `201 Created`:**

```json
{
  "id": 1,
  "username": "john",
  "email": "john@example.com"
}
```

</details>

<details>
<summary><strong>Login and obtain JWT token</strong></summary>

```bash
curl -X POST http://localhost:4000/auth/login \
  -d "username=john&password=secret123"
```

**Response `200 OK`:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

</details>

<details>
<summary><strong>Create a transaction</strong></summary>

```bash
curl -X POST http://localhost:4000/transactions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Groceries",
    "amount": 150,
    "type": "expense",
    "category": "Food",
    "date": "2026-01-15"
  }'
```

</details>

<details>
<summary><strong>Filter transactions</strong></summary>

```bash
curl "http://localhost:4000/transactions/filter?type=expense&category=Food&minimum_amount=100&maximum_amount=5000" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

</details>

<details>
<summary><strong>Update a transaction</strong></summary>

```bash
curl -X PUT http://localhost:4000/transactions/1 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Groceries", "amount": 200}'
```

</details>

<details>
<summary><strong>Delete a transaction</strong></summary>

```bash
curl -X DELETE http://localhost:4000/transactions/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response `200 OK`:**

```json
{
  "message": "Transaction deleted successfully"
}
```

</details>

---

## Testing

The test suite uses an in-memory SQLite database and FakeRedis by default — **no Supabase or Redis connection required**.

### Install test dependencies

```bash
pip install -r requirements.txt
```

### Run all tests

```bash
python -m pytest -v
```

Expected output:

```
======================== 25 passed ========================
```

### Run specific test files

```bash
# Authentication tests only
python -m pytest tests/test_auth.py -v

# Transaction tests only
python -m pytest tests/test_transactions.py -v
```

### Run specific test classes

```bash
# Create transaction tests
python -m pytest tests/test_transactions.py::TestCreateTransaction -v

# Get all transactions tests
python -m pytest tests/test_transactions.py::TestGetTransactions -v

# Get transaction by ID tests
python -m pytest tests/test_transactions.py::TestGetTransactionById -v

# Update transaction tests
python -m pytest tests/test_transactions.py::TestUpdateTransaction -v

# Delete transaction tests
python -m pytest tests/test_transactions.py::TestDeleteTransaction -v

# Filter transaction tests
python -m pytest tests/test_transactions.py::TestFilterTransactions -v
```

### Run a single test case

```bash
python -m pytest tests/test_transactions.py::TestCreateTransaction::test_create_transaction_success -v
```

### Run with short summary

```bash
python -m pytest -q
```

### Run with coverage report (optional)

```bash
pip install pytest-cov
python -m pytest -v --cov=app --cov-report=term-missing
```

### Docker testing

```bash
# Run all tests inside the API container
docker compose run --rm api pytest -v

# Run transaction tests only
docker compose run --rm api pytest tests/test_transactions.py -v

# Run auth tests only
docker compose run --rm api pytest tests/test_auth.py -v
```

### Test against PostgreSQL (optional)

```bash
TEST_DATABASE_URL=postgresql://user:pass@host:5432/dbname python -m pytest -v
```

### Test coverage summary

| # | Test Case | File | Class |
|:-:|-----------|------|-------|
| 1 | Register + login returns JWT | `test_auth.py` | — |
| 2 | Same device returns same token | `test_auth.py` | — |
| 3 | Refresh token flow | `test_auth.py` | — |
| 4 | Logout revokes token | `test_auth.py` | — |
| 5 | Create transaction (POST) | `test_transactions.py` | `TestCreateTransaction` |
| 6 | Get all transactions (GET list) | `test_transactions.py` | `TestGetTransactions` |
| 7 | Get transaction by ID (GET) | `test_transactions.py` | `TestGetTransactionById` |
| 8 | Update transaction (PUT) | `test_transactions.py` | `TestUpdateTransaction` |
| 9 | Delete transaction (DELETE) | `test_transactions.py` | `TestDeleteTransaction` |
| 10 | Filter by type/category/amount | `test_transactions.py` | `TestFilterTransactions` |

**Module 24 required tests (10 marks):** Create, Get list, Get by ID, Update — all covered in `tests/test_transactions.py`.

---

## Database Models

### User

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Primary key |
| `username` | str | Unique username |
| `email` | str | Email address |
| `hashed_password` | str | Bcrypt-hashed password (never returned in API) |

### Transaction

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Primary key |
| `title` | str | Transaction title |
| `amount` | float | Positive amount |
| `type` | str | `"income"` or `"expense"` |
| `category` | str | Category label |
| `date` | date | Transaction date |
| `owner_id` | int | Foreign key → `users.id` |

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for full details.

```
Copyright (c) 2026 Md. Nazmus Sakib (engrsakib)
```

---

<div align="center">

### Author

**Md. Nazmus Sakib**

[![GitHub](https://img.shields.io/badge/GitHub-engrsakib-181717?style=for-the-badge&logo=github)](https://github.com/engrsakib)
[![Website](https://img.shields.io/badge/Website-engrsakib.com-0A66C2?style=for-the-badge&logo=googlechrome&logoColor=white)](https://engrsakib.com)

---

Built with FastAPI · Secured with JWT · Powered by Supabase PostgreSQL

**SecureLedger Vault** © 2026

</div>
