
# Ajaia Docs

A collaborative document management and editing application built as part of the Ajaia AI-Native Full Stack Developer assessment.

Ajaia Docs allows users to create, edit, organize, upload, and share documents through a web-based interface.

## Features

### User Authentication
- Login using demo accounts.
- Secure password-based authentication.
- User-specific document access.

### Document Management
- Create new documents.
- Rename existing documents.
- Edit document content.
- View documents owned by the current user.
- Access documents shared by other users.
- Automatically save document changes.

### Rich Text Editing
- Bold, italic, and underline formatting.
- Headings.
- Bulleted and numbered lists.
- Structured document editing.

### File Upload
- Upload documents through the application.
- Access uploaded files through the document interface.

### Document Sharing
- Share documents with other users.
- Assign viewer or editor permissions.
- Distinguish owned documents from shared documents.
- Control access based on sharing permissions.

## Demo Accounts

All demo accounts use the following password:

`password123`

| Name | Email | Password |
|---|---|---|
| Shiva | shiva@example.com | password123 |
| Priya | priya@example.com | password123 |
| Sai | sai@example.com | password123 |

## Technology Stack

### Frontend
- React
- TypeScript
- Vite
- Rich text editor

### Backend
- Python
- FastAPI
- SQLAlchemy
- REST APIs

### Database
- PostgreSQL
- SQLAlchemy ORM

### Deployment
- Render
- Docker

## Project Structure

```text
ajaia-docs/
├── client/
│   ├── src/
│   └── tests/
├── server/
│   ├── app/
│   ├── tests/
│   └── requirements-dev.txt
├── docs/
│   ├── ARCHITECTURE.md
│   └── AI_USAGE.md
├── Dockerfile
├── render.yaml
├── .env.example
└── README.md
```

## Local Setup

### Prerequisites

- Python 3.12+
- Node.js and npm
- PostgreSQL

### 1. Clone the repository

```bash
git clone https://github.com/shiva-priya123/ajaia-docs.git
cd ajaia-docs
```

### 2. Backend setup

```bash
cd server
python -m venv .venv
```

Activate the virtual environment.

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements-dev.txt
```

Configure the environment variables using the provided `.env.example` file.

Start the backend:

```bash
uvicorn app.main:app --reload
```

The backend API documentation is available at:

`http://localhost:8000/docs`

### 3. Frontend setup

Open another terminal:

```bash
cd client
npm install
npm run dev
```

Open the frontend at:

`http://localhost:5173`

## Running Tests

### Backend tests

From the `server` directory:

```bash
python -m pytest -q
```

### Frontend tests

From the `client` directory:

```bash
npm test
```

Refer to the client package scripts if the test command differs.

## Deployment

The application is configured for deployment using Render.

The repository includes:
- `Dockerfile` for containerized deployment.
- `render.yaml` for Render Blueprint configuration.
- `.env.example` for environment configuration.

Configure the required environment variables and database connection in Render before deploying.

## Documentation

Additional project documentation:

- [Architecture](docs/ARCHITECTURE.md)
- [AI Workflow and Usage](docs/AI_USAGE.md)

## GitHub Repository

[https://github.com/shiva-priya123/ajaia-docs](https://github.com/shiva-priya123/ajaia-docs)

## Author

**Shiv Priya Pillalamarri**

Built for the Ajaia AI-Native Full Stack Developer assessment.
