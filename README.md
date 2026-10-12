# DispatchLens - FMCSA Backend Integration Proof-of-Concept

A lightweight Django REST Framework proof-of-concept for **DispatchLens** that connects to the official **FMCSA QCMobile API**, retrieves carrier information using a DOT number, combines responses across multiple FMCSA endpoints, normalizes carrier records, and persists them into a MySQL/SQLite compatible database.

---

## Features

- **Official FMCSA Integration**: Connects to `https://mobile.fmcsa.dot.gov/qc/services`.
- **Multi-Endpoint Aggregation**: Queries and merges six FMCSA endpoints:
  - `/carriers/{DOT}`
  - `/carriers/{DOT}/basics`
  - `/carriers/{DOT}/cargo-carried`
  - `/carriers/{DOT}/operation-classification`
  - `/carriers/{DOT}/docket-numbers`
  - `/carriers/{DOT}/authority`
- **Data Normalization**: Converts raw FMCSA JSON into a standardized carrier structure.
- **MC Number Extraction**: Automatically extracts prefix (e.g. `MC`) and numeric docket ID (e.g. `1670397`).
- **Database Persistence**: Stores normalized records in a MySQL-compatible `Carrier` model.
- **Robust Error Handling**: Handles network timeouts, HTTP errors, invalid DOT formats, and missing optional endpoints without leaking `FMCSA_WEB_KEY`.
- **Automated Mock Test Suite**: Includes a unit test suite mocking FMCSA responses.

---

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

---

## Setup & Installation

### 1. Prerequisites

- Python 3.10+
- `pip` package manager

### 2. Create and Activate Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables (`.env`)

Copy `.env.example` to create `.env`:

```bash
# On Windows PowerShell
Copy-Item .env.example .env

# On Linux/macOS
cp .env.example .env
```

Open `.env` and set your `FMCSA_WEB_KEY`:

```env
FMCSA_WEB_KEY=your_actual_fmcsa_web_key
SECRET_KEY=django-insecure-dispatchlens-poc-key-2026
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# MySQL Database Configuration (Optional: defaults to SQLite if DB_NAME is omitted)
DB_ENGINE=django.db.backends.mysql
DB_NAME=dispatchlens_db
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306
```

> **Note**: If `DB_NAME` is left blank or omitted, Django automatically falls back to an SQLite database (`db.sqlite3`), allowing instant out-of-the-box local testing.

### 5. Run Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## Running the Server

Start the Django development server:

```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`.

---

## API Documentation

### Get Normalized Carrier Information

- **Endpoint**: `GET /api/carriers/<dot_number>/`
- **Example Request**:
  ```text
  GET http://127.0.0.1:8000/api/carriers/4202109/
  ```

#### Example Success Response (HTTP 200 OK):

```json
{
  "success": true,
  "carrier": {
    "dot_number": 4202109,
    "mc_number": 1670397,
    "mc_prefix": "MC",
    "legal_name": "RP TRANSPORT LLC",
    "dba_name": null,
    "allowed_to_operate": true,
    "carrier_operation_code": "C",
    "carrier_operation_description": "Interstate",
    "common_authority_status": "A",
    "contract_authority_status": "N",
    "broker_authority_status": "N",
    "authorized_for_property": true,
    "authorized_for_broker": false,
    "authorized_for_household_goods": false,
    "authorized_for_passenger": false,
    "phy_street": "123 MAIN ST",
    "phy_city": "MISSION",
    "phy_state": "TX",
    "phy_zipcode": "78573",
    "phy_country": "US",
    "total_drivers": 5,
    "total_power_units": 3,
    "bipd_insurance_on_file": "Y",
    "bipd_insurance_required": "Y",
    "bipd_required_amount": 750000,
    "cargo_insurance_on_file": "N",
    "cargo_insurance_required": "N",
    "bond_insurance_on_file": "N",
    "bond_insurance_required": "N",
    "crash_total": 0,
    "fatal_crash": 0,
    "inj_crash": 0,
    "towaway_crash": 0,
    "driver_insp": 10,
    "driver_oos_insp": 1,
    "driver_oos_rate": 10.0,
    "driver_oos_rate_national_average": 5.5,
    "vehicle_insp": 15,
    "vehicle_oos_insp": 2,
    "vehicle_oos_rate": 13.3,
    "vehicle_oos_rate_national_average": 20.1,
    "hazmat_insp": 0,
    "hazmat_oos_insp": 0,
    "hazmat_oos_rate": null,
    "hazmat_oos_rate_national_average": null,
    "safety_rating": "SATISFACTORY",
    "safety_rating_date": "2022-01-15",
    "oos_date": null,
    "status_code": "A",
    "operation_classification": [
      "Authorized For Hire"
    ],
    "cargo_carried": [
      "General Freight"
    ],
    "created_at": "2026-10-08T21:00:00Z",
    "updated_at": "2026-10-08T21:00:00Z"
  }
}
```

---

### Error Responses

#### 1. Invalid DOT Number (HTTP 400 Bad Request)
```json
{
  "success": false,
  "error": "Invalid DOT number"
}
```

#### 2. Carrier Not Found (HTTP 404 Not Found)
```json
{
  "success": false,
  "error": "Carrier not found"
}
```

#### 3. FMCSA Service Unavailable (HTTP 503 Service Unavailable)
```json
{
  "success": false,
  "error": "FMCSA service temporarily unavailable"
}
```

---

## Running Automated Tests

Run the Django test suite (which mocks all FMCSA HTTP requests):

```bash
python manage.py test
```

### Test Coverage Highlights
1. Successful carrier lookup & data normalization.
2. Handling carrier endpoints with empty content arrays.
3. Validation of invalid DOT numbers.
4. Handling FMCSA HTTP 500 API errors.
5. Handling FMCSA connection timeouts.
6. Docket number / MC prefix and number parsing.
7. Serializer & database persistence verification.
