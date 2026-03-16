# Software Requirements Specification (SRS)

## System: SCLAPP

---

# 1. Introduction

## 1.1 Purpose

This document describes the **functional and non-functional requirements** of the **SCLAPP system**.
Its purpose is to provide a clear specification for developers, testers, and stakeholders during the development, deployment, and maintenance of the software.

## 1.2 Scope

SCLAPP is a backend system designed to manage data through a **RESTful API built with Node.js, Express, and PostgreSQL**.

The system provides functionality to:

* Manage data stored in a database
* Process client requests
* Provide REST API endpoints
* Apply business logic
* Validate user input
* Handle server responses and errors

## 1.3 Definitions, Acronyms, and Abbreviations

| Term | Definition                          |
| ---- | ----------------------------------- |
| API  | Application Programming Interface   |
| DB   | Database                            |
| SRS  | Software Requirements Specification |
| CRUD | Create, Read, Update, Delete        |
| REST | Representational State Transfer     |

## 1.4 References

* Project technical documentation
* Repository README file
* SQL database schema
* System setup and execution guide

---

# 2. Overall Description

## 2.1 Product Perspective

SCLAPP operates as an **independent backend service** that exposes endpoints to be consumed by client applications such as web or mobile interfaces.

### System Architecture

```
Client
   │
   ▼
Express API
   │
   ▼
Services / Controllers
   │
   ▼
PostgreSQL Database
```

## 2.2 Product Functions

The system provides the following main functionalities:

* Create database records
* Retrieve stored information
* Update existing records
* Delete records
* Process HTTP requests
* Validate input data
* Handle system errors

## 2.3 User Classes

| User Type     | Description                                 |
| ------------- | ------------------------------------------- |
| Administrator | Manages and controls system records         |
| API Consumer  | External client that interacts with the API |

## 2.4 Operating Environment

The system operates in the following environment:

* **Node.js runtime**
* **Express.js framework**
* **PostgreSQL database**
* **Operating Systems:** Linux, Windows, macOS
* **Development tools:** npm, Git

## 2.5 Design Constraints

The system must follow these constraints:

* Implementation using **Node.js and Express**
* Data persistence using **PostgreSQL**
* Architecture based on **REST API**
* Modular code structure

## 2.6 Assumptions and Dependencies

The system assumes:

* Database server is properly configured
* Environment variables are correctly defined
* Network access to the backend server
* A client application consuming the API

---

# 3. Functional Requirements

## FR1 – Create Records

The system shall allow the creation of new records in the database.

**Input**

* Data submitted through the API.

**Output**

* Confirmation message indicating successful creation.

---

## FR2 – Retrieve Records

The system shall allow users to retrieve existing records.

Available operations:

* Retrieve all records
* Retrieve a record by ID

---

## FR3 – Update Records

The system shall allow modification of existing records.

**Input**

* Record identifier
* Updated data fields

---

## FR4 – Delete Records

The system shall allow deletion of records from the database.

**Input**

* Record ID

---

## FR5 – REST Endpoints

The system shall expose HTTP endpoints for interaction.

### Example Endpoints

```
GET /api/resources
POST /api/resources
PUT /api/resources/:id
DELETE /api/resources/:id
```

---

## FR6 – Input Validation

The system shall validate client input before processing requests.

Examples of validations include:

* Required fields
* Correct data types
* Valid formats

---

## FR7 – Error Handling

The system shall properly handle server errors and return appropriate HTTP responses.

Example responses:

```
400 - Bad Request
404 - Not Found
500 - Internal Server Error
```

---

# 4. Non-Functional Requirements

## 4.1 Performance

The system should respond to API requests within **2 seconds under normal conditions**.

## 4.2 Security

The system shall:

* Validate all user inputs
* Prevent SQL injection
* Implement authentication if required

## 4.3 Scalability

The architecture must allow:

* Horizontal scaling
* Future service separation (microservices if needed)

## 4.4 Availability

The system should remain available **24/7** with proper error handling mechanisms.

## 4.5 Maintainability

The codebase must:

* Follow a modular architecture
* Be well documented
* Use consistent coding standards

---

# 5. Data Model (Summary)

Example table structure:

```
Table: resources

id
name
description
created_at
updated_at
```

Relationships between tables maintain **data integrity and structure**.

---

# 6. System Interfaces

## 6.1 API Interface

Communication with the system occurs via **HTTP REST API**.

### Data Format

```
JSON
```

### Example Response

```json
{
  "id": 1,
  "name": "Example",
  "status": "active"
}
```

---

# 7. Future Enhancements

Potential improvements for the system include:

* Implementing **JWT authentication**
* Creating an **administration dashboard**
* Integration with a **web frontend**
* Adding **logging and monitoring**
* Automatic API documentation using **Swagger**
