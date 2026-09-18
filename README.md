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