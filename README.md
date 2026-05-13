# 🏥 Clinic Management System

> 🚧 This project is currently under development and is not finished yet.

A modern clinic management backend built with Django, PostgreSQL, Redis, Docker, and JWT authentication.

---

## ✨ Features

- 🔐 JWT Authentication
- 👤 Custom User Model with UUID
- 🗄 PostgreSQL Database
- ⚡ Redis Integration
- 🐳 Dockerized Environment
- 📦 Environment-based Configuration
- 🌍 CORS & CSRF Configuration
- 📩 SMS Service Support
- 💳 Payment Gateway Ready
- ⏳ Celery & Background Tasks Ready

---

## 🛠 Tech Stack

- Python 3.12
- Django
- PostgreSQL
- Redis
- Docker & Docker Compose
- JWT Authentication
- Celery

---

## 📁 Environment Variables

Create a `.env` file based on `.env.sample`.

Example:

```env
DJANGO_SECRET_KEY=your-secret-key
DEBUG=True

POSTGRES_DB=clinic_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432

REDIS_HOST=127.0.0.1
REDIS_PORT=6379
```

---

## 🚀 Run with Docker

```bash
docker compose up --build
```

---

## 📌 Useful Commands

### Create Superuser

```bash
docker compose exec web python manage.py createsuperuser
```

### Run Migrations

```bash
docker compose exec web python manage.py migrate
```

### Open Django Shell

```bash
docker compose exec web python manage.py shell
```

---

## 🧱 Project Structure

```bash
.
├── core/
├── users/
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
└── .env
```

---

## ⚠ Notes

- Uses UUID as primary keys.
- PostgreSQL and Redis run in separate containers.
- Static files are collected automatically on startup.

---

## 📄 License

MIT License
