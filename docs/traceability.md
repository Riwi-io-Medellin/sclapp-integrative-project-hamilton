# Traceability Matrix

## SCLAPP System

The traceability matrix connects functional requirements with the system components that implement them.

---

| Requirement | Frontend | API | Backend Module | Service | Model | DB Table |
|--------------|----------|-----|---------------|--------|--------|---------|
| RF01 User Registration | register.js | api/v1/auth.py | modules/auth | auth_service.py | user.py | users |
| RF02 User Login | login.js | api/v1/auth.py | modules/auth | auth_service.py | user.py | users |
| RF03 Session Management | login.js | api/v1/auth.py | modules/auth | auth_service.py | user.py | refresh_tokens |
| RF04 Role Management | perfil.js | api/v1/profile.py | modules/auth | auth_service.py | user.py | role |
| RF05 Company Management | empresas.js | api/v1/companies.py | modules/companies | company_service.py | company.py | company |
| RF06 Company Update | empresas.js | api/v1/companies.py | modules/companies | company_service.py | company.py | company |
| RF07 Status Management | empresas.js | api/v1/companies.py | modules/companies | company_service.py | company.py | statuses |
| RF08 Technology Association | empresas.js | api/v1/companies.py | modules/companies | company_service.py | company.py | company_technologies |
| RF09 Scraping Execution | dashboard.js | api/v1/scraping.py | modules/scraping | scrape_service.py | - | scraping_logs |
| RF10 Scraping Logging | dashboard.js | api/v1/scraping.py | modules/scraping | scrape_service.py | - | scraping_logs |
| RF11 Email Sending | correos.js | api/v1/emails.py | modules/email | email_service.py | - | emails |
| RF12 Email History | correos.js | api/v1/emails.py | modules/email | email_service.py | - | emails |
| RF13 Email Events | correos.js | api/v1/emails.py | modules/email | email_service.py | - | email_events |
| RF14 Dashboard | dashboard.js | api/v1/dashboard.py | modules/dashboard | dashboard_service.py | - | company |
| RF15 User Profile | perfil.js | api/v1/profile.py | modules/auth | auth_service.py | user.py | users |

---

# External Services

## System integrations

| Function | Service |
|----------|--------|
| Scraping | RemoteOK, Remotive, GetOnBoard |
| Email | Brevo API |

---

# System Components

## Frontend

Location:

frontend/assets/js

## Backend API

Location:

backend/api/v1

## Backend Modules

Location:

backend/modules

## Services

Location:

backend/services

## Models

Location:

backend/db/models

## Database

Engine:

PostgreSQL

Main tables:

- users
- role
- statuses
- company
- technologies
- company_technologies
- refresh_tokens
- scraping_logs
- emails
- email_events
