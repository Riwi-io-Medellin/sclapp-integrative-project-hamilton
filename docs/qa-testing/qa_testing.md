# QA Testing – Scraping, AI Classification, and System Validation

## Objective

Validate the correct behavior of the system across its main functional areas:

- Job scraping from external sources
- Keyword filtering
- Riwi relevance filtering
- AI-based job classification
- Technology extraction
- Database persistence
- API responses
- Frontend visualization

The goal is to ensure that the system reliably collects, processes, stores, and presents relevant job data for identifying companies that may need technology talent.

---

# Scope

This testing covers the following system components:

### Scraping Layer
- Remotive scraper
- RemoteOK scraper

### Data Processing
- Keyword filtering
- Riwi relevance filter (`job_filters.py`)
- AI classification (`job_classifier.py`)
- Technology extraction

### Database Persistence
- `company`
- `technologies`
- `company_technologies`
- `scraping_logs`

### API Endpoints
- `/api/scraping/start`
- `/api/dashboard/stats`
- `/api/companies/enriched`
- `/api/companies/top`
- `/api/companies/technologies/trending`

### Frontend Views
- Dashboard
- Companies page
- Scraping modal

---

# Preconditions

Before executing the tests:

1. Backend running at  
   `http://localhost:8000`

2. Frontend accessible in the browser.

3. PostgreSQL database available.

4. Environment variables configured:

```
OPENAI_API_KEY
OPENAI_MODEL
```

5. Required database tables exist:

```
company
technologies
company_technologies
scraping_logs
```

---

# Test Cases

---

# 1. Scraping and AI Processing

---

## TC-01 – Basic scraping from Remotive

### Objective
Verify that scraping from a real job source works correctly.

### Endpoint

```
POST /api/scraping/start
```

### Request

```json
{
  "parameters": {
    "source": "remotive",
    "max_items": 5
  }
}
```

### Expected Result

- HTTP response `200`
- `execution_status = SUCCESS`
- `total_found > 0`

Database behavior:

- At least one company inserted or updated
- A new record appears in `scraping_logs`

### SQL Validation

```sql
SELECT *
FROM scraping_logs
ORDER BY executed_at DESC
LIMIT 1;
```

---

## TC-02 – Keyword filter: python

### Objective
Verify that the backend filters jobs using the keyword `python`.

### Request

```json
{
  "parameters": {
    "source": "remotive",
    "query": "python",
    "max_items": 10,
    "only_riwi_relevant": true,
    "require_junior_focus": false
  }
}
```

### Expected Result

- HTTP response `200`
- Jobs are related to Python roles
- Stored companies show Python-related technologies

### SQL Validation

```sql
SELECT name, category, score
FROM company
ORDER BY id_company DESC
LIMIT 10;
```

```sql
SELECT id_tech, name_tech
FROM technologies
ORDER BY id_tech DESC
LIMIT 20;
```

---

## TC-03 – Keyword filter: react

### Objective
Verify that a frontend keyword produces frontend-related jobs.

### Request

```json
{
  "parameters": {
    "source": "remotive",
    "query": "react",
    "max_items": 10,
    "only_riwi_relevant": true,
    "require_junior_focus": false
  }
}
```

### Expected Result

Results should contain frontend roles.

Possible technologies:

- react
- javascript
- typescript

---

## TC-04 – Keyword filter: data

### Objective
Validate detection of data-related roles.

### Request

```json
{
  "parameters": {
    "source": "remotive",
    "query": "data",
    "max_items": 10,
    "only_riwi_relevant": true,
    "require_junior_focus": false
  }
}
```

### Expected Result

Detected profiles may include:

- Data Analyst
- Data Engineer
- Data Scientist

Possible technologies:

- pandas
- sql
- airflow
- dbt
- spark
- power bi

---

## TC-05 – Keyword filter: devops

### Objective
Verify detection of DevOps and infrastructure roles.

### Request

```json
{
  "parameters": {
    "source": "remotive",
    "query": "devops",
    "max_items": 10,
    "only_riwi_relevant": true,
    "require_junior_focus": false
  }
}
```

### Expected Result

Possible roles:

- DevOps Engineer

Possible technologies:

- docker
- kubernetes
- aws
- linux

---

## TC-06 – AI scoring validation

### Objective

Verify that the AI assigns a valid score and category.

### Expected Result

Stored companies should have:

- `score` between **1 and 3**
- `category` not empty

### SQL Validation

```sql
SELECT name, category, score
FROM company
WHERE score IS NOT NULL
ORDER BY score DESC
LIMIT 20;
```

---

## TC-07 – Technology extraction validation

### Objective

Verify that technologies are correctly extracted and stored.

### Expected Result

- `technologies` table contains real technical tools
- `company_technologies` links companies with technologies

Examples that should **NOT** appear as technologies:

- insurance
- onboarding
- project management
- trading

### SQL Validation

```sql
SELECT *
FROM technologies
ORDER BY id_tech DESC;
```

```sql
SELECT ct.id_company, c.name, t.name_tech
FROM company_technologies ct
JOIN company c ON c.id_company = ct.id_company
JOIN technologies t ON t.id_tech = ct.id_tech
LIMIT 50;
```

---

## TC-08 – Duplicate prevention

### Objective

Verify that the system does not create duplicate companies.

### Steps

1. Run a scraping request with query `python`
2. Run the same request again

### Expected Result

- Second execution produces fewer new companies
- `total_updated` may increase
- No duplicated companies appear in the database

---

# 2. Data Quality and Database Integrity

---

## TC-09 – Technology duplication validation

### Objective

Ensure technologies are not duplicated due to case differences.

### SQL Validation

```sql
SELECT LOWER(name_tech), COUNT(*)
FROM technologies
GROUP BY LOWER(name_tech)
HAVING COUNT(*) > 1;
```

### Expected Result

No duplicated technologies should exist ignoring case.

---

## TC-10 – Relationship integrity

### Objective

Verify that all records in `company_technologies` reference valid companies and technologies.

### SQL Validation

```sql
SELECT *
FROM company_technologies ct
LEFT JOIN company c ON c.id_company = ct.id_company
LEFT JOIN technologies t ON t.id_tech = ct.id_tech
WHERE c.id_company IS NULL OR t.id_tech IS NULL;
```

### Expected Result

No orphan relationship records should exist.

---

# 3. API and Frontend Integration

---

## TC-11 – Dashboard validation

### Objective

Verify that the dashboard displays real data.

### Visual Validation

Dashboard must show:

- Companies with vacancies
- Emails sent
- AI scored companies
- High score companies

Lists must show:

- Top companies by score
- Trending technologies

### Endpoints Used

```
GET /api/dashboard/stats
GET /api/companies/top
GET /api/companies/technologies/trending
```

---

## TC-12 – Companies table validation

### Objective

Verify that the Companies page loads real database data.

### Visual Validation

The table should display:

- Company name
- Technologies
- Category
- Country
- AI score

### Endpoint

```
GET /api/companies/enriched
```

Example request:

```
/api/companies/enriched?search=react&tech=python&score=3
```

---

## TC-13 – Combined frontend filters

### Objective

Verify that search and filters work together correctly.

### Steps

1. Open **Companies**
2. Search by name
3. Filter by technology
4. Filter by score

### Expected Result

The table updates correctly according to all active filters.

---

## TC-14 – Scraping execution from UI

### Objective

Verify that scraping can be triggered from the frontend.

### Steps

1. Open the application
2. Navigate to **Companies**
3. Click **Run scraping**
4. Select a source
5. Enter keyword `python`
6. Start search

### Expected Result

User sees a result message:

```
Scraping completed
Found: X · New: X · Updated: X · Failed: X
```

### Database Validation

```sql
SELECT *
FROM scraping_logs
ORDER BY executed_at DESC
LIMIT 1;
```

---

# 4. Error Handling and Edge Cases

---

## TC-15 – Invalid scraping source

### Objective

Verify that the API rejects unsupported sources.

### Request

```json
{
  "parameters": {
    "source": "linkedin",
    "max_items": 5
  }
}
```

### Expected Result

- Request rejected
- Clear error message returned
- Backend remains stable

---

## TC-16 – Scraping with no matching results

### Objective

Verify system behavior when a query produces no results.

### Request

```json
{
  "parameters": {
    "source": "remotive",
    "query": "veryrarekeyword123",
    "max_items": 10
  }
}
```

### Expected Result

- Request succeeds
- `total_found = 0` or very low
- Scraping log still records execution

---

## TC-17 – AI service unavailable

### Objective

Verify system behavior when OpenAI is unavailable.

### Preconditions

Remove or invalidate:

```
OPENAI_API_KEY
```

### Expected Result

- Scraping process does not crash
- Controlled error handling
- Logs indicate AI classification failure

---

# 5. Authentication and Security

---

## TC-18 – Successful login

### Objective

Verify that a registered user can log in successfully.

### Expected Result

- Authentication successful
- User redirected to dashboard
- Session or cookie created correctly

---

## TC-19 – Invalid login credentials

### Objective

Verify rejection of incorrect login credentials.

### Expected Result

- Login fails
- Clear error message shown
- No session created

---

## TC-20 – Unauthorized access protection

### Objective

Verify that protected endpoints require authentication.

### Example Endpoints

```
GET /api/dashboard/stats
GET /api/companies/enriched
```

### Expected Result

- Unauthorized request rejected
- System does not expose protected data

---

# 6. Performance Observation

---

## TC-21 – Basic scraping performance

### Objective

Ensure scraping completes within acceptable time for demo conditions.

### Scenario

- Source: remotive
- max_items: 5

### Expected Result

- Request completes successfully
- No timeout occurs
- Execution time remains reasonable for MVP usage

---

# Conclusion

This testing plan validates the core functionality of the SCLAPP MVP:

- Job scraping from real sources
- AI-based job classification
- Technology extraction
- Database persistence
- Dashboard insights
- Frontend interaction
- Error handling and system stability

The test cases ensure the system behaves reliably under both normal and edge conditions.