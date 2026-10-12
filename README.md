# DispatchLens — Carrier Intelligence Backend

A lightweight Django REST Framework proof of concept for **DispatchLens**, a carrier intelligence tool designed to help truck dispatchers retrieve, organize, and analyze carrier information through a unified API.

## Features

- **Carrier Lookup:** Retrieve carrier information using a DOT number.
- **Multi-Source Data Aggregation:** Combines information from multiple data endpoints into a unified carrier record.
- **Data Normalization:** Converts raw responses into a consistent, structured format.
- **MC Number Extraction:** Identifies MC prefixes and numeric docket identifiers.
- **Authority & Operating Status:** Organizes carrier authority and operating-status information.
- **Insurance Information:** Structures available insurance requirements and filing details.
- **Safety & Compliance Data:** Supports structured safety records, inspection statistics, and crash information.
- **Equipment & Fleet Information:** Stores fleet size, driver counts, and related carrier attributes.
- **Database Persistence:** Supports MySQL and SQLite for storing normalized carrier records.
- **Error Handling:** Handles invalid input, missing records, request timeouts, and service errors without exposing sensitive credentials.
- **Automated Testing:** Includes unit tests with mocked external requests to verify data processing, error handling, and database operations.

## Tech Stack

- Python 3.10+
- Django
- Django REST Framework
- MySQL / SQLite
- Python `requests`
- Environment-based configuration
- Automated unit testing

## Project Structure

```text
dispatchlens/
├── manage.py
├── .env
├── .env.example
├── requirements.txt
├── README.md
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── carriers/
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── serializers.py
    ├── urls.py
    ├── views.py
    ├── tests.py
    └── services/
        └── fmcsa_service.py
```

## Setup & Installation

### Prerequisites

- Python 3.10 or newer
- pip

### 1. Create a Virtual Environment

**Windows (PowerShell)**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt)**

```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**macOS / Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a local `.env` file from the provided example.

**Windows (PowerShell)**

```powershell
Copy-Item .env.example .env
```

**macOS / Linux**

```bash
cp .env.example .env
```

Configure your local environment:

```env
SECRET_KEY=replace_with_a_secure_secret
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_ENGINE=django.db.backends.mysql
DB_NAME=dispatchlens_db
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306
```

Configure any required external service credentials using the appropriate environment variables. Never commit real credentials or production secrets to version control.

**Database configuration:** The application can use SQLite for local development or MySQL when configured. Confirm that your Django settings support the intended fallback behavior.

### 4. Apply Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Start the Development Server

```bash
python manage.py runserver
```

The local development server will be available at:

`http://127.0.0.1:8000/`

## API Documentation

### Retrieve Carrier Information

**Endpoint**

```http
GET /api/carriers/<dot_number>/
```

**Example request**

```http
GET /api/carriers/4202109/
```

### Successful Response

Returns a normalized carrier record containing available information such as:

- DOT and MC identifiers
- Legal business name and DBA
- Operating and authority status
- Insurance filing details
- Physical address
- Driver and vehicle counts
- Safety ratings and inspection statistics
- Crash statistics
- Operation classifications
- Cargo categories
- Record creation and update timestamps

The exact fields depend on the information available for the requested carrier.

### Error Responses

**400 — Invalid Input**

```json
{
  "success": false,
  "error": "Invalid DOT number"
}
```

**404 — Carrier Not Found**

```json
{
  "success": false,
  "error": "Carrier not found"
}
```

**503 — Service Unavailable**

```json
{
  "success": false,
  "error": "Carrier information service temporarily unavailable"
}
```

## Running Automated Tests

Execute the test suite with:

```bash
python manage.py test
```

The tests cover:

1. Successful carrier lookups and data normalization.
2. Handling of empty or missing optional data.
3. Invalid DOT number validation.
4. External service errors.
5. Network connection timeouts.
6. MC identifier parsing.
7. Serialization and database persistence.

## Security & Configuration

- Store credentials and secret keys in environment variables.
- Keep `.env` and other sensitive configuration files out of Git.
- Use secure settings for production deployments.
- Avoid exposing internal exception details or credentials in API responses.
- Validate and sanitize incoming request parameters.

## Project Status

**Proof of Concept (PoC)**

DispatchLens is being developed to simplify carrier research through structured data retrieval, normalization, and a unified API. The backend provides a foundation for future search, filtering, and carrier discovery capabilities.
