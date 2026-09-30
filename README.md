# Page Metrics — Agency Workspace Application

Internal analytics and Instagram page metrics dashboard built for social media agencies.

---

## 🚀 Quick Start

### 1. Launch Server (Windows)
Double-click **`start_app.bat`** or run:
```powershell
.\start_app.bat
```
App will open automatically at **[http://localhost:8000](http://localhost:8000)**.

### 2. Sign In Credentials
- **Agency ID**: `agency_admin`
- **Password**: `SecureAgency123!`

---

## ⚡ Data Providers & Backup Configuration

### Primary Source: Instagram Graph API (Official)
The application primarily uses Meta's official Instagram Graph API (`Business Discovery API`).
Configure credentials in `.env`:
```env
META_ACCESS_TOKEN=your_access_token_here
IG_BUSINESS_ACCOUNT_ID=your_ig_business_account_id_here
```

### Secondary Source: SerpApi Backup Provider
A secondary backup provider (`SerpApiProvider`) can be enabled when the primary Meta Graph API is unavailable, rate-limited, or encounters permission restrictions.
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
