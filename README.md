# IMetric — Agency Website

An agency website with a public product overview and a secure workspace for tracking Instagram page performance.

---

## Quick Start

### Launch locally (Windows)
Double-click **`start_app.bat`** or run:
```powershell
.\start_app.bat
```
The public website opens at **[http://localhost:8000](http://localhost:8000)**. The authenticated workspace is available at **[http://localhost:8000/app](http://localhost:8000/app)**.

### Database migrations
The backend applies pending Alembic migrations under a database lock before accepting requests. Existing unversioned databases created by earlier app versions are adopted at the initial schema revision and upgraded without recreating their data. Incomplete or unknown schemas stop startup rather than being silently stamped.

To inspect or apply migrations manually from the workspace root:
```powershell
$env:PYTHONPATH="backend"; .venv\Scripts\alembic.exe -c backend\alembic.ini current
$env:PYTHONPATH="backend"; .venv\Scripts\alembic.exe -c backend\alembic.ini upgrade head
```

### Local seed account
- **Agency ID**: `agency_admin`
- **Password**: `SecureAgency123!`

These credentials are development-only. Production startup rejects these defaults.

### Production deployment requirements
Set these values in the deployment secret store or an untracked `.env` file before starting Compose:
```env
ENV=production
POSTGRES_USER=pagemetrics
POSTGRES_PASSWORD=<unique database password>
POSTGRES_DB=pagemetrics
DATABASE_URL=postgresql+asyncpg://pagemetrics:<URL-encoded-password>@db:5432/pagemetrics
INITIAL_USER=<owner Agency ID>
INITIAL_PASSWORD=<unique password of at least 12 characters>
META_ACCESS_TOKEN=<Meta access token>
IG_BUSINESS_ACCOUNT_ID=<connected Instagram business account ID>
CORS_ORIGINS=["https://your-public-domain.example"]
```

Production requires PostgreSQL, HTTPS CORS origins, a non-default owner credential, and configured Meta API credentials. Compose binds the database, API, and web container ports to localhost; put a TLS reverse proxy in front of the web container and configure forwarded headers at that proxy. Keep `.env` out of source control and rotate secrets through your deployment platform.

Refresh jobs and status are stored in PostgreSQL, can be reclaimed after a worker restart, and are limited to one active job per agency. Provider calls are quota-reserved before fallback requests. Old completed refresh jobs are retained for 30 days; page snapshots are retained for up to 365 days and 100 snapshots per page.

---

## ⚡ Data Providers & Backup Configuration

### Primary source: Instagram Graph API (official)
The application primarily uses Meta's official Instagram Graph API (`Business Discovery API`).
Configure credentials in `.env`:
```env
META_ACCESS_TOKEN=your_access_token_here
IG_BUSINESS_ACCOUNT_ID=your_ig_business_account_id_here
```

### Optional secondary source: SerpApi
A secondary backup provider (`SerpApiProvider`) can be enabled for transient or rate-limit failures from the primary Meta Graph API. Authentication, permission, and account errors are returned directly so configuration problems are not hidden.
> **⚠️ Compliance Note**:
> By default, `BACKUP_ENABLED=false`. The backup provider collects publicly visible Instagram data through a third party (SerpApi). This is outside Meta's official Graph API. Enabling this secondary provider is the decision of the system operator.

To enable the backup provider in `.env`:
```env
BACKUP_ENABLED=true
SERPAPI_API_KEY=your_serpapi_key_here
BACKUP_DAILY_LIMIT=200
BACKUP_PER_AGENCY_DAILY_LIMIT=50
```

#### Cost & Abuse Controls:
- **Global Daily Limit**: 200 calls/day (configurable).
- **Agency Daily Limit**: 50 calls/day per agency account.
- **Combined Concurrency Cap**: Concurrency semaphore (3) applies across both providers.
- **Data Quality Guard**: Reject backup results if follower counts jump by >50% or reels drop to zero unexpectedly.
- **API Key Redaction**: All SerpApi keys are masked (`[REDACTED_API_KEY]`) in logs, stack traces, and API responses.

---

## 🛠️ CLI Admin Commands

```powershell
# Test Instagram Graph API & Error Classification
python -m app.cli check-instagram <username>

# Test ProviderChain Fallback & Provider Usage
python -m app.cli check-providers <username>

# Create Agency Account
python -m app.cli create-user <agency_id>

# Reset Agency Password
python -m app.cli reset-password <agency_id>
```

---

## 🧪 Testing

```powershell
# Run backend pytest suite
$env:PYTHONPATH="backend"; .venv\Scripts\pytest.exe backend/tests

# Run frontend build
npm --prefix frontend run build
```
