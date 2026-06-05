# SENTINEL — Commit Governance Platform

## Architecture Document v1.0

> **Codename:** SENTINEL  
> **Purpose:** Enterprise-grade commit governance, merge coverage analysis, content verification, and executive reporting for multi-folder GitHub repositories.  
> **Philosophy:** Deterministic. Auditable. Traceable. Zero AI/LLM dependency.  
> **Cost:** $0 — Every tool, library, and service in this stack is free and open-source.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Principles](#2-architecture-principles)
3. [Technology Stack](#3-technology-stack)
4. [High-Level Architecture](#4-high-level-architecture)
5. [Module Architecture](#5-module-architecture)
6. [Database Architecture](#6-database-architecture)
7. [API Architecture](#7-api-architecture)
8. [Frontend Architecture](#8-frontend-architecture)
9. [Data Flow Pipeline](#9-data-flow-pipeline)
10. [Security & Access Control](#10-security--access-control)
11. [Background Processing](#11-background-processing)
12. [Caching Strategy](#12-caching-strategy)
13. [Export & Reporting Pipeline](#13-export--reporting-pipeline)
14. [Testing Strategy](#14-testing-strategy)
15. [Deployment Architecture](#15-deployment-architecture)
16. [CI/CD Pipeline](#16-cicd-pipeline)
17. [Monitoring & Observability](#17-monitoring--observability)
18. [Project Structure](#18-project-structure)
19. [Development Workflow](#19-development-workflow)
20. [Performance Targets](#20-performance-targets)
21. [Appendix: Decision Log](#21-appendix-decision-log)

---

## 1. System Overview

### 1.1 What SENTINEL Does

SENTINEL is a self-hosted platform that connects to GitHub repositories, ingests commit history, and produces deterministic governance analytics across multiple customer configuration folders.

It answers five core questions:

| # | Question | Module |
|---|----------|--------|
| 1 | Which Jira tickets were committed, and where? | Commit Collector + Jira Aggregation |
| 2 | Are files actually identical across folders? | Content Verification Engine |
| 3 | How long are merges being delayed? | Merge Delay Analytics |
| 4 | Which folders are falling behind? | Folder Health Engine |
| 5 | What needs immediate attention? | Exception Detection + Dashboard |

### 1.2 System Boundaries

```
┌─────────────────────────────────────────────────────────────────┐
│                        SENTINEL PLATFORM                        │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │  GitHub   │  │  FastAPI  │  │  Celery   │  │   Next.js    │   │
│  │ Ingestion │──│  Backend  │──│  Workers  │  │  Dashboard   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │
│       │              │              │               │            │
│       └──────────────┴──────────────┘               │            │
│                      │                              │            │
│              ┌───────┴───────┐              ┌───────┴───────┐   │
│              │  PostgreSQL   │              │     Redis      │   │
│              │   Database    │              │   Cache/Queue  │   │
│              └───────────────┘              └───────────────┘   │
└─────────────────────────────────────────────────────────────────┘
         │                                           │
         ▼                                           ▼
   ┌──────────┐                               ┌──────────┐
   │  GitHub   │                               │  Browser  │
   │   API     │                               │  Client   │
   └──────────┘                               └──────────┘
```

### 1.3 Key Actors

| Actor | Role |
|-------|------|
| **Developer** | Commits code, triggers ingestion |
| **Team Lead** | Reviews coverage, folder health |
| **Manager** | Uses dashboard, exports reports |
| **Admin** | Configures repos, folders, rules |
| **System** | Scheduled ingestion, background analysis |

---

## 2. Architecture Principles

### 2.1 Core Principles

| Principle | Implementation |
|-----------|---------------|
| **Deterministic** | Every result is produced by reproducible logic. Same input → same output. Always. |
| **Auditable** | Every computation logs its inputs, rule applied, and output. Full trace chain. |
| **Modular** | Each of the 10 modules is an independent service layer with clean interfaces. |
| **Offline-First** | All data is stored locally. No external API calls during analysis (only during ingestion). |
| **Zero AI** | No LLMs, no ML models, no probabilistic inference. Rule-based only. |
| **Free Forever** | Every dependency is MIT/Apache/BSD licensed. No vendor lock-in. No paid tiers. |

### 2.2 Design Patterns

| Pattern | Where Used | Why |
|---------|-----------|-----|
| **Repository Pattern** | Database access | Decouples business logic from ORM/SQL |
| **Service Layer** | Each module | Encapsulates business rules, testable in isolation |
| **Event-Driven** | Ingestion pipeline | Celery tasks trigger downstream analysis after data loads |
| **CQRS (lite)** | Dashboard queries vs. write operations | Separate read-optimized views from write models |
| **Strategy Pattern** | Exception rules engine | Pluggable rule definitions without modifying core |
| **Builder Pattern** | Report generation | Composable Excel/PDF report construction |

### 2.3 Error Handling Philosophy

```
Every function returns typed results, never raw exceptions to the caller.

Pattern:
  ServiceResult[T] = { success: bool, data: T | None, error: str | None, metadata: dict }

Errors are:
  - Logged with full context (structured JSON logging)
  - Categorized (RETRIABLE, FATAL, VALIDATION, EXTERNAL)
  - Propagated through the service layer with context preservation
  - Never silently swallowed
```

---

## 3. Technology Stack

### 3.1 Backend

| Component | Technology | Version | License | Purpose |
|-----------|-----------|---------|---------|---------|
| **Language** | Python | 3.12+ | PSF | Core backend language |
| **Framework** | FastAPI | 0.115+ | MIT | REST API framework |
| **ORM** | SQLAlchemy | 2.0+ | MIT | Database ORM with async support |
| **Migrations** | Alembic | 1.13+ | MIT | Schema migrations |
| **Validation** | Pydantic | 2.0+ | MIT | Request/response validation |
| **Task Queue** | Celery | 5.4+ | BSD | Background job processing |
| **Message Broker** | Redis | 7.0+ | BSD-3 | Celery broker + caching |
| **GitHub Client** | PyGithub + `git` CLI | Latest | LGPL/GPL | API + raw git operations |
| **Excel Export** | openpyxl | 3.1+ | MIT | .xlsx generation with charts |
| **PDF Export** | WeasyPrint | 62+ | BSD | HTML-to-PDF rendering |
| **Charts** | matplotlib | 3.9+ | PSF | Chart generation for reports |
| **Hashing** | hashlib (stdlib) | — | PSF | SHA256 content verification |
| **Scheduling** | Celery Beat | — | BSD | Periodic task scheduling |
| **Logging** | structlog | 24.0+ | MIT | Structured JSON logging |

### 3.2 Frontend

| Component | Technology | Version | License | Purpose |
|-----------|-----------|---------|---------|---------|
| **Framework** | Next.js | 15+ | MIT | React SSR/SSG framework |
| **Language** | TypeScript | 5.5+ | Apache-2.0 | Type-safe frontend |
| **Styling** | Tailwind CSS | 4.0+ | MIT | Utility-first CSS |
| **Charts** | Recharts | 2.13+ | MIT | Dashboard visualizations |
| **Tables** | TanStack Table | 8.0+ | MIT | Data grid with sorting/filtering |
| **State** | Zustand | 5.0+ | MIT | Lightweight state management |
| **HTTP** | Axios | 1.7+ | MIT | API client |
| **Icons** | Lucide React | Latest | ISC | Icon library |
| **Dates** | date-fns | 4.0+ | MIT | Date manipulation |
| **Forms** | React Hook Form | 7.0+ | MIT | Form handling |
| **Toast** | Sonner | 1.7+ | MIT | Notification toasts |

### 3.3 Database

| Component | Technology | Version | License | Purpose |
|-----------|-----------|---------|---------|---------|
| **Primary DB** | PostgreSQL | 16+ | PostgreSQL | Main data store |
| **Cache** | Redis | 7.0+ | BSD-3 | Query cache + task broker |

### 3.4 Infrastructure

| Component | Technology | Version | License | Purpose |
|-----------|-----------|---------|---------|---------|
| **Containerization** | Docker | Latest | Apache-2.0 | Service isolation |
| **Orchestration** | Docker Compose | Latest | Apache-2.0 | Multi-container management |
| **Reverse Proxy** | Nginx | Latest | BSD-2 | SSL termination, static serving |
| **CI/CD** | GitHub Actions | — | Free tier | Automated testing & deployment |
| **Monitoring** | Prometheus + Grafana | Latest | Apache-2.0 | Metrics & dashboards |
| **Log Aggregation** | Loki | Latest | AGPL-3.0 | Centralized logging |

### 3.5 Why These Choices

| Decision | Rationale |
|----------|-----------|
| **FastAPI over Django** | Native async, automatic OpenAPI docs, Pydantic integration, lighter footprint |
| **SQLAlchemy 2.0 over Django ORM** | Explicit query construction, async support, better for complex aggregations |
| **Celery over background threads** | Battle-tested, retries, rate limiting, monitoring (Flower), horizontal scaling |
| **PostgreSQL over SQLite** | Concurrent writes, JSONB support, window functions, materialized views |
| **Redis over RabbitMQ** | Simpler ops, dual-purpose (cache + broker), lower memory footprint |
| **Next.js over plain React** | SSR for SEO, API routes, file-based routing, built-in optimization |
| **Recharts over D3** | React-native, declarative, sufficient for dashboard charts, faster dev time |
| **WeasyPrint over ReportLab** | HTML/CSS-based templates, easier to maintain, better typography |
| **openpyxl over xlsxwriter** | Read+write support, chart API, conditional formatting |

---

## 4. High-Level Architecture

### 4.1 Layered Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                       │
│                                                               │
│   Next.js Dashboard    │    REST API (FastAPI)    │   Exports  │
│   (Browser Client)     │    (JSON Responses)      │  (XLS/PDF) │
└────────────┬───────────┴────────────┬─────────────┴───────────┘
             │                        │
┌────────────▼────────────────────────▼─────────────────────────┐
│                       API GATEWAY LAYER                        │
│                                                               │
│   Authentication  │  Rate Limiting  │  Request Validation     │
│   (JWT + RBAC)    │  (SlowAPI)      │  (Pydantic Models)      │
└────────────┬──────┴────────┬────────┴────────┬────────────────┘
             │               │                 │
┌────────────▼───────────────▼─────────────────▼────────────────┐
│                       SERVICE LAYER                            │
│                                                               │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────────┐    │
│  │   Commit     │ │    Jira      │ │   Folder Coverage   │    │
│  │  Collector   │ │  Aggregation │ │      Engine         │    │
│  │  Service     │ │   Service    │ │     Service         │    │
│  └─────────────┘ └──────────────┘ └─────────────────────┘    │
│                                                               │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────────┐    │
│  │  Content     │ │  Merge Delay │ │   Folder Health     │    │
│  │ Verification │ │  Analytics   │ │     Engine          │    │
│  │  Service     │ │   Service    │ │     Service         │    │
│  └─────────────┘ └──────────────┘ └─────────────────────┘    │
│                                                               │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────────┐    │
│  │  Exception   │ │  Historical  │ │    Reporting        │    │
│  │  Detection   │ │   Trends     │ │     Engine          │    │
│  │   Engine     │ │   Service    │ │    Service          │    │
│  └─────────────┘ └──────────────┘ └─────────────────────┘    │
└────────────┬──────────────┬──────────────┬────────────────────┘
             │              │              │
┌────────────▼──────────────▼──────────────▼────────────────────┐
│                     REPOSITORY LAYER                           │
│                                                               │
│   CommitRepo  │  JiraRepo  │  FolderRepo  │  SnapshotRepo    │
│   FileRepo    │  RuleRepo  │  AuditRepo   │  ReportRepo      │
└────────────┬──────────────┬──────────────┬────────────────────┘
             │              │              │
┌────────────▼──────────────▼──────────────▼────────────────────┐
│                      DATA LAYER                                │
│                                                               │
│          PostgreSQL              │           Redis             │
│   (Persistent Storage)          │    (Cache + Task Broker)    │
└─────────────────────────────────┴─────────────────────────────┘
```

### 4.2 Module Dependency Graph

```
                    ┌──────────────────┐
                    │  M1: Commit      │
                    │  Collector       │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  M2: Jira        │
                    │  Aggregation     │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼────┐ ┌──────▼──────┐ ┌─────▼───────┐
     │ M3: Folder  │ │ M4: Content │ │ M5: Merge   │
     │ Coverage    │ │ Verification│ │ Delay       │
     └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
            │               │               │
            └───────────────┼───────────────┘
                            │
                   ┌────────▼─────────┐
                   │  M6: Folder      │
                   │  Health          │
                   └────────┬─────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
     ┌────────▼────┐ ┌─────▼──────┐ ┌────▼──────────┐
     │ M7: Exception│ │ M8: Trends │ │ M9: Dashboard │
     │ Detection   │ │ Analytics  │ │ (Frontend)    │
     └──────┬──────┘ └──────┬─────┘ └───────────────┘
            │               │
            └───────┬───────┘
                    │
           ┌────────▼─────────┐
           │  M10: Reporting  │
           │  (Excel + PDF)   │
           └──────────────────┘
```

---

## 5. Module Architecture

### 5.1 Module 1 — GitHub Commit Collector

**Responsibility:** Ingest commit data from GitHub repositories into the local database.

**Strategy: Dual-Mode Ingestion**

| Mode | Method | Use Case |
|------|--------|----------|
| **API Mode** | PyGithub (GitHub REST API v3) | Initial sync, remote repos, rate-limit aware |
| **Git Mode** | `git log --format` via subprocess | Local clones, faster for large histories, no rate limits |

**Ingestion Pipeline:**

```
GitHub API / git log
        │
        ▼
┌──────────────────┐
│  Raw Commit      │
│  Parser          │ ──→ Normalize author, dates, message
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Jira Extractor  │ ──→ Regex: r'[A-Z]{2,10}-\d{3,6}'
│                  │     Configurable per repository
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  File Differ     │ ──→ Parse changed files, detect folder
│                  │     Map file → folder using path prefix
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Deduplication   │ ──→ SHA-based dedup, skip existing
│                  │     Upsert on conflict
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Database Write  │ ──→ Batch insert (500 per batch)
│                  │     Transaction-safe
└──────────────────┘
```

**Configuration:**

```python
# config/repositories.yaml
repositories:
  - name: "main-config-repo"
    url: "https://github.com/org/repo"
    branches:
      - "main"
      - "develop"
    folders:
      - "vanilla"
      - "MET"
      - "AMO"
      - "IOM"
      - "JCF"
      - "MOD"
      - "WMP"
      - "YATH"
    jira_patterns:
      - '[A-Z]{2,10}-\d{3,6}'
    sync_mode: "api"          # "api" | "git" | "hybrid"
    sync_interval_minutes: 30
```

**Rate Limiting Strategy (GitHub API):**

```
- Check X-RateLimit-Remaining header before each batch
- If remaining < 100, pause until X-RateLimit-Reset
- Use conditional requests (If-None-Match) to save quota
- Log every API call with timestamp and remaining quota
- Fallback to git clone mode if rate limit is exhausted
```

**Key Service Interface:**

```python
class CommitCollectorService:
    async def sync_repository(self, repo_id: str, date_range: DateRange) -> SyncResult
    async def sync_incremental(self, repo_id: str) -> SyncResult
    async def get_sync_status(self, repo_id: str) -> SyncStatus
    async def extract_jira_ids(self, message: str, patterns: list[str]) -> list[str]
    async def map_files_to_folders(self, files: list[str], folder_config: list[str]) -> dict
```

---

### 5.2 Module 2 — Jira Aggregation Engine

**Responsibility:** Group commits by Jira ticket and compute timeline metadata.

**Aggregation Logic:**

```sql
-- Core aggregation query (conceptual)
SELECT
    jira_id,
    COUNT(DISTINCT commit_sha) AS commit_count,
    COUNT(DISTINCT author)     AS author_count,
    MIN(commit_date)           AS first_seen,
    MAX(commit_date)           AS last_updated,
    ARRAY_AGG(DISTINCT folder) AS touched_folders,
    MAX(commit_date) - MIN(commit_date) AS active_duration
FROM commit_jira_mapping
JOIN commit_files ON ...
GROUP BY jira_id;
```

**Jira Status Classification:**

| Status | Condition |
|--------|-----------|
| `ACTIVE` | Last update within 7 days |
| `STALE` | Last update 8–30 days ago |
| `DORMANT` | Last update 31–90 days ago |
| `ARCHIVED` | Last update > 90 days ago |

**Key Service Interface:**

```python
class JiraAggregationService:
    async def aggregate_all(self) -> list[JiraSummary]
    async def get_jira_detail(self, jira_id: str) -> JiraDetail
    async def get_jira_timeline(self, jira_id: str) -> JiraTimeline
    async def search_jiras(self, query: str, filters: JiraFilters) -> PaginatedResult
    async def get_jira_coverage_matrix(self, jira_ids: list[str]) -> CoverageMatrix
```

---

### 5.3 Module 3 — Folder Coverage Engine

**Responsibility:** For each Jira, determine expected vs. actual folder coverage.

**Coverage Algorithm:**

```
Input:
  - jira_id: str
  - expected_folders: list[str]   # from repository config
  - actual_folders: list[str]     # from commit_files data

Algorithm:
  merged  = expected ∩ actual
  missing = expected - actual

  coverage_pct = |merged| / |expected| × 100

  status =
    MERGED   if coverage_pct == 100
    PARTIAL  if 0 < coverage_pct < 100
    MISSING  if coverage_pct == 0

Output:
  CoverageResult {
    jira_id, coverage_pct, status,
    merged_folders, missing_folders,
    expected_count, actual_count
  }
```

**Coverage Matrix (per Jira × Folder):**

```
             vanilla  MET  AMO  IOM  JCF  MOD  WMP  YATH
NC-4928         ✓      ✓    ✗    ✗    ✓    ✗    ✗    ✗     37.5%
CON-146908      ✓      ✓    ✓    ✓    ✓    ✓    ✓    ✓    100.0%
NCE-2387        ✓      ✗    ✗    ✗    ✗    ✗    ✗    ✗     12.5%
```

**Key Service Interface:**

```python
class FolderCoverageService:
    async def compute_coverage(self, jira_id: str) -> CoverageResult
    async def compute_all_coverage(self) -> list[CoverageResult]
    async def get_coverage_matrix(self, filters: CoverageFilters) -> CoverageMatrix
    async def get_coverage_summary(self) -> CoverageSummary
    async def get_missing_merges(self) -> list[MissingMerge]
```

---

### 5.4 Module 4 — Content Verification Engine

**Responsibility:** Verify that files are truly identical across folders using SHA256 hashing.

**This is the most critical differentiator.** Existence ≠ correctness. A file can exist in a folder but contain different content.

**Verification Pipeline:**

```
For each Jira ticket:
  1. Identify all files changed by commits linked to this Jira
  2. For each file:
     a. Get the file content from each folder at HEAD (latest commit)
     b. Compute SHA256 hash
     c. Compare hashes across all folders
     d. Record: file_path, folder, sha256, file_size, last_modified_commit

  Comparison Logic:
     - If all hashes identical → IDENTICAL
     - If hashes differ       → DIFFERENT (flag which folders diverge)
     - If file missing        → MISSING
```

**Content Retrieval Strategy:**

| Method | When | Performance |
|--------|------|-------------|
| `git show <sha>:<path>` | For specific commit versions | Fast, precise |
| `git ls-tree + git cat-file` | For bulk HEAD content | Batch-friendly |
| GitHub Contents API | When no local clone exists | Rate-limited |

**Hash Computation:**

```python
import hashlib

def compute_file_hash(content: bytes) -> str:
    """SHA256 hash of raw file content, normalized."""
    # Normalize line endings to prevent false differences
    normalized = content.replace(b'\r\n', b'\n').rstrip(b'\n')
    return hashlib.sha256(normalized).hexdigest()
```

**Content Drift Detection:**

```
For each file present in 2+ folders:

  hashes = { folder: hash(content(folder, file)) for folder in folders }

  groups = group_by_value(hashes)

  if len(groups) == 1:
      status = IDENTICAL
      drift_score = 0.0
  else:
      status = DIFFERENT
      majority_hash = mode(hashes.values())
      drift_score = 1 - (count(majority_hash) / len(hashes))

  Result:
    ContentVerificationResult {
      file_path, status, drift_score,
      folder_hashes: dict[str, str],
      majority_hash, divergent_folders,
      file_sizes: dict[str, int]
    }
```

**Key Service Interface:**

```python
class ContentVerificationService:
    async def verify_jira(self, jira_id: str) -> list[ContentVerificationResult]
    async def verify_file_across_folders(self, file_path: str) -> ContentVerificationResult
    async def verify_all(self) -> ContentVerificationSummary
    async def get_drift_report(self) -> DriftReport
    async def compute_file_hash(self, content: bytes) -> str
```

---

### 5.5 Module 5 — Merge Delay Analytics

**Responsibility:** Measure how long it takes for changes to propagate from initial commit to all target folders.

**Delay Calculation:**

```
For each Jira:

  initial_commit_date = MIN(commit_date) across all commits for this Jira

  For each folder:
    folder_merge_date = MIN(commit_date) WHERE folder = this_folder AND jira = this_jira

  first_merge_date   = MIN(folder_merge_date)   across all folders
  latest_merge_date  = MAX(folder_merge_date)    across all folders (NULL if not all merged)

  propagation_delay  = latest_merge_date - initial_commit_date   (in days)
  first_response     = first_merge_date - initial_commit_date    (in days)

  delay_classification:
    0–3 days   → HEALTHY  (🟢)
    4–14 days  → WARNING  (🟡)
    15+ days   → CRITICAL (🔴)
```

**Delay Metrics Per Folder:**

```
folder_avg_delay = AVG(folder_merge_date - initial_commit_date) per folder
folder_max_delay = MAX(folder_merge_date - initial_commit_date) per folder
folder_p95_delay = PERCENTILE_95(delays) per folder
```

**Key Service Interface:**

```python
class MergeDelayService:
    async def compute_delay(self, jira_id: str) -> DelayResult
    async def compute_all_delays(self) -> list[DelayResult]
    async def get_delay_stats(self) -> DelayStatistics
    async def get_folder_delay_ranking(self) -> list[FolderDelayRank]
    async def get_delay_trend(self, period: str) -> list[DelayTrendPoint]
```

---

### 5.6 Module 6 — Folder Health Engine

**Responsibility:** Produce a composite health score for each folder.

**Health Score Formula:**

```
For each folder:

  coverage_score    = (merged_jiras / expected_jiras) × 100
  consistency_score = (identical_files / total_files) × 100
  timeliness_score  = max(0, 100 - (avg_delay_days × 3))
  completeness      = (files_present / files_expected) × 100

  health_score = (
      coverage_score    × 0.35 +
      consistency_score × 0.30 +
      timeliness_score  × 0.20 +
      completeness      × 0.15
  )

  classification:
    90–100 → EXCELLENT (🟢)
    70–89  → GOOD      (🟢)
    50–69  → WARNING   (🟡)
    25–49  → POOR      (🟠)
    0–24   → CRITICAL  (🔴)
```

**Folder Ranking:**

```
All folders ranked by health_score descending.

Example Output:
  1. MET      → 94.2%  🟢 EXCELLENT
  2. JCF      → 91.0%  🟢 EXCELLENT
  3. vanilla  → 87.5%  🟢 GOOD
  4. MOD      → 72.3%  🟢 GOOD
  5. WMP      → 58.1%  🟡 WARNING
  6. IOM      → 51.9%  🟡 WARNING
  7. YATH     → 48.3%  🟠 POOR
  8. AMO      → 31.7%  🟠 POOR
```

**Key Service Interface:**

```python
class FolderHealthService:
    async def compute_health(self, folder: str) -> FolderHealthResult
    async def compute_all_health(self) -> list[FolderHealthResult]
    async def get_health_ranking(self) -> list[FolderHealthRank]
    async def get_health_trend(self, folder: str, period: str) -> list[HealthTrendPoint]
    async def get_weakest_folders(self, n: int = 3) -> list[FolderHealthResult]
```

---

### 5.7 Module 7 — Exception Detection Engine

**Responsibility:** Flag governance violations using deterministic, configurable rules.

**Rule Engine Architecture:**

```python
class GovernanceRule(ABC):
    """Base class for all governance rules."""

    rule_id: str
    name: str
    severity: Severity          # CRITICAL, HIGH, MEDIUM, LOW, INFO
    category: str               # COVERAGE, DELAY, CONSISTENCY, PROPAGATION
    enabled: bool = True

    @abstractmethod
    async def evaluate(self, context: RuleContext) -> list[RuleViolation]:
        """Evaluate this rule and return any violations found."""
        pass
```

**Built-in Rules:**

| Rule ID | Name | Condition | Severity |
|---------|------|-----------|----------|
| `GOV-001` | Vanilla-only commit | Jira exists only in `vanilla` and nowhere else | CRITICAL |
| `GOV-002` | Extreme low coverage | Coverage < 25% | HIGH |
| `GOV-003` | Severe merge delay | Merge delay > 30 days | HIGH |
| `GOV-004` | Content divergence | Same file has different content across folders | CRITICAL |
| `GOV-005` | Stale Jira | No activity in 60+ days with incomplete coverage | MEDIUM |
| `GOV-006` | Single-folder merge | Jira merged to only 1 non-vanilla folder | HIGH |
| `GOV-007` | Author isolation | Only 1 author touching a Jira with 10+ commits | MEDIUM |
| `GOV-008` | Folder regression | Folder health dropped 10+ points in a week | HIGH |
| `GOV-009` | Mass missing merge | 5+ Jiras missing from a single folder | HIGH |
| `GOV-010` | Zero propagation | Jira committed 14+ days ago, only in 1 folder | CRITICAL |

**Rule Configuration (YAML):**

```yaml
# config/rules.yaml
rules:
  - id: "GOV-001"
    name: "Vanilla-only commit"
    enabled: true
    severity: "CRITICAL"
    params:
      source_folder: "vanilla"
      min_age_days: 3     # ignore very recent commits

  - id: "GOV-002"
    name: "Extreme low coverage"
    enabled: true
    severity: "HIGH"
    params:
      threshold_pct: 25

  - id: "GOV-003"
    name: "Severe merge delay"
    enabled: true
    severity: "HIGH"
    params:
      max_delay_days: 30

  - id: "GOV-004"
    name: "Content divergence"
    enabled: true
    severity: "CRITICAL"
    params:
      ignore_whitespace: true
```

**Key Service Interface:**

```python
class ExceptionDetectionService:
    async def evaluate_all_rules(self) -> list[RuleViolation]
    async def evaluate_rule(self, rule_id: str) -> list[RuleViolation]
    async def get_violations(self, filters: ViolationFilters) -> PaginatedResult
    async def get_violation_summary(self) -> ViolationSummary
    async def acknowledge_violation(self, violation_id: str, user: str, note: str) -> None
```

---

### 5.8 Module 8 — Historical Trend Analytics

**Responsibility:** Track and visualize governance metrics over time.

**Snapshot Strategy:**

```
Daily Snapshot Job (Celery Beat, runs at 02:00 UTC):

  1. Compute current state of all metrics
  2. Insert into `governance_snapshots` table with today's date
  3. Metrics captured:
     - Total Jiras, Total Commits
     - Overall Coverage %
     - Per-folder coverage %
     - Per-folder health score
     - Missing merge count
     - Average delay days
     - Critical violation count
     - Content drift count
```

**Trend Queries:**

```sql
-- Weekly coverage trend
SELECT
    DATE_TRUNC('week', snapshot_date) AS week,
    AVG(overall_coverage_pct) AS avg_coverage,
    MIN(overall_coverage_pct) AS min_coverage,
    MAX(overall_coverage_pct) AS max_coverage
FROM governance_snapshots
WHERE snapshot_date >= NOW() - INTERVAL '12 weeks'
GROUP BY week
ORDER BY week;

-- Folder health over time
SELECT
    snapshot_date,
    folder_name,
    health_score
FROM folder_health_snapshots
WHERE snapshot_date >= NOW() - INTERVAL '90 days'
ORDER BY snapshot_date, folder_name;
```

**Key Service Interface:**

```python
class TrendAnalyticsService:
    async def capture_daily_snapshot(self) -> SnapshotResult
    async def get_coverage_trend(self, period: TrendPeriod) -> list[TrendPoint]
    async def get_folder_health_trend(self, folder: str, period: TrendPeriod) -> list[TrendPoint]
    async def get_delay_trend(self, period: TrendPeriod) -> list[TrendPoint]
    async def get_violation_trend(self, period: TrendPeriod) -> list[TrendPoint]
    async def get_comparative_trend(self, metric: str, folders: list[str]) -> ComparativeTrend
```

---

### 5.9 Module 9 — Executive Dashboard (Frontend)

**Responsibility:** Web-based dashboard for real-time governance visibility.

**Page Architecture:**

| Route | Page | Purpose |
|-------|------|---------|
| `/` | Dashboard Home | KPI cards, charts, quick actions |
| `/jiras` | Jira Explorer | Search, filter, sort all Jiras |
| `/jiras/[id]` | Jira Detail | Timeline, coverage matrix, content status |
| `/folders` | Folder Overview | Health scores, heatmap, ranking |
| `/folders/[name]` | Folder Detail | Coverage, missing merges, health history |
| `/commits` | Commit Log | Search by SHA, author, date, file |
| `/coverage` | Coverage Matrix | Full Jira × Folder matrix with filters |
| `/content` | Content Verification | Drift detection, hash comparison |
| `/violations` | Governance Issues | Active violations, severity, actions |
| `/trends` | Historical Trends | Charts: coverage, health, delay over time |
| `/reports` | Report Builder | Generate/download Excel & PDF reports |
| `/settings` | Configuration | Repos, folders, rules, users |

**Dashboard Home KPI Cards:**

```
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│  Total   │ │  Total   │ │ Coverage │ │ Missing  │ │ Critical │
│  Jiras   │ │ Commits  │ │    %     │ │ Merges   │ │  Issues  │
│   247    │ │  1,893   │ │  73.2%   │ │   142    │ │    18    │
│  +12 ▲   │ │  +89 ▲   │ │ +2.1% ▲ │ │  -8 ▼   │ │  -3 ▼   │
└──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘
```

**Component Architecture:**

```
src/
├── app/                          # Next.js App Router
│   ├── layout.tsx                # Root layout with sidebar
│   ├── page.tsx                  # Dashboard home
│   ├── jiras/
│   │   ├── page.tsx              # Jira list
│   │   └── [id]/page.tsx         # Jira detail
│   ├── folders/
│   │   ├── page.tsx              # Folder overview
│   │   └── [name]/page.tsx       # Folder detail
│   └── ...
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx
│   │   ├── Header.tsx
│   │   └── BreadcrumbNav.tsx
│   ├── dashboard/
│   │   ├── KPICard.tsx
│   │   ├── CoverageChart.tsx
│   │   ├── FolderHeatmap.tsx
│   │   └── RecentViolations.tsx
│   ├── data/
│   │   ├── DataTable.tsx
│   │   ├── CoverageMatrix.tsx
│   │   ├── TimelineView.tsx
│   │   └── FilterBar.tsx
│   └── ui/                       # Shared primitives
│       ├── Badge.tsx
│       ├── Card.tsx
│       ├── Progress.tsx
│       └── StatusIndicator.tsx
├── hooks/
│   ├── useApiQuery.ts
│   ├── useCoverage.ts
│   └── useFolderHealth.ts
├── lib/
│   ├── api.ts                    # Axios instance + interceptors
│   ├── types.ts                  # Shared TypeScript types
│   └── utils.ts                  # Formatting, date helpers
└── stores/
    ├── filterStore.ts            # Zustand: global filter state
    └── dashboardStore.ts         # Zustand: dashboard preferences
```

---

### 5.10 Module 10 — Reporting Engine

**Responsibility:** Generate downloadable Excel workbooks and PDF reports.

**Excel Workbook Structure:**

```
SENTINEL_Report_2026-06-05.xlsx
│
├── Sheet 1: Executive Summary
│   ├── Overall KPIs (total jiras, commits, coverage, health)
│   ├── Governance Score (0–100)
│   ├── Top 5 critical issues
│   └── Trend sparklines (last 4 weeks)
│
├── Sheet 2: Jira Summary
│   ├── Jira ID, Status, Commit Count, Author Count
│   ├── First Seen, Last Updated, Coverage %, Delay Days
│   └── Conditional formatting: RED for <50%, GREEN for 100%
│
├── Sheet 3: Detailed Merge Matrix
│   ├── Jira × Folder grid (✓/✗)
│   ├── Coverage % column
│   └── Color-coded cells
│
├── Sheet 4: Folder Analysis
│   ├── Folder Name, Health Score, Coverage Score
│   ├── Consistency Score, Timeliness Score
│   ├── Ranking
│   └── Chart: Folder Health Bar Chart
│
├── Sheet 5: Coverage Metrics
│   ├── Overall coverage stats
│   ├── Coverage distribution histogram
│   └── Weekly coverage trend
│
├── Sheet 6: Delay Analytics
│   ├── Per-Jira delay breakdown
│   ├── Per-folder average delays
│   └── Delay classification distribution
│
├── Sheet 7: Critical Issues
│   ├── All CRITICAL + HIGH violations
│   ├── Rule ID, Description, Affected Jira, Affected Folder
│   └── Recommended action
│
├── Sheet 8: Missing Merges
│   ├── Jira ID, Missing Folder, Days Since Commit
│   ├── Priority (based on delay + severity)
│   └── Sorted by priority descending
│
└── Sheet 9: Content Verification
    ├── File Path, Folders Present, Status (IDENTICAL/DIFFERENT/MISSING)
    ├── Hash values per folder
    ├── Drift score
    └── Divergent folders highlighted
```

**PDF Report Structure:**

```
SENTINEL_Report_2026-06-05.pdf
│
├── Cover Page
│   ├── SENTINEL logo + title
│   ├── Repository name
│   ├── Report date range
│   └── Generated timestamp
│
├── Executive Summary (1 page)
│   ├── Governance Score gauge
│   ├── KPI summary boxes
│   └── Top critical findings
│
├── Coverage Analysis (1–2 pages)
│   ├── Coverage distribution pie chart
│   ├── Coverage trend line chart
│   └── Top 10 lowest-coverage Jiras
│
├── Folder Health (1 page)
│   ├── Folder health bar chart
│   ├── Heatmap table
│   └── Weakest folders callout
│
├── Merge Delay Analysis (1 page)
│   ├── Delay distribution histogram
│   ├── Average delay per folder
│   └── Critical delays table
│
├── Content Verification (1 page)
│   ├── Consistency summary
│   ├── Drift report
│   └── Divergent files table
│
├── Governance Violations (1–2 pages)
│   ├── Violation severity breakdown
│   ├── Top violations table
│   └── Recommendations
│
└── Appendix
    ├── Methodology notes
    ├── Rule definitions
    └── Glossary
```

**Report Generation Pipeline:**

```
Request (API / Scheduled)
        │
        ▼
┌───────────────────┐
│  Data Aggregator   │ ──→ Collect all metrics from services
└────────┬──────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│ Excel  │ │  PDF   │
│Builder │ │Builder │
└───┬────┘ └───┬────┘
    │          │
    ▼          ▼
┌────────┐ ┌────────┐
│.xlsx   │ │ .pdf   │ ──→ Store in /reports/<timestamp>/
│ file   │ │ file   │
└────────┘ └────────┘
```

**Key Service Interface:**

```python
class ReportingService:
    async def generate_excel_report(self, config: ReportConfig) -> ReportResult
    async def generate_pdf_report(self, config: ReportConfig) -> ReportResult
    async def generate_full_report(self, config: ReportConfig) -> FullReportResult
    async def list_reports(self) -> list[ReportMetadata]
    async def get_report(self, report_id: str) -> ReportFile
    async def schedule_report(self, schedule: ReportSchedule) -> None
```

---

## 6. Database Architecture

### 6.1 Entity Relationship Diagram

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│ repositories │────<│     commits       │>────│   authors    │
└──────────────┘     └──────────────────┘     └──────────────┘
                            │
                     ┌──────┴───────┐
                     │              │
              ┌──────▼──────┐ ┌────▼────────────┐
              │ commit_jiras│ │  commit_files    │
              └──────┬──────┘ └────┬────────────┘
                     │             │
              ┌──────▼──────┐ ┌───▼─────────────┐
              │  jira_cache  │ │ file_hashes     │
              └─────────────┘ └─────────────────┘

┌──────────────────┐     ┌──────────────────┐
│  governance_     │     │  folder_health_  │
│  snapshots       │     │  snapshots       │
└──────────────────┘     └──────────────────┘

┌──────────────────┐     ┌──────────────────┐
│  rule_violations │     │  audit_log       │
└──────────────────┘     └──────────────────┘

┌──────────────────┐     ┌──────────────────┐
│  users           │     │  reports         │
└──────────────────┘     └──────────────────┘
```

### 6.2 Table Definitions

```sql
-- ============================================================
-- CORE TABLES
-- ============================================================

CREATE TABLE repositories (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL UNIQUE,
    url             VARCHAR(512) NOT NULL,
    default_branch  VARCHAR(128) DEFAULT 'main',
    folders         JSONB NOT NULL DEFAULT '[]',        -- ["vanilla","MET",...]
    jira_patterns   JSONB NOT NULL DEFAULT '[]',        -- ["[A-Z]{2,10}-\\d+"]
    sync_mode       VARCHAR(20) DEFAULT 'api',          -- api, git, hybrid
    sync_interval   INTEGER DEFAULT 30,                 -- minutes
    last_synced_at  TIMESTAMPTZ,
    last_sync_sha   VARCHAR(40),                        -- last processed commit SHA
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE authors (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    github_username VARCHAR(255),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE commits (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sha             VARCHAR(40) NOT NULL,
    repository_id   UUID NOT NULL REFERENCES repositories(id),
    author_id       UUID NOT NULL REFERENCES authors(id),
    branch          VARCHAR(255),
    message         TEXT NOT NULL,
    commit_date     TIMESTAMPTZ NOT NULL,
    ingested_at     TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(sha, repository_id)
);

CREATE INDEX idx_commits_sha ON commits(sha);
CREATE INDEX idx_commits_date ON commits(commit_date);
CREATE INDEX idx_commits_repo ON commits(repository_id);
CREATE INDEX idx_commits_author ON commits(author_id);

CREATE TABLE commit_files (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commit_id       UUID NOT NULL REFERENCES commits(id) ON DELETE CASCADE,
    file_path       VARCHAR(1024) NOT NULL,
    folder          VARCHAR(255),                       -- extracted folder name
    change_type     VARCHAR(20) NOT NULL,               -- ADDED, MODIFIED, DELETED, RENAMED
    additions       INTEGER DEFAULT 0,
    deletions       INTEGER DEFAULT 0,

    UNIQUE(commit_id, file_path)
);

CREATE INDEX idx_commit_files_folder ON commit_files(folder);
CREATE INDEX idx_commit_files_path ON commit_files(file_path);

CREATE TABLE commit_jiras (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commit_id       UUID NOT NULL REFERENCES commits(id) ON DELETE CASCADE,
    jira_id         VARCHAR(50) NOT NULL,

    UNIQUE(commit_id, jira_id)
);

CREATE INDEX idx_commit_jiras_jira ON commit_jiras(jira_id);

-- ============================================================
-- CONTENT VERIFICATION
-- ============================================================

CREATE TABLE file_hashes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id   UUID NOT NULL REFERENCES repositories(id),
    file_path       VARCHAR(1024) NOT NULL,
    folder          VARCHAR(255) NOT NULL,
    sha256_hash     VARCHAR(64) NOT NULL,
    file_size       BIGINT NOT NULL,
    last_commit_sha VARCHAR(40) NOT NULL,
    last_commit_date TIMESTAMPTZ NOT NULL,
    verified_at     TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(repository_id, file_path, folder)
);

CREATE INDEX idx_file_hashes_path ON file_hashes(file_path);
CREATE INDEX idx_file_hashes_folder ON file_hashes(folder);
CREATE INDEX idx_file_hashes_hash ON file_hashes(sha256_hash);

-- ============================================================
-- GOVERNANCE SNAPSHOTS (for trends)
-- ============================================================

CREATE TABLE governance_snapshots (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id       UUID NOT NULL REFERENCES repositories(id),
    snapshot_date       DATE NOT NULL,
    total_jiras         INTEGER NOT NULL,
    total_commits       INTEGER NOT NULL,
    overall_coverage_pct DECIMAL(5,2),
    missing_merge_count INTEGER,
    critical_violation_count INTEGER,
    avg_delay_days      DECIMAL(8,2),
    governance_score    DECIMAL(5,2),
    metadata            JSONB DEFAULT '{}',

    UNIQUE(repository_id, snapshot_date)
);

CREATE TABLE folder_health_snapshots (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id       UUID NOT NULL REFERENCES repositories(id),
    snapshot_date       DATE NOT NULL,
    folder_name         VARCHAR(255) NOT NULL,
    health_score        DECIMAL(5,2),
    coverage_score      DECIMAL(5,2),
    consistency_score   DECIMAL(5,2),
    timeliness_score    DECIMAL(5,2),
    completeness_score  DECIMAL(5,2),

    UNIQUE(repository_id, snapshot_date, folder_name)
);

-- ============================================================
-- EXCEPTION DETECTION
-- ============================================================

CREATE TABLE rule_violations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id       UUID NOT NULL REFERENCES repositories(id),
    rule_id             VARCHAR(20) NOT NULL,            -- GOV-001, GOV-002, ...
    severity            VARCHAR(20) NOT NULL,            -- CRITICAL, HIGH, MEDIUM, LOW
    category            VARCHAR(50) NOT NULL,            -- COVERAGE, DELAY, CONSISTENCY
    jira_id             VARCHAR(50),
    folder_name         VARCHAR(255),
    file_path           VARCHAR(1024),
    description         TEXT NOT NULL,
    details             JSONB DEFAULT '{}',
    is_acknowledged     BOOLEAN DEFAULT false,
    acknowledged_by     VARCHAR(255),
    acknowledged_at     TIMESTAMPTZ,
    acknowledge_note    TEXT,
    detected_at         TIMESTAMPTZ DEFAULT NOW(),
    resolved_at         TIMESTAMPTZ,

    UNIQUE(repository_id, rule_id, jira_id, folder_name, file_path)
);

CREATE INDEX idx_violations_severity ON rule_violations(severity);
CREATE INDEX idx_violations_rule ON rule_violations(rule_id);
CREATE INDEX idx_violations_jira ON rule_violations(jira_id);

-- ============================================================
-- REPORTING
-- ============================================================

CREATE TABLE reports (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id       UUID NOT NULL REFERENCES repositories(id),
    report_type         VARCHAR(20) NOT NULL,            -- EXCEL, PDF, FULL
    file_path           VARCHAR(1024) NOT NULL,
    file_size           BIGINT,
    config              JSONB DEFAULT '{}',
    generated_by        VARCHAR(255),
    generated_at        TIMESTAMPTZ DEFAULT NOW(),
    expires_at          TIMESTAMPTZ                      -- optional auto-cleanup
);

-- ============================================================
-- USERS & AUDIT
-- ============================================================

CREATE TABLE users (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username            VARCHAR(255) NOT NULL UNIQUE,
    email               VARCHAR(255) NOT NULL UNIQUE,
    password_hash       VARCHAR(512) NOT NULL,
    role                VARCHAR(20) NOT NULL DEFAULT 'viewer',  -- admin, manager, viewer
    is_active           BOOLEAN DEFAULT true,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    last_login_at       TIMESTAMPTZ
);

CREATE TABLE audit_log (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID REFERENCES users(id),
    action              VARCHAR(100) NOT NULL,           -- SYNC_STARTED, REPORT_GENERATED, ...
    entity_type         VARCHAR(50),                     -- repository, report, rule, ...
    entity_id           VARCHAR(255),
    details             JSONB DEFAULT '{}',
    ip_address          VARCHAR(45),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_date ON audit_log(created_at);
```

### 6.3 Materialized Views (Performance)

```sql
-- Pre-computed Jira summary for fast dashboard queries
CREATE MATERIALIZED VIEW mv_jira_summary AS
SELECT
    cj.jira_id,
    r.id AS repository_id,
    COUNT(DISTINCT c.sha) AS commit_count,
    COUNT(DISTINCT c.author_id) AS author_count,
    MIN(c.commit_date) AS first_seen,
    MAX(c.commit_date) AS last_updated,
    ARRAY_AGG(DISTINCT cf.folder) FILTER (WHERE cf.folder IS NOT NULL) AS touched_folders,
    COUNT(DISTINCT cf.folder) AS folder_count
FROM commit_jiras cj
JOIN commits c ON c.id = cj.commit_id
JOIN repositories r ON r.id = c.repository_id
LEFT JOIN commit_files cf ON cf.commit_id = c.id
GROUP BY cj.jira_id, r.id;

CREATE UNIQUE INDEX idx_mv_jira_summary ON mv_jira_summary(jira_id, repository_id);

-- Refresh strategy: after every sync completion
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_jira_summary;


-- Pre-computed coverage matrix
CREATE MATERIALIZED VIEW mv_coverage_matrix AS
SELECT
    cj.jira_id,
    r.id AS repository_id,
    f.folder_name AS expected_folder,
    CASE WHEN cf.folder IS NOT NULL THEN true ELSE false END AS is_merged,
    MIN(c.commit_date) FILTER (WHERE cf.folder = f.folder_name) AS merge_date
FROM commit_jiras cj
JOIN commits c ON c.id = cj.commit_id
JOIN repositories r ON r.id = c.repository_id
CROSS JOIN LATERAL unnest(r.folders::text[]) AS f(folder_name)
LEFT JOIN commit_files cf ON cf.commit_id = c.id AND cf.folder = f.folder_name
GROUP BY cj.jira_id, r.id, f.folder_name, cf.folder;

CREATE UNIQUE INDEX idx_mv_coverage ON mv_coverage_matrix(jira_id, repository_id, expected_folder);
```

### 6.4 Database Indexing Strategy

| Table | Index | Type | Purpose |
|-------|-------|------|---------|
| commits | `sha` | B-tree | Dedup during ingestion |
| commits | `commit_date` | B-tree | Date range filtering |
| commits | `repository_id` | B-tree | Per-repo queries |
| commit_jiras | `jira_id` | B-tree | Jira lookup |
| commit_files | `folder` | B-tree | Folder-based filtering |
| file_hashes | `(file_path, folder)` | Composite | Content comparison |
| file_hashes | `sha256_hash` | B-tree | Identical file detection |
| rule_violations | `severity` | B-tree | Dashboard filtering |
| audit_log | `created_at` | B-tree | Time-range audit queries |

---

## 7. API Architecture

### 7.1 API Design Principles

- **RESTful** with consistent resource naming
- **Versioned** under `/api/v1/`
- **Paginated** for all list endpoints (cursor-based or offset)
- **Filterable** with query parameters
- **Documented** via auto-generated OpenAPI (Swagger UI at `/docs`)

### 7.2 Endpoint Map

#### Repository Management

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/repositories` | List all repositories |
| `POST` | `/api/v1/repositories` | Add a repository |
| `GET` | `/api/v1/repositories/{id}` | Get repository details |
| `PUT` | `/api/v1/repositories/{id}` | Update repository config |
| `DELETE` | `/api/v1/repositories/{id}` | Remove repository |
| `POST` | `/api/v1/repositories/{id}/sync` | Trigger manual sync |
| `GET` | `/api/v1/repositories/{id}/sync/status` | Get sync status |

#### Commits

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/commits` | List commits (paginated, filterable) |
| `GET` | `/api/v1/commits/{sha}` | Get commit detail |
| `GET` | `/api/v1/commits/{sha}/files` | Get files changed in commit |

#### Jiras

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/jiras` | List all Jiras (paginated) |
| `GET` | `/api/v1/jiras/{jira_id}` | Get Jira detail with timeline |
| `GET` | `/api/v1/jiras/{jira_id}/coverage` | Get coverage for specific Jira |
| `GET` | `/api/v1/jiras/{jira_id}/timeline` | Get merge timeline |
| `GET` | `/api/v1/jiras/{jira_id}/content` | Get content verification |

#### Coverage

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/coverage` | Overall coverage summary |
| `GET` | `/api/v1/coverage/matrix` | Full Jira × Folder matrix |
| `GET` | `/api/v1/coverage/missing` | List all missing merges |

#### Content Verification

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/content/verification` | Content verification summary |
| `GET` | `/api/v1/content/drift` | Drift report |
| `GET` | `/api/v1/content/file/{path}` | Verify specific file |

#### Folders

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/folders` | List all folders with health |
| `GET` | `/api/v1/folders/{name}` | Get folder detail |
| `GET` | `/api/v1/folders/{name}/health` | Get health breakdown |
| `GET` | `/api/v1/folders/{name}/missing` | Missing merges for folder |
| `GET` | `/api/v1/folders/heatmap` | Folder heatmap data |
| `GET` | `/api/v1/folders/ranking` | Folder health ranking |

#### Merge Delay

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/delays` | Delay analytics summary |
| `GET` | `/api/v1/delays/ranking` | Folder delay ranking |

#### Violations

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/violations` | List violations (filterable) |
| `GET` | `/api/v1/violations/{id}` | Violation detail |
| `POST` | `/api/v1/violations/{id}/acknowledge` | Acknowledge violation |
| `GET` | `/api/v1/violations/summary` | Violation summary by severity |

#### Trends

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/trends/coverage` | Coverage trend data |
| `GET` | `/api/v1/trends/health` | Folder health trend |
| `GET` | `/api/v1/trends/delays` | Delay trend |
| `GET` | `/api/v1/trends/violations` | Violation trend |

#### Reports

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/reports/excel` | Generate Excel report |
| `POST` | `/api/v1/reports/pdf` | Generate PDF report |
| `POST` | `/api/v1/reports/full` | Generate both |
| `GET` | `/api/v1/reports` | List generated reports |
| `GET` | `/api/v1/reports/{id}/download` | Download report file |

#### Dashboard

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/dashboard/kpis` | Dashboard KPI cards data |
| `GET` | `/api/v1/dashboard/governance-score` | Governance score |
| `GET` | `/api/v1/dashboard/recent-activity` | Recent commits/merges |
| `GET` | `/api/v1/dashboard/critical-items` | Critical items needing attention |

#### Auth

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/auth/login` | Login, get JWT token |
| `POST` | `/api/v1/auth/refresh` | Refresh token |
| `GET` | `/api/v1/auth/me` | Current user info |

### 7.3 Standard Response Envelope

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "total": 247,
    "page": 1,
    "page_size": 50,
    "has_next": true,
    "generated_at": "2026-06-05T15:00:00Z"
  },
  "errors": null
}
```

### 7.4 Error Response Format

```json
{
  "success": false,
  "data": null,
  "meta": null,
  "errors": [
    {
      "code": "VALIDATION_ERROR",
      "field": "date_from",
      "message": "Invalid date format. Expected ISO 8601."
    }
  ]
}
```

---

## 8. Frontend Architecture

### 8.1 Design System

**Theme:** Dark mode primary with light mode toggle.

**Color Palette:**

| Token | Dark Mode | Light Mode | Usage |
|-------|-----------|------------|-------|
| `--bg-primary` | `#0F1117` | `#FFFFFF` | Main background |
| `--bg-secondary` | `#1A1D27` | `#F8F9FA` | Card background |
| `--bg-tertiary` | `#252830` | `#E9ECEF` | Nested containers |
| `--text-primary` | `#F1F3F5` | `#1A1D27` | Main text |
| `--text-secondary` | `#909296` | `#6C757D` | Secondary text |
| `--accent-blue` | `#4C9AFF` | `#2563EB` | Links, active states |
| `--accent-green` | `#36B37E` | `#16A34A` | Healthy, success |
| `--accent-yellow` | `#FFAB00` | `#D97706` | Warning states |
| `--accent-orange` | `#FF8B00` | `#EA580C` | Poor states |
| `--accent-red` | `#FF5630` | `#DC2626` | Critical, error |
| `--accent-purple` | `#6554C0` | `#7C3AED` | Special highlights |

**Status Colors (Governance-Specific):**

```css
--status-merged:    var(--accent-green);
--status-partial:   var(--accent-yellow);
--status-missing:   var(--accent-red);
--status-identical: var(--accent-green);
--status-different: var(--accent-red);
--status-healthy:   var(--accent-green);
--status-warning:   var(--accent-yellow);
--status-critical:  var(--accent-red);
```

### 8.2 State Management (Zustand)

```typescript
// stores/filterStore.ts
interface FilterState {
  repository: string | null;
  dateRange: { from: Date; to: Date } | null;
  folders: string[];
  severity: Severity[];
  searchQuery: string;
  setRepository: (repo: string) => void;
  setDateRange: (range: { from: Date; to: Date }) => void;
  toggleFolder: (folder: string) => void;
  reset: () => void;
}
```

### 8.3 Data Fetching Strategy

| Pattern | Library | Use Case |
|---------|---------|----------|
| **Server Components** | Next.js `fetch` | Initial page load (SSR) |
| **Client Queries** | SWR or TanStack Query | Interactive data (polling, refetch) |
| **Optimistic Updates** | Zustand + API | Acknowledge violations |
| **Real-time** | SSE (Server-Sent Events) | Sync progress updates |

### 8.4 Chart Components

| Chart | Library | Data Source |
|-------|---------|-------------|
| Coverage trend line | Recharts `<LineChart>` | `/api/v1/trends/coverage` |
| Folder health bar | Recharts `<BarChart>` | `/api/v1/folders/ranking` |
| Delay distribution | Recharts `<BarChart>` | `/api/v1/delays` |
| Coverage pie | Recharts `<PieChart>` | `/api/v1/coverage` |
| Folder heatmap | Custom `<HeatmapGrid>` | `/api/v1/folders/heatmap` |
| Governance gauge | Custom `<GaugeChart>` | `/api/v1/dashboard/governance-score` |

---

## 9. Data Flow Pipeline

### 9.1 Ingestion Flow

```
                    TRIGGER
                      │
           ┌──────────┼──────────┐
           │          │          │
     ┌─────▼───┐ ┌───▼────┐ ┌──▼──────┐
     │ Manual  │ │Webhook │ │Scheduled│
     │ (API)   │ │(GitHub)│ │(Celery) │
     └─────┬───┘ └───┬────┘ └──┬──────┘
           │          │         │
           └──────────┼─────────┘
                      │
                      ▼
            ┌─────────────────┐
            │  Celery Task:   │
            │  sync_repository│
            └────────┬────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
         ▼           ▼           ▼
   ┌──────────┐ ┌─────────┐ ┌──────────┐
   │ Fetch    │ │ Parse   │ │ Extract  │
   │ Commits  │ │ Files   │ │ Jira IDs │
   └────┬─────┘ └────┬────┘ └────┬─────┘
        │            │           │
        └────────────┼───────────┘
                     │
                     ▼
            ┌────────────────┐
            │  Database      │
            │  Batch Insert  │
            └────────┬───────┘
                     │
                     ▼
            ┌────────────────┐
            │  Post-Sync     │
            │  Tasks Chain   │
            └────────┬───────┘
                     │
       ┌─────────────┼─────────────┐
       │             │             │
       ▼             ▼             ▼
 ┌──────────┐ ┌──────────┐ ┌──────────┐
 │ Refresh  │ │ Content  │ │ Evaluate │
 │ Mat.Views│ │ Verify   │ │ Rules    │
 └──────────┘ └──────────┘ └──────────┘
                                │
                                ▼
                        ┌──────────┐
                        │ Capture  │
                        │ Snapshot │
                        └──────────┘
```

### 9.2 Analysis Flow (Post-Ingestion)

```
After new commits are ingested:

1. REFRESH materialized views (mv_jira_summary, mv_coverage_matrix)
2. COMPUTE folder coverage for affected Jiras
3. VERIFY content hashes for changed files
4. CALCULATE merge delays for affected Jiras
5. UPDATE folder health scores
6. EVALUATE governance rules
7. DETECT new violations
8. CAPTURE daily snapshot (if not yet captured today)
9. INVALIDATE Redis cache keys for affected entities
10. EMIT SSE event to connected dashboards
```

### 9.3 Celery Task Chain

```python
# tasks/pipeline.py
from celery import chain, group

def post_sync_pipeline(repo_id: str, affected_jiras: list[str]):
    """Execute the full analysis pipeline after a sync."""
    return chain(
        refresh_materialized_views.si(repo_id),
        group(
            compute_coverage.si(repo_id, affected_jiras),
            verify_content.si(repo_id, affected_jiras),
            compute_delays.si(repo_id, affected_jiras),
        ),
        compute_folder_health.si(repo_id),
        evaluate_governance_rules.si(repo_id),
        capture_snapshot_if_needed.si(repo_id),
        invalidate_caches.si(repo_id),
        notify_dashboard.si(repo_id),
    )
```

---

## 10. Security & Access Control

### 10.1 Authentication

| Component | Implementation |
|-----------|---------------|
| **Method** | JWT (JSON Web Tokens) |
| **Library** | python-jose + passlib |
| **Token Expiry** | Access: 30 min, Refresh: 7 days |
| **Password Hashing** | bcrypt via passlib |
| **Token Storage** | HttpOnly secure cookie (frontend) |

### 10.2 Role-Based Access Control (RBAC)

| Role | Permissions |
|------|------------|
| **Admin** | Full access: manage repos, users, rules, generate reports |
| **Manager** | Read all data, generate reports, acknowledge violations |
| **Viewer** | Read-only dashboard and data access |

**Permission Matrix:**

| Action | Admin | Manager | Viewer |
|--------|-------|---------|--------|
| View dashboard | ✓ | ✓ | ✓ |
| Search/filter data | ✓ | ✓ | ✓ |
| Download reports | ✓ | ✓ | ✓ |
| Generate reports | ✓ | ✓ | ✗ |
| Acknowledge violations | ✓ | ✓ | ✗ |
| Manage repositories | ✓ | ✗ | ✗ |
| Manage rules | ✓ | ✗ | ✗ |
| Manage users | ✓ | ✗ | ✗ |
| Trigger sync | ✓ | ✓ | ✗ |
| View audit log | ✓ | ✗ | ✗ |

### 10.3 Security Measures

| Measure | Implementation |
|---------|---------------|
| **CORS** | Whitelist frontend origin only |
| **Rate Limiting** | SlowAPI: 100 req/min per user, 10 req/min for auth |
| **Input Validation** | Pydantic models for all request bodies |
| **SQL Injection** | Parameterized queries via SQLAlchemy ORM |
| **XSS** | React auto-escapes, CSP headers via Nginx |
| **CSRF** | SameSite cookies + CSRF tokens |
| **Secrets** | Environment variables, never in code or config files |
| **GitHub Token** | Encrypted at rest, scoped to read-only repo access |

---

## 11. Background Processing

### 11.1 Celery Configuration

```python
# config/celery_config.py
broker_url = "redis://redis:6379/0"
result_backend = "redis://redis:6379/1"

task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]

task_acks_late = True                    # re-deliver on worker crash
task_reject_on_worker_lost = True
worker_prefetch_multiplier = 1           # fair scheduling
task_soft_time_limit = 300               # 5 min soft limit
task_time_limit = 600                    # 10 min hard limit
task_max_retries = 3
task_default_retry_delay = 60            # 1 min between retries
```

### 11.2 Task Registry

| Task | Queue | Schedule | Timeout | Retries |
|------|-------|----------|---------|---------|
| `sync_repository` | `ingestion` | Every 30 min (configurable) | 10 min | 3 |
| `compute_coverage` | `analysis` | Post-sync | 5 min | 2 |
| `verify_content` | `analysis` | Post-sync | 10 min | 2 |
| `compute_delays` | `analysis` | Post-sync | 5 min | 2 |
| `compute_folder_health` | `analysis` | Post-sync | 5 min | 2 |
| `evaluate_governance_rules` | `analysis` | Post-sync | 5 min | 2 |
| `capture_daily_snapshot` | `snapshots` | Daily 02:00 UTC | 5 min | 3 |
| `refresh_materialized_views` | `maintenance` | Post-sync | 2 min | 2 |
| `generate_excel_report` | `reports` | On-demand | 5 min | 1 |
| `generate_pdf_report` | `reports` | On-demand | 5 min | 1 |
| `cleanup_old_reports` | `maintenance` | Daily 03:00 UTC | 2 min | 1 |

### 11.3 Celery Beat Schedule

```python
# config/celery_beat.py
beat_schedule = {
    "sync-repos-periodic": {
        "task": "tasks.ingestion.sync_all_repositories",
        "schedule": crontab(minute="*/30"),
    },
    "daily-snapshot": {
        "task": "tasks.snapshots.capture_daily_snapshot",
        "schedule": crontab(hour=2, minute=0),
    },
    "cleanup-old-reports": {
        "task": "tasks.maintenance.cleanup_old_reports",
        "schedule": crontab(hour=3, minute=0),
    },
    "refresh-mat-views": {
        "task": "tasks.maintenance.refresh_all_materialized_views",
        "schedule": crontab(minute="*/15"),
    },
}
```

---

## 12. Caching Strategy

### 12.1 Redis Cache Layout

| Key Pattern | TTL | Purpose |
|-------------|-----|---------|
| `dashboard:kpis:{repo_id}` | 5 min | Dashboard KPI cards |
| `dashboard:gov_score:{repo_id}` | 5 min | Governance score |
| `jira:detail:{jira_id}` | 10 min | Jira detail page |
| `coverage:matrix:{repo_id}` | 10 min | Full coverage matrix |
| `coverage:summary:{repo_id}` | 5 min | Coverage summary |
| `folders:health:{repo_id}` | 10 min | Folder health scores |
| `folders:heatmap:{repo_id}` | 10 min | Heatmap data |
| `violations:summary:{repo_id}` | 5 min | Violation summary |
| `trends:{metric}:{repo_id}:{period}` | 30 min | Trend chart data |
| `sync:status:{repo_id}` | No TTL | Live sync status |

### 12.2 Cache Invalidation

```
On sync completion:
  - Invalidate ALL keys matching `*:{repo_id}`

On violation acknowledgment:
  - Invalidate `violations:*:{repo_id}`
  - Invalidate `dashboard:*:{repo_id}`

On rule config change:
  - Invalidate `violations:*`
  - Trigger `evaluate_governance_rules` task
```

---

## 13. Export & Reporting Pipeline

### 13.1 Excel Generation (openpyxl)

```python
class ExcelReportBuilder:
    """Builder pattern for constructing multi-sheet Excel workbooks."""

    def __init__(self, config: ReportConfig):
        self.wb = Workbook()
        self.config = config
        self.styles = ExcelStyles()       # Pre-defined styles

    def add_executive_summary(self, data: ExecutiveSummary) -> Self: ...
    def add_jira_summary(self, data: list[JiraSummary]) -> Self: ...
    def add_merge_matrix(self, data: CoverageMatrix) -> Self: ...
    def add_folder_analysis(self, data: list[FolderHealthResult]) -> Self: ...
    def add_coverage_metrics(self, data: CoverageSummary) -> Self: ...
    def add_delay_analytics(self, data: list[DelayResult]) -> Self: ...
    def add_critical_issues(self, data: list[RuleViolation]) -> Self: ...
    def add_missing_merges(self, data: list[MissingMerge]) -> Self: ...
    def add_content_verification(self, data: list[ContentVerificationResult]) -> Self: ...

    def build(self) -> bytes: ...
```

### 13.2 PDF Generation (WeasyPrint)

```
Template Engine: Jinja2
CSS Framework: Custom print stylesheet
Chart Embedding: matplotlib → PNG → inline base64

Pipeline:
  1. Collect all data from services
  2. Generate charts as PNG using matplotlib
  3. Render Jinja2 HTML templates with data + charts
  4. Convert HTML → PDF using WeasyPrint
  5. Return PDF bytes
```

**PDF Template Structure:**

```
backend/templates/reports/
├── base.html              # Base layout with headers/footers
├── cover.html             # Cover page
├── executive_summary.html
├── coverage_analysis.html
├── folder_health.html
├── delay_analysis.html
├── content_verification.html
├── governance_violations.html
├── appendix.html
└── styles/
    └── report.css         # Print-optimized CSS
```

---

## 14. Testing Strategy

### 14.1 Testing Pyramid

```
                    ┌───────────┐
                    │   E2E     │  ← 10% (Playwright)
                    │   Tests   │
                   ┌┴───────────┴┐
                   │ Integration  │  ← 30% (pytest + TestContainers)
                   │    Tests     │
                  ┌┴──────────────┴┐
                  │   Unit Tests    │  ← 60% (pytest)
                  └────────────────┘
```

### 14.2 Backend Testing

| Type | Tool | Target | Coverage Goal |
|------|------|--------|---------------|
| **Unit** | pytest | Services, utils, models | 90%+ |
| **Integration** | pytest + testcontainers | API endpoints, DB queries | 80%+ |
| **E2E** | pytest + httpx | Full API flows | Key flows |

**Test Fixtures:**

```python
# tests/conftest.py
@pytest.fixture
def sample_repository() -> Repository: ...

@pytest.fixture
def sample_commits(sample_repository) -> list[Commit]: ...

@pytest.fixture
def sample_jira_data() -> dict: ...

# Deterministic test data — no randomness
SAMPLE_COMMITS = [
    Commit(sha="abc123", message="NC-4928: Fix card mode", ...),
    Commit(sha="def456", message="CON-146908: Update config", ...),
]
```

**Key Test Cases:**

```
Module 1 (Collector):
  ✓ Extracts NC-4928 from "NC-4928: Fix card mode overrides"
  ✓ Extracts multiple Jiras from "NC-4928, CON-146908: Combined fix"
  ✓ Maps file "vanilla/config.csv" to folder "vanilla"
  ✓ Deduplicates commits by SHA
  ✓ Handles GitHub API rate limit gracefully

Module 3 (Coverage):
  ✓ 3/8 folders merged = 37.5% coverage
  ✓ 8/8 folders merged = 100% (MERGED status)
  ✓ 0/8 folders merged = 0% (MISSING status)

Module 4 (Content):
  ✓ Identical content → IDENTICAL status
  ✓ Different content → DIFFERENT status + drift score
  ✓ Missing file → MISSING status
  ✓ Line ending normalization doesn't cause false diffs

Module 7 (Rules):
  ✓ GOV-001: vanilla-only Jira → CRITICAL
  ✓ GOV-002: 12.5% coverage → HIGH
  ✓ GOV-003: 45-day delay → HIGH
  ✓ GOV-004: mismatched hashes → CRITICAL
```

### 14.3 Frontend Testing

| Type | Tool | Target |
|------|------|--------|
| **Unit** | Vitest + React Testing Library | Components, hooks, utils |
| **E2E** | Playwright | User flows, navigation |

### 14.4 Test Commands

```bash
# Backend
pytest                                    # Run all tests
pytest tests/unit/                        # Unit tests only
pytest tests/integration/                 # Integration tests only
pytest --cov=app --cov-report=html       # Coverage report

# Frontend
npm test                                  # Run all tests
npm run test:e2e                         # Playwright E2E

# Full suite
docker compose -f docker-compose.test.yml up --abort-on-container-exit
```

---

## 15. Deployment Architecture

### 15.1 Docker Compose (Production)

```yaml
# docker-compose.yml
version: '3.9'

services:
  # ─── DATABASE ───
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: sentinel
      POSTGRES_USER: sentinel
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sentinel"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ─── CACHE & BROKER ───
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s

  # ─── BACKEND API ───
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql+asyncpg://sentinel:${DB_PASSWORD}@postgres:5432/sentinel
      REDIS_URL: redis://redis:6379/0
      GITHUB_TOKEN: ${GITHUB_TOKEN}
      JWT_SECRET: ${JWT_SECRET}
      ENVIRONMENT: production
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - reports_data:/app/reports

  # ─── CELERY WORKER ───
  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.celery_app worker --loglevel=info --concurrency=4 -Q ingestion,analysis,reports,snapshots,maintenance
    environment:
      DATABASE_URL: postgresql+asyncpg://sentinel:${DB_PASSWORD}@postgres:5432/sentinel
      REDIS_URL: redis://redis:6379/0
      GITHUB_TOKEN: ${GITHUB_TOKEN}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - reports_data:/app/reports

  # ─── CELERY BEAT ───
  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.celery_app beat --loglevel=info
    environment:
      REDIS_URL: redis://redis:6379/0
    depends_on:
      redis:
        condition: service_healthy

  # ─── FRONTEND ───
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        NEXT_PUBLIC_API_URL: http://backend:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend

  # ─── REVERSE PROXY ───
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend

  # ─── MONITORING ───
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana-oss:latest
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
    ports:
      - "3001:3000"
    depends_on:
      - prometheus

volumes:
  postgres_data:
  redis_data:
  reports_data:
  prometheus_data:
  grafana_data:
```

### 15.2 Backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim AS base

WORKDIR /app

# System dependencies for WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 15.3 Frontend Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:20-alpine AS runner

WORKDIR /app

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["node", "server.js"]
```

---

## 16. CI/CD Pipeline

### 16.1 GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
name: SENTINEL CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  # ─── BACKEND TESTS ───
  backend-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: sentinel_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports: ["6379:6379"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run linting
        run: |
          cd backend
          ruff check .
          mypy app/
      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml -v
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/sentinel_test
          REDIS_URL: redis://localhost:6379/0

  # ─── FRONTEND TESTS ───
  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Run linting
        run: |
          cd frontend
          npm run lint
      - name: Run type check
        run: |
          cd frontend
          npm run type-check
      - name: Run tests
        run: |
          cd frontend
          npm test

  # ─── BUILD & PUSH ───
  build:
    needs: [backend-test, frontend-test]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker images
        run: |
          docker compose build
      - name: Run integration tests
        run: |
          docker compose -f docker-compose.test.yml up --abort-on-container-exit
```

### 16.2 Branch Strategy

```
main          ──────────────────────────── production-ready
  │
  ├── develop ──────────────────────────── integration branch
  │     │
  │     ├── feature/module-1-collector ── feature branches
  │     ├── feature/module-4-content
  │     └── fix/coverage-calc-rounding
  │
  └── release/v1.0.0 ──────────────────── release candidates
```

---

## 17. Monitoring & Observability

### 17.1 Metrics (Prometheus)

| Metric | Type | Labels |
|--------|------|--------|
| `sentinel_sync_duration_seconds` | Histogram | `repo`, `status` |
| `sentinel_sync_commits_total` | Counter | `repo` |
| `sentinel_api_request_duration_seconds` | Histogram | `method`, `path`, `status` |
| `sentinel_api_requests_total` | Counter | `method`, `path`, `status` |
| `sentinel_celery_task_duration_seconds` | Histogram | `task`, `status` |
| `sentinel_celery_tasks_total` | Counter | `task`, `status` |
| `sentinel_governance_score` | Gauge | `repo` |
| `sentinel_coverage_percent` | Gauge | `repo` |
| `sentinel_violations_active` | Gauge | `repo`, `severity` |
| `sentinel_db_query_duration_seconds` | Histogram | `query_name` |

### 17.2 Logging (structlog)

```python
# All log entries are structured JSON
{
    "timestamp": "2026-06-05T15:00:00Z",
    "level": "info",
    "event": "sync_completed",
    "repository": "main-config-repo",
    "commits_ingested": 47,
    "duration_seconds": 12.3,
    "new_jiras": ["NC-4928", "CON-146908"],
    "trace_id": "abc-123-def"
}
```

### 17.3 Health Check Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Basic liveness (HTTP 200) |
| `GET /health/ready` | Readiness (DB + Redis connected) |
| `GET /health/detailed` | Full status (DB, Redis, Celery, last sync) |

### 17.4 Grafana Dashboards

| Dashboard | Panels |
|-----------|--------|
| **API Performance** | Request rate, latency p50/p95/p99, error rate |
| **Celery Workers** | Task throughput, queue depth, worker utilization |
| **Database** | Query latency, connection pool usage, table sizes |
| **Governance** | Coverage trend, violation count, governance score |

---

## 18. Project Structure

```
SENTINEL/
│
├── .github/
│   └── workflows/
│       ├── ci.yml                     # CI/CD pipeline
│       └── release.yml                # Release automation
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app entry point
│   │   ├── celery_app.py              # Celery application
│   │   ├── config.py                  # Settings (pydantic-settings)
│   │   │
│   │   ├── api/                       # API Layer
│   │   │   ├── __init__.py
│   │   │   ├── deps.py                # Dependency injection
│   │   │   ├── middleware.py          # CORS, logging, auth middleware
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── router.py          # Aggregate v1 router
│   │   │       ├── repositories.py    # Repository endpoints
│   │   │       ├── commits.py         # Commit endpoints
│   │   │       ├── jiras.py           # Jira endpoints
│   │   │       ├── coverage.py        # Coverage endpoints
│   │   │       ├── content.py         # Content verification endpoints
│   │   │       ├── folders.py         # Folder endpoints
│   │   │       ├── delays.py          # Delay endpoints
│   │   │       ├── violations.py      # Violation endpoints
│   │   │       ├── trends.py          # Trend endpoints
│   │   │       ├── reports.py         # Report endpoints
│   │   │       ├── dashboard.py       # Dashboard endpoints
│   │   │       └── auth.py            # Auth endpoints
│   │   │
│   │   ├── models/                    # SQLAlchemy Models
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # Base model class
│   │   │   ├── repository.py
│   │   │   ├── commit.py
│   │   │   ├── jira.py
│   │   │   ├── file_hash.py
│   │   │   ├── violation.py
│   │   │   ├── snapshot.py
│   │   │   ├── report.py
│   │   │   ├── user.py
│   │   │   └── audit.py
│   │   │
│   │   ├── schemas/                   # Pydantic Schemas
│   │   │   ├── __init__.py
│   │   │   ├── repository.py
│   │   │   ├── commit.py
│   │   │   ├── jira.py
│   │   │   ├── coverage.py
│   │   │   ├── content.py
│   │   │   ├── folder.py
│   │   │   ├── delay.py
│   │   │   ├── violation.py
│   │   │   ├── trend.py
│   │   │   ├── report.py
│   │   │   ├── dashboard.py
│   │   │   ├── auth.py
│   │   │   └── common.py             # Pagination, filters, envelopes
│   │   │
│   │   ├── services/                  # Business Logic (10 Modules)
│   │   │   ├── __init__.py
│   │   │   ├── commit_collector.py    # Module 1
│   │   │   ├── jira_aggregation.py    # Module 2
│   │   │   ├── folder_coverage.py     # Module 3
│   │   │   ├── content_verification.py# Module 4
│   │   │   ├── merge_delay.py         # Module 5
│   │   │   ├── folder_health.py       # Module 6
│   │   │   ├── exception_detection.py # Module 7
│   │   │   ├── trend_analytics.py     # Module 8
│   │   │   ├── reporting/             # Module 10
│   │   │   │   ├── __init__.py
│   │   │   │   ├── excel_builder.py
│   │   │   │   ├── pdf_builder.py
│   │   │   │   ├── chart_generator.py
│   │   │   │   └── report_service.py
│   │   │   └── governance_score.py    # Composite scoring
│   │   │
│   │   ├── repositories/             # Data Access Layer
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # Base repository class
│   │   │   ├── commit_repo.py
│   │   │   ├── jira_repo.py
│   │   │   ├── folder_repo.py
│   │   │   ├── file_hash_repo.py
│   │   │   ├── violation_repo.py
│   │   │   ├── snapshot_repo.py
│   │   │   ├── report_repo.py
│   │   │   ├── user_repo.py
│   │   │   └── audit_repo.py
│   │   │
│   │   ├── rules/                     # Governance Rules (Module 7)
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # Abstract rule class
│   │   │   ├── gov_001_vanilla_only.py
│   │   │   ├── gov_002_low_coverage.py
│   │   │   ├── gov_003_severe_delay.py
│   │   │   ├── gov_004_content_drift.py
│   │   │   ├── gov_005_stale_jira.py
│   │   │   ├── gov_006_single_folder.py
│   │   │   ├── gov_007_author_isolation.py
│   │   │   ├── gov_008_folder_regression.py
│   │   │   ├── gov_009_mass_missing.py
│   │   │   ├── gov_010_zero_propagation.py
│   │   │   └── registry.py           # Rule auto-discovery
│   │   │
│   │   ├── tasks/                     # Celery Tasks
│   │   │   ├── __init__.py
│   │   │   ├── ingestion.py           # Sync tasks
│   │   │   ├── analysis.py            # Coverage, content, delay tasks
│   │   │   ├── snapshots.py           # Daily snapshot task
│   │   │   ├── reports.py             # Report generation tasks
│   │   │   ├── maintenance.py         # Cleanup, mat. view refresh
│   │   │   └── pipeline.py            # Task chains/groups
│   │   │
│   │   ├── core/                      # Shared Utilities
│   │   │   ├── __init__.py
│   │   │   ├── database.py            # Async SQLAlchemy engine/session
│   │   │   ├── redis.py               # Redis client
│   │   │   ├── security.py            # JWT, password hashing
│   │   │   ├── logging.py             # structlog configuration
│   │   │   ├── exceptions.py          # Custom exception hierarchy
│   │   │   └── result.py              # ServiceResult[T] type
│   │   │
│   │   └── templates/                 # PDF Report Templates
│   │       └── reports/
│   │           ├── base.html
│   │           ├── cover.html
│   │           ├── executive_summary.html
│   │           └── styles/
│   │               └── report.css
│   │
│   ├── migrations/                    # Alembic Migrations
│   │   ├── env.py
│   │   ├── alembic.ini
│   │   └── versions/
│   │
│   ├── tests/
│   │   ├── conftest.py                # Shared fixtures
│   │   ├── factories.py              # Test data factories
│   │   ├── unit/
│   │   │   ├── test_commit_collector.py
│   │   │   ├── test_jira_aggregation.py
│   │   │   ├── test_folder_coverage.py
│   │   │   ├── test_content_verification.py
│   │   │   ├── test_merge_delay.py
│   │   │   ├── test_folder_health.py
│   │   │   ├── test_exception_detection.py
│   │   │   ├── test_trend_analytics.py
│   │   │   ├── test_reporting.py
│   │   │   └── test_governance_score.py
│   │   └── integration/
│   │       ├── test_api_commits.py
│   │       ├── test_api_jiras.py
│   │       ├── test_api_coverage.py
│   │       ├── test_pipeline.py
│   │       └── test_report_generation.py
│   │
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── pyproject.toml                 # ruff, mypy, pytest config
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── app/                       # Next.js App Router
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx               # Dashboard home
│   │   │   ├── globals.css
│   │   │   ├── jiras/
│   │   │   │   ├── page.tsx
│   │   │   │   └── [id]/page.tsx
│   │   │   ├── folders/
│   │   │   │   ├── page.tsx
│   │   │   │   └── [name]/page.tsx
│   │   │   ├── commits/page.tsx
│   │   │   ├── coverage/page.tsx
│   │   │   ├── content/page.tsx
│   │   │   ├── violations/page.tsx
│   │   │   ├── trends/page.tsx
│   │   │   ├── reports/page.tsx
│   │   │   └── settings/page.tsx
│   │   │
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── BreadcrumbNav.tsx
│   │   │   │   └── PageContainer.tsx
│   │   │   ├── dashboard/
│   │   │   │   ├── KPICard.tsx
│   │   │   │   ├── CoverageChart.tsx
│   │   │   │   ├── FolderHeatmap.tsx
│   │   │   │   ├── GovernanceGauge.tsx
│   │   │   │   ├── RecentViolations.tsx
│   │   │   │   └── ActivityFeed.tsx
│   │   │   ├── data/
│   │   │   │   ├── DataTable.tsx
│   │   │   │   ├── CoverageMatrix.tsx
│   │   │   │   ├── TimelineView.tsx
│   │   │   │   ├── FilterBar.tsx
│   │   │   │   └── SearchInput.tsx
│   │   │   ├── charts/
│   │   │   │   ├── LineChart.tsx
│   │   │   │   ├── BarChart.tsx
│   │   │   │   ├── PieChart.tsx
│   │   │   │   └── HeatmapGrid.tsx
│   │   │   └── ui/
│   │   │       ├── Badge.tsx
│   │   │       ├── Card.tsx
│   │   │       ├── Progress.tsx
│   │   │       ├── StatusIndicator.tsx
│   │   │       ├── Skeleton.tsx
│   │   │       └── Modal.tsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── useApiQuery.ts
│   │   │   ├── useCoverage.ts
│   │   │   ├── useFolderHealth.ts
│   │   │   ├── useViolations.ts
│   │   │   └── useTrends.ts
│   │   │
│   │   ├── lib/
│   │   │   ├── api.ts                 # Axios instance
│   │   │   ├── types.ts               # Shared TypeScript interfaces
│   │   │   ├── constants.ts           # Colors, status mappings
│   │   │   └── utils.ts               # Format helpers
│   │   │
│   │   └── stores/
│   │       ├── filterStore.ts
│   │       └── dashboardStore.ts
│   │
│   ├── public/
│   │   └── favicon.ico
│   │
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   └── .env.example
│
├── config/
│   ├── repositories.yaml              # Repository configuration
│   ├── rules.yaml                     # Governance rule configuration
│   └── folders.yaml                   # Folder aliases and metadata
│
├── db/
│   └── init.sql                       # Initial schema (for Docker)
│
├── nginx/
│   ├── nginx.conf                     # Reverse proxy config
│   └── ssl/                           # SSL certificates (self-signed for dev)
│
├── monitoring/
│   ├── prometheus.yml                 # Prometheus config
│   └── grafana/
│       └── dashboards/
│           ├── api-performance.json
│           ├── celery-workers.json
│           └── governance.json
│
├── scripts/
│   ├── setup.sh                       # First-time setup
│   ├── seed_data.py                   # Seed sample data for dev
│   └── migrate.sh                     # Run Alembic migrations
│
├── docker-compose.yml                 # Production compose
├── docker-compose.dev.yml             # Development compose (with hot reload)
├── docker-compose.test.yml            # Test compose
├── Makefile                           # Common commands
├── ARCHITECTURE.md                    # ← This file
├── README.md                          # Project README
├── CONTRIBUTING.md                    # Contribution guidelines
├── LICENSE                            # MIT License
└── .gitignore
```

---

## 19. Development Workflow

### 19.1 Local Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/org/SENTINEL.git
cd SENTINEL

# 2. Start infrastructure services
docker compose -f docker-compose.dev.yml up -d postgres redis

# 3. Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate          # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt
cp .env.example .env               # Configure your GitHub token, DB URL
alembic upgrade head               # Run migrations

# 4. Start backend
uvicorn app.main:app --reload --port 8000

# 5. Start Celery worker (separate terminal)
celery -A app.celery_app worker --loglevel=info

# 6. Frontend setup (separate terminal)
cd frontend
npm install
cp .env.example .env.local
npm run dev                        # Starts on port 3000
```

### 19.2 Makefile Commands

```makefile
# Makefile
.PHONY: dev test lint migrate seed clean

dev:                    ## Start all services in dev mode
	docker compose -f docker-compose.dev.yml up

test:                   ## Run all tests
	cd backend && pytest -v
	cd frontend && npm test

test-backend:           ## Run backend tests with coverage
	cd backend && pytest --cov=app --cov-report=term-missing -v

test-frontend:          ## Run frontend tests
	cd frontend && npm test

lint:                   ## Lint all code
	cd backend && ruff check . && mypy app/
	cd frontend && npm run lint

migrate:                ## Run database migrations
	cd backend && alembic upgrade head

migrate-create:         ## Create new migration
	cd backend && alembic revision --autogenerate -m "$(MSG)"

seed:                   ## Seed development data
	cd backend && python scripts/seed_data.py

clean:                  ## Stop and remove all containers
	docker compose down -v

build:                  ## Build production images
	docker compose build

deploy:                 ## Deploy to production
	docker compose up -d
```

### 19.3 Environment Variables

```bash
# backend/.env.example

# ─── Database ───
DATABASE_URL=postgresql+asyncpg://sentinel:password@localhost:5432/sentinel

# ─── Redis ───
REDIS_URL=redis://localhost:6379/0

# ─── GitHub ───
GITHUB_TOKEN=ghp_your_personal_access_token
# Create at: https://github.com/settings/tokens
# Required scope: repo (read-only)

# ─── Security ───
JWT_SECRET=change-this-to-a-random-64-char-string
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# ─── Application ───
ENVIRONMENT=development
LOG_LEVEL=DEBUG
CORS_ORIGINS=http://localhost:3000

# ─── Reports ───
REPORTS_DIR=/app/reports
REPORT_RETENTION_DAYS=30
```

---

## 20. Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Dashboard page load | < 1.5s | Time to interactive (TTI) |
| API response (list) | < 500ms | p95 latency |
| API response (detail) | < 200ms | p95 latency |
| Full sync (1000 commits) | < 60s | End-to-end ingestion |
| Coverage computation | < 5s | Full recalculation |
| Content verification | < 30s | Full repo scan |
| Excel report generation | < 15s | Full 9-sheet workbook |
| PDF report generation | < 20s | Full multi-page report |
| Concurrent users | 50+ | Without degradation |
| Database query | < 100ms | p95, using mat. views |

### 20.1 Performance Optimizations

| Optimization | Where | Impact |
|-------------|-------|--------|
| Materialized views | PostgreSQL | 10x faster dashboard queries |
| Redis caching | API layer | Eliminates repeated DB hits |
| Batch inserts | Ingestion | 500 commits per batch, 5x throughput |
| Connection pooling | SQLAlchemy | Reuse connections, reduce overhead |
| Async I/O | FastAPI + asyncpg | Non-blocking DB and HTTP calls |
| Incremental sync | Commit Collector | Only fetch new commits since last SHA |
| Worker concurrency | Celery | 4 concurrent workers for parallel analysis |
| Static generation | Next.js | Pre-render where possible |
| Debounced search | Frontend | Reduce API calls during typing |
| Lazy loading | Frontend | Load charts/tables on viewport entry |

---

## 21. Appendix: Decision Log

| # | Decision | Alternatives Considered | Rationale |
|---|----------|------------------------|-----------|
| D1 | PostgreSQL over SQLite | SQLite, MySQL | Need concurrent writes, JSONB, window functions, materialized views |
| D2 | FastAPI over Django | Django, Flask | Async native, auto-docs, Pydantic, lighter for API-only backend |
| D3 | Celery over APScheduler | APScheduler, Dramatiq, Huey | Most mature, supports chains/groups, Flower monitoring, horizontal scaling |
| D4 | Redis over RabbitMQ | RabbitMQ, SQS | Dual-purpose (cache + broker), simpler ops, sufficient for our throughput |
| D5 | openpyxl over xlsxwriter | xlsxwriter, pandas.to_excel | Read+write, chart API, conditional formatting, active maintenance |
| D6 | WeasyPrint over ReportLab | ReportLab, FPDF, Puppeteer | HTML/CSS templates (maintainable), good typography, no browser dependency |
| D7 | Recharts over Chart.js | Chart.js, D3, Nivo | React-native declarative API, sufficient chart types, good docs |
| D8 | Zustand over Redux | Redux, Jotai, Context API | Minimal boilerplate, TypeScript-first, sufficient for our state complexity |
| D9 | structlog over stdlib logging | stdlib logging, loguru | Structured JSON output, context binding, async-safe |
| D10 | SHA256 for content hashing | MD5, SHA1, xxhash | Cryptographic strength, no collision risk, stdlib support |
| D11 | YAML config over DB config | DB-stored config, TOML, JSON | Human-readable, version-controlled, easy to review in PRs |
| D12 | GitHub Actions over Jenkins | Jenkins, GitLab CI, CircleCI | Free for public repos, native GitHub integration, YAML-based |
| D13 | Prometheus+Grafana over Datadog | Datadog, New Relic, ELK | Fully free, self-hosted, industry standard for Docker monitoring |
| D14 | Alembic over raw SQL migrations | Django migrations, Flyway | Native SQLAlchemy integration, auto-generation, Python-based |

---

## Governance Score Formula

The composite governance score provides a single 0–100 metric for repository health.

```
Governance Score = (
    coverage_weight    × overall_coverage_pct +
    delay_weight       × delay_score +
    consistency_weight × consistency_score +
    missing_weight     × missing_merge_score
)

Where:
  coverage_weight    = 0.35
  delay_weight       = 0.25
  consistency_weight = 0.25
  missing_weight     = 0.15

  delay_score        = max(0, 100 - (avg_delay_days × 2.5))
  consistency_score  = (identical_files / total_verified_files) × 100
  missing_merge_score = max(0, 100 - (missing_merge_count × 0.5))

Classification:
  90–100 → A (Excellent)
  75–89  → B (Good)
  60–74  → C (Needs Improvement)
  40–59  → D (Poor)
  0–39   → F (Critical)
```

---

> **Document Version:** 1.0  
> **Last Updated:** 2026-06-05  
> **Author:** SENTINEL Engineering  
> **Status:** DRAFT — Pending team review
