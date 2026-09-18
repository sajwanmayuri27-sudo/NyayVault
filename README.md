# NyayVault 🏛️🔒

> **Secure Legal Evidence & Case Management System** with Blockchain Anchoring, Automated Redaction, and Multilingual Support. Developed for the Smart India Hackathon (SIH).

---

## 🚀 Overview

**NyayVault** is a high-security digital vault and case management platform designed for legal professionals, investigators, and judicial workflows. It guarantees absolute chain of custody for digital evidence, offers tamper-proof blockchain anchoring, provides automated document redaction, and streamlines end-to-end case tracking through a modern dashboard interface.

---

## ✨ Key Features

* **Role-Based Access Control (RBAC)**: Secure authentication and granular permission management for lawyers, judges, and administrative staff (`auth.py`, `users.py`).
* **Comprehensive Case Tracking**: Centralized repository for managing active legal files, linking evidence, and monitoring chronological updates (`cases.py`, `documents.py`).
* **Blockchain Evidence Anchoring**: Cryptographic file hashing combined with smart contracts (`HashAnchor.sol`) to anchor evidence integrity on a decentralized ledger (`blockchain_anchor.py`).
* **Automated Redaction & EXIF Utilities**: Built-in tools for stripping sensitive metadata (`exif_utils.py`) and redacting confidential information from digital submissions (`redaction.py`).
* **Audio & Search Integration**: Dedicated audio processing routers (`audio.py`) and high-performance search endpoints (`search.py`) for rapid evidence retrieval.
* **Immutable Audit Logs**: Comprehensive system logging tracking every access, modification, and export action for strict legal compliance (`audit_logs.py`).
* **Automated Report Generation**: Dynamic compilation of structured case and evidence summaries into secure PDF formats (`pdf_report.py`).
* **Modern Web Interface**: Responsive HTML5/CSS3 frontend equipped with internationalization (`i18n.js`), dynamic theme toggling (`theme.js`), and modular API integration (`api.js`).

---

## 📂 Project Architecture

```text
NyayVault/
├── app/                          # FastAPI backend application
│   ├── routers/                  # API routing modules
│   │   ├── auth.py               # Authentication & token endpoints
│   │   ├── cases.py              # Case file management
│   │   ├── documents.py          # Document upload & handling
│   │   ├── redaction.py          # Sensitive data redaction
│   │   ├── search.py             # Advanced search services
│   │   ├── audio.py              # Audio recording & processing
│   │   ├── audit_logs.py         # Security & action audit trails
│   │   ├── reports.py            # Report generation triggers
│   │   └── users.py              # User management & roles
│   ├── utils/                    # Core utility modules
│   │   ├── contracts/            # Smart contracts (HashAnchor.sol)
│   │   ├── blockchain_anchor.py  # Blockchain integration logic
│   │   ├── exif_utils.py         # Metadata extraction & stripping
│   │   ├── hashing.py            # Cryptographic hashing utilities
│   │   └── pdf_report.py         # PDF report layout generator
│   ├── config.py                 # Application configuration & env settings
│   ├── database.py               # SQLAlchemy session & DB connection
│   ├── dependencies.py           # FastAPI dependency injections & guards
│   ├── models.py                 # SQLAlchemy ORM database models
│   ├── schemas.py                # Pydantic validation schemas
│   └── security.py               # JWT encoding & password hashing
├── frontend/                     # Static web client
│   ├── css/                      # Stylesheets (styles, login, dashboard)
│   ├── js/                       # Modular JavaScript (api, dashboard, i18n, theme)
│   ├── login.html                # Authentication view
│   └── dashboard.html            # Main administrative dashboard
├── storage/                      # Secure file storage directories
│   ├── evidence/                 # Uploaded raw evidence files
│   └── reports/                  # Generated PDF reports
├── .env.example                  # Environment variables template
├── requirements.txt              # Python project dependencies
└── seed_data.py                  # Database initialization & seeding script


🛠️ Tech Stack
Backend Framework: Python, FastAPI, Uvicorn
Database & ORM: SQLAlchemy, Pydantic
Frontend: HTML5, CSS3, Vanilla JavaScript (ES6 Modules)
Security & Cryptography: SHA-256 Hashing, JSON Web Tokens (JWT), Solidity (Smart Contracts)
File Processing: ReportLab / PDF utilities, EXIF toolkits
⚙️ Getting Started & Installation
Prerequisites
Python 3.10 or higher
Git
1. Clone & Navigate
Bash
git clone <repository-url>
cd SIHnyayvault/NyayVault
2. Set Up Virtual Environment
Bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
3. Install Dependencies
Bash
pip install -r requirements.txt
4. Configure Environment Variables
Copy the template file and configure your local environment settings:
Bash
cp .env.example .env
5. Seed Initial Data
Populate the database with default administrative accounts and mock case data:
Bash
python seed_data.py
6. Run the FastAPI Server
Bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
API Documentation (Swagger UI): http://127.0.0.1:8000/docs
🖥️ Accessing the Frontend
Open the frontend/login.html file directly in any modern browser, or host the frontend/ directory using a local static server (e.g., Live Server extension in VS Code).
Use your seeded credentials to log in and interact with the frontend/dashboard.html interface.
📜 License
Developed for the Smart India Hackathon. All rights reserved.
