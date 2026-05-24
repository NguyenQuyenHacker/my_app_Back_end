# Báo cáo scan project `my-app-BE` — chuẩn bị refactor `app/db/database.py`

> **Mode:** READ-ONLY. Không sửa, không tạo (trừ chính file báo cáo này), không xóa file nào.
> **Generated:** 2026-05-24

---

## PHẦN 1 — Cấu trúc project

### 1.1. Tree `my-app-BE/` (depth 3, đã ẩn `__pycache__`, `.git`, `.venv`, `.pytest_cache`)

```
my-app-BE/
├── .gitignore
├── README.md
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── dependencies.py            (file riêng, KHÁC với app/core/dependencies.py)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── constants.py
│   │   ├── dependencies.py
│   │   └── security.py
│   ├── crud/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── user_preferences_crud.py
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py            ← refactor target
│   ├── jobs/
│   │   ├── __init__.py
│   │   ├── reconcile_processing_job.py
│   │   └── savings_maturity_job.py
│   ├── models/                    (14 file model)
│   ├── routers/
│   │   ├── admin/  (3 routers + __init__)
│   │   └── client/ (10 routers + __init__)
│   ├── schemas/
│   │   ├── admin/  (6 files)
│   │   ├── client/ (9 files)
│   │   └── auth_schema.py
│   ├── services/
│   │   ├── admin/  (4 files + knowledge_base/rag/)
│   │   └── client/ (13 files)
│   ├── tests/  (4 file test)
│   └── utils/
│       ├── embedding_utils.py
│       └── security.py
├── app-agent/                     (LangGraph agent — project con riêng)
│   ├── .env                       ← (CHƯA track git, đã .gitignore)
│   ├── .gitignore
│   ├── langgraph.json
│   ├── pyproject.toml
│   ├── .langgraph_api/            (state local của langgraph dev server)
│   └── my_agent/
│       ├── __init__.py
│       ├── agent.py
│       ├── data/bank_codes.json
│       ├── prompts/system_prompt.md
│       └── src/
│           ├── bank_codes.py
│           ├── config.py
│           └── tool/
│               ├── _http.py
│               ├── account_tool.py
│               ├── search_tool.py
│               └── transfer_tool.py
└── scripts/
    ├── savings.sql
    └── transfer_sessions.sql
```

### 1.2. Toàn bộ file Python trong `app/`

> Đếm: **~80 file .py** dưới `app/`. Đường dẫn đầy đủ (rút gọn thành relative cho dễ đọc):

```
app/__init__.py
app/main.py
app/dependencies.py
app/core/__init__.py
app/core/config.py
app/core/constants.py
app/core/dependencies.py
app/core/security.py
app/crud/__init__.py
app/crud/user.py
app/crud/user_preferences_crud.py
app/db/__init__.py
app/db/database.py
app/jobs/__init__.py
app/jobs/reconcile_processing_job.py
app/jobs/savings_maturity_job.py
app/models/__init__.py
app/models/account_model.py
app/models/admin_model.py
app/models/card_model.py
app/models/customer_model.py
app/models/enums.py
app/models/external_bank_account_model.py
app/models/idempotency_key_model.py
app/models/knowledge_bases_model.py
app/models/ledger_entry_model.py
app/models/ledger_model.py
app/models/savings_account_model.py
app/models/savings_product_model.py
app/models/system_account_model.py
app/models/transaction_model.py
app/models/transfer_model.py
app/models/transfer_session_model.py
app/models/user_model.py
app/models/user_preferences_model.py
app/models/user_thread_model.py
app/routers/admin/__init__.py
app/routers/admin/admin_user_bar_router.py
app/routers/admin/auth_admin_router.py
app/routers/admin/knowledge_bases_router.py
app/routers/client/__init__.py
app/routers/client/account_router.py
app/routers/client/agent_proxy_router.py
app/routers/client/auth_client_router.py
app/routers/client/customer_home_router.py
app/routers/client/customer_info_router.py
app/routers/client/savings_router.py
app/routers/client/settings_router.py
app/routers/client/statistics_router.py
app/routers/client/transfer_router.py
app/routers/client/user_thread_router.py
app/schemas/__init__.py
app/schemas/auth_schema.py
app/schemas/admin/__init__.py
app/schemas/admin/admin_schema.py
app/schemas/admin/admin_thread_schema.py
app/schemas/admin/admin_transfer_schema.py
app/schemas/admin/admin_user_bar_schema.py
app/schemas/admin/admin_user_status_schema.py
app/schemas/admin/knowledge_bases_schema.py
app/schemas/client/__init__.py
app/schemas/client/account_schema.py
app/schemas/client/card_schema.py
app/schemas/client/customer_schema.py
app/schemas/client/register_schema.py
app/schemas/client/savings_schema.py
app/schemas/client/settings_schema.py
app/schemas/client/statistics_schema.py
app/schemas/client/transfer_schema.py
app/schemas/client/user_thread_schema.py
app/services/__init__.py
app/services/auth_service.py
app/services/chat_service.py
app/services/admin/__init__.py
app/services/admin/admin_info_service.py
app/services/admin/admin_thread_service.py
app/services/admin/admin_transfer_service.py
app/services/admin/admin_user_bar_service.py
app/services/admin/knowledge_base/rag/store_vectors_pg.py
app/services/client/__init__.py
app/services/client/account_service.py
app/services/client/customer_home_service.py
app/services/client/customer_info_service.py
app/services/client/idempotency_service.py
app/services/client/ledger_service.py
app/services/client/napas_mock.py
app/services/client/otp_service.py
app/services/client/register_service.py
app/services/client/savings_service.py
app/services/client/settings_service.py
app/services/client/statistics_service.py
app/services/client/transfer_common.py
app/services/client/transfer_external_service.py
app/services/client/transfer_internal_service.py
app/services/client/transfer_session_service.py
app/services/client/user_thread_service.py
app/tests/__init__.py
app/tests/test_chat.py
app/tests/test_health.py
app/tests/test_savings.py
app/tests/test_transfer.py
app/utils/__init__.py
app/utils/embedding_utils.py
app/utils/security.py
```

> ⚠️ **Lưu ý:** có **2 file `dependencies.py`** — `app/dependencies.py` và `app/core/dependencies.py`. Cần kiểm tra trùng lặp / xem cái nào đang được dùng (ngoài phạm vi báo cáo).

---

## PHẦN 2 — File `database.py` hiện tại

### 2.1. Đường dẫn

```
my-app-BE/app/db/database.py
```

### 2.2. Nội dung đầy đủ

```python
 1  # /app/db/database.py
 2  from sqlmodel import create_engine, Session
 3
 4  DATABASE_URL = "postgresql://fastapi_user:xxx@localhost:5432/banking_db"
 5  DATABASE_URL_LANGGRAPH = "postgresql+psycopg://fastapi_user:xxx@localhost:5433/banking_db"
 6  DATABASE_URL_ADMIN = "postgresql+psycopg://fastapi_user:xxx@localhost:5434/banking_db"
 7
 8  engine = create_engine(DATABASE_URL, echo=True)
 9  engine_admin = create_engine(DATABASE_URL_ADMIN, echo=True)
10  engine_langgraph = create_engine(DATABASE_URL_LANGGRAPH, echo=True)
11
12  def get_session():
13      with Session(engine) as session:
14          yield session
15
16
17  def get_session_admin():
18      with Session(engine_admin) as session:
19          yield session
20
21  def get_session_langgraph():
22      with Session(engine_langgraph) as session:
23          yield session
24
```
> Password thật `123456` đã che thành `xxx`.

---

## PHẦN 3 — Search dead code candidates

### 3.1. Symbol KHÔNG ai dùng (dead code candidate)

| Symbol | File ngoài database.py | Kết quả |
|---|---|---|
| `DATABASE_URL_LANGGRAPH` | — | ❌ **Không tìm thấy** |
| `engine_langgraph` | — | ❌ **Không tìm thấy** |
| `get_session_langgraph` | — | ❌ **Không tìm thấy** |

→ **3 symbol này là dead code, an toàn để xóa.**

### 3.2. Symbol CẦN GIỮ

| Symbol | File | Dòng | Nội dung |
|---|---|---|---|
| `DATABASE_URL_ADMIN` | app/services/admin/knowledge_base/rag/store_vectors_pg.py | 4 | `from app.db.database import DATABASE_URL_ADMIN` |
| `DATABASE_URL_ADMIN` | app/services/admin/knowledge_base/rag/store_vectors_pg.py | 16 | `pg_engine = PGEngine.from_connection_string(url=DATABASE_URL_ADMIN)` |
| `DATABASE_URL_ADMIN` | app/services/admin/knowledge_base/rag/store_vectors_pg.py | 23 | `pg_engine = PGEngine.from_connection_string(url=DATABASE_URL_ADMIN)` |
| `engine_admin` | — | — | ❌ Không file nào ngoài database.py dùng |
| `get_session_admin` | app/core/dependencies.py | 1, 19 | `from app.db.database import get_session_admin` / `SessionAdminDep = Annotated[Session, Depends(get_session_admin)]` |
| `get_session_admin` | app/routers/admin/auth_admin_router.py | 5, 16 | import + `Depends(get_session_admin)` |
| `get_session_admin` | app/routers/admin/knowledge_bases_router.py | 4 + (9 endpoint: 32, 43, 70, 83, 114, 131, 182, 210, 219) | import + 9 chỗ `Depends(get_session_admin)` |
| `get_session_admin` | app/routers/admin/admin_user_bar_router.py | 5 | `from app.db.database import get_session_admin, get_session` |
| `get_session` (chỉ form `(` hoặc `Depends()`) | app/core/dependencies.py | 11, 18 | `from app.db.database import get_session` + `SessionDep = Annotated[Session, Depends(get_session)]` |
| `get_session` | app/routers/client/user_thread_router.py | 7, 29, 42, 59, 75, 91, 107 | 6 endpoint dùng |
| `get_session` | app/routers/client/transfer_router.py | 7, 31, 55, 79, 94, 109, 124 | 6 endpoint dùng |
| `get_session` | app/routers/client/savings_router.py | 8, 30, 38, 48, 63, 78, 87, 97, 113 | 8 endpoint dùng |
| `get_session` | app/routers/client/auth_client_router.py | 5, 48, 62, 67 | 2 endpoint dùng (import lặp 2 lần dòng 5 & 48 — dư) |
| `get_session` | app/routers/client/statistics_router.py | 7, 25, 34, 43, 53, 62 | 5 endpoint dùng |
| `get_session` | app/routers/admin/admin_user_bar_router.py | 17, 24 | 2 endpoint dùng |
| `engine` (object) | app/jobs/reconcile_processing_job.py | 6, 22 | `from app.db.database import engine` + `with Session(engine) as session:` |
| `engine` (object) | app/jobs/savings_maturity_job.py | 7, 17 | `from app.db.database import engine` + `with Session(engine) as session:` |

### 3.3. Tất cả import từ `app/db/database`

| File | Dòng | Nội dung |
|---|---|---|
| app/core/dependencies.py | 1 | `from app.db.database import get_session_admin` |
| app/core/dependencies.py | 11 | `from app.db.database import get_session` |
| app/jobs/reconcile_processing_job.py | 6 | `from app.db.database import engine` |
| app/jobs/savings_maturity_job.py | 7 | `from app.db.database import engine` |
| app/routers/admin/auth_admin_router.py | 5 | `from app.db.database import get_session_admin` |
| app/routers/admin/knowledge_bases_router.py | 4 | `from app.db.database import get_session_admin` |
| app/routers/admin/admin_user_bar_router.py | 5 | `from app.db.database import get_session_admin, get_session` |
| app/routers/client/savings_router.py | 8 | `from app.db.database import get_session` |
| app/routers/client/auth_client_router.py | 5, 48 | `from app.db.database import get_session` (lặp 2 lần) |
| app/routers/client/statistics_router.py | 7 | `from app.db.database import get_session` |
| app/routers/client/transfer_router.py | 7 | `from app.db.database import get_session` |
| app/routers/client/user_thread_router.py | 7 | `from app.db.database import get_session` |
| app/services/admin/knowledge_base/rag/store_vectors_pg.py | 4 | `from app.db.database import DATABASE_URL_ADMIN` |

> Không tìm thấy import dạng `from .database` hay `from ..db.database` — toàn project dùng absolute import `from app.db.database`.

---

## PHẦN 4 — Hardcoded connection strings ngoài `database.py`

| File | Dòng | Nội dung |
|---|---|---|
| app-agent/my_agent/src/config.py | 13-16 | `VECTOR_DB_URL = os.getenv("VECTOR_DB_URL", "postgresql+psycopg://fastapi_user:xxx@host.docker.internal:5434/banking_db")` |

> ⚠️ **CHỖ DUY NHẤT** ngoài database.py còn hardcoded credentials. Đây là **fallback** của `os.getenv` — nếu env không có thì fallback dùng password thật → vẫn rủi ro lộ secret nếu commit.
>
> **Lưu ý:** file này thuộc project con `app-agent/` (LangGraph agent), chạy **trong container Docker**, nên dùng `host.docker.internal` thay vì `localhost`.

Không tìm thấy pattern hardcoded trong các file:
- `.yml`, `.yaml`, `.json`, `.toml`, `.ini`, `.conf` — ❌ Không tìm thấy
- `Dockerfile`, `docker-compose*` — ❌ Không tồn tại trong `my-app-BE`
- File `.env` ở `my-app-BE/` root — ❌ Không tồn tại

---

## PHẦN 5 — Dependencies

### 5.1. Nội dung `requirements.txt`

> ⚠️ **File đang ở encoding UTF-16 LE (với BOM `FF FE`)** — do PowerShell `pip freeze > requirements.txt` tạo ra. Khi sửa cần giữ nguyên encoding để không phá toàn bộ file. Khi deploy lên Linux/Docker, `pip install -r` có thể parse lỗi → nên convert về UTF-8.

Số package: **~200**. Trích các package liên quan đến DB và config:

```
SQLAlchemy==2.0.48
sqlmodel==0.0.37
psycopg==3.3.3
psycopg-binary==3.3.3
psycopg-pool==3.3.0
psycopg2-binary==2.9.11
asyncpg==0.31.0
pgvector==0.3.6
python-dotenv==1.2.2
pydantic==2.12.5
pydantic-settings==2.13.1
pydantic_core==2.41.5
fastapi==0.135.1
uvicorn==0.42.0
langgraph==1.1.2
langgraph-api==0.7.75
langgraph-checkpoint==4.0.1
langgraph-checkpoint-postgres==3.0.4
langgraph-cli==0.4.18
langgraph-prebuilt==1.0.8
langgraph-runtime-inmem==0.26.0
langgraph-sdk==0.3.11
langchain==1.2.12
langchain-classic==1.0.3
langchain-community==0.4.1
langchain-core==1.2.19
langchain-google-genai==4.2.1
langchain-postgres==0.0.17
langchain-text-splitters==1.1.1
```

### 5.2. Checklist package quan trọng

| Package | Có trong requirements? | Version |
|---|---|---|
| `psycopg2-binary` | ✅ Có | 2.9.11 |
| `psycopg2` (non-binary) | ❌ Không | — |
| `psycopg` (v3) | ✅ Có | 3.3.3 |
| `psycopg[binary]` (extra) | — | (đã có `psycopg-binary==3.3.3` riêng) |
| `psycopg-binary` | ✅ Có | 3.3.3 |
| `asyncpg` | ✅ Có | 0.31.0 |
| `sqlalchemy` | ✅ Có | 2.0.48 |
| `sqlmodel` | ✅ Có | 0.0.37 |
| `fastapi` | ✅ Có | 0.135.1 |
| `python-dotenv` | ✅ Có | 1.2.2 |
| `alembic` | ❌ **Không có** | — |

> 🔴 **Không có Alembic** → project chưa có migration system. Nếu deploy production nên cân nhắc bổ sung.
>
> 🟡 **Đang dùng cả `psycopg2-binary` + `psycopg3`** — hợp lý vì `database.py` có URL prefix khác nhau (`postgresql://` dùng psycopg2 mặc định, `postgresql+psycopg://` ép dùng psycopg3). Nhưng dài hạn nên thống nhất 1 driver.

### 5.3. `pyproject.toml` / `Pipfile`

- `my-app-BE/pyproject.toml` — ❌ Không có
- `my-app-BE/Pipfile` — ❌ Không có
- `my-app-BE/app-agent/pyproject.toml` — ✅ **CÓ** (project con cho LangGraph agent):

```toml
[build-system]
requires = ["setuptools>=61", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "app-agent"
version = "0.1.0"
description = "LangGraph agent project"
requires-python = ">=3.11"
dependencies = [
    "langchain",
    "langgraph",
    "langchain-google-genai",
    "langchain-postgres",
    "psycopg[binary]",
    "pgvector",
    "asyncpg",
    "sqlalchemy",
    "requests",
    "pydantic",
]

[tool.setuptools.packages.find]
where = ["."]
include = ["my_agent*"]
```

---

## PHẦN 6 — Git và env files

### 6.1. Nội dung `my-app-BE/.gitignore`

```gitignore
# Byte-compiled / optimized / DLL files
__pycache__/
*.pyc
*$py.class

# Virtual environments
venv/
.venv/
env/
.env/

# Environment variables
.env
.env.local
.env.*.local
.env.development
.env.production

# IDEs / Editor
.idea/
.vscode/
*.swp
*.swo
.DS_Store

# Testing / Coverage
.pytest_cache/
.coverage
htmlcov/
coverage.xml

# Logs
logs/
*.log

# Distribution / packaging
dist/
build/
*.egg-info/

# Misc
.cache/
```

**Pattern liên quan env:** `.env`, `.env.local`, `.env.*.local`, `.env.development`, `.env.production` — ✅ **đủ rộng**, file `.env` sẽ tự bị ignore khi tạo.

> ⚠️ Pattern **không phủ** `.env.example` và `.env.template` — đúng ý, vì những file mẫu cần commit.

### 6.2. File env tại `my-app-BE/` (root project)

| File | Tồn tại? |
|---|---|
| `.env` | ❌ |
| `.env.local` | ❌ |
| `.env.development` | ❌ |
| `.env.production` | ❌ |
| `.env.example` | ❌ |
| `.env.template` | ❌ |

→ **Không có file env nào** ở root `my-app-BE/`. Sau refactor sẽ tự tạo (hoặc bạn tự tạo) `.env`.

> ℹ️ Trong project con `my-app-BE/app-agent/` **CÓ** file `.env` (cho LangGraph agent). File này được `.gitignore` riêng của app-agent (dòng 12-13: `.env`, `.env.*`).

### 6.3. File `.env` tracked trong git?

| Path | Tracked? |
|---|---|
| `my-app-BE/.env` | ❌ Không (vì không tồn tại) |
| `my-app-BE/app-agent/.env` | ❌ Không (gitignored bởi `app-agent/.gitignore`) |

> ✅ **AN TOÀN** — không có `.env` của my-app-BE bị track. Trong toàn repo WD chỉ có `TEST_UI_LANGCHAIN/backend/.env` từng được add (status `AD` — đã add rồi delete), nhưng đó là sandbox khác, không liên quan my-app-BE.

---

## PHẦN 7 — Database config nơi khác

### 7.1. Folder `app-agent/` (depth 2)

```
my-app-BE/app-agent/
├── .env                          (gitignored, chứa GOOGLE_API_KEY, etc.)
├── .gitignore
├── langgraph.json
├── pyproject.toml
├── .langgraph_api/               (state local của langgraph dev — gitignored)
│   ├── .langgraph_checkpoint.1.pckl
│   ├── .langgraph_checkpoint.2.pckl
│   ├── .langgraph_checkpoint.3.pckl
│   ├── .langgraph_ops.pckl
│   ├── .langgraph_retry_counter.pckl
│   ├── store.pckl
│   └── store.vectors.pckl
└── my_agent/
    ├── __init__.py
    ├── agent.py
    ├── data/bank_codes.json
    ├── prompts/system_prompt.md
    └── src/
        ├── __init__.py
        ├── bank_codes.py
        ├── config.py             ← chứa hardcoded fallback URL (xem PHẦN 4)
        └── tool/
            ├── _http.py
            ├── account_tool.py
            ├── search_tool.py
            └── transfer_tool.py
```

### 7.2. `langgraph.json`

```json
{
    "dependencies": [
        "."
    ],
    "graphs": {
        "agent": "./my_agent/agent.py:graph"
    },
    "env": ".env"
}
```
> Không chứa password. `"env": ".env"` → LangGraph CLI sẽ tự load `app-agent/.env` khi build/run.

### 7.3. Folder `alembic/` hoặc `migrations/`

❌ **Không tìm thấy** — project chưa có migration framework.

> Schema DB hiện tại có vẻ được tạo qua `SQLModel.metadata.create_all()` hoặc `scripts/*.sql` thủ công (`scripts/savings.sql`, `scripts/transfer_sessions.sql`).

### 7.4. File `alembic.ini`

❌ **Không tồn tại.**

### 7.5. `docker-compose.yml`

❌ **KHÔNG có** trong `my-app-BE` (đã check toàn bộ).

> 🤔 **Vấn đề:** Stack `app-agent-*` (langgraph-api, langgraph-postgres, langgraph-redis) đang chạy trong Docker — nhưng compose file không nằm trong repo này. Có thể:
> - Được sinh tự động bởi `langgraph-cli` (chạy `langgraph build` / `langgraph up`).
> - Hoặc nằm ở project khác mà bạn `compose up` từ đó.
>
> → Nên kiểm tra: `langgraph-cli` đọc `langgraph.json` rồi tự generate Dockerfile + compose ephemeral. Lệnh `langgraph up` ở thư mục `app-agent/` sẽ dựng stack.
>
> Container `pgvector-db` cũng không thấy compose → chắc tạo `docker run` thủ công.

---

## PHẦN 8 — Entry point

### 8.1. FastAPI entry point: `app/main.py`

```python
 1  from fastapi import FastAPI
 2  import asyncio
 3  import sys
 4
 5  # Quan trọng cho Windows + psycopg để sửa lỗi ProactorEventLoop
 6  if sys.platform == "win32":
 7      asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
 8
 9  from app.routers.client import customer_info_router, customer_home_router, account_router, transfer_router, user_thread_router, auth_client_router, agent_proxy_router, settings_router, savings_router, statistics_router
10  from fastapi.middleware.cors import CORSMiddleware
11  from app.routers.admin import auth_admin_router, admin_user_bar_router, knowledge_bases_router
12  from app.jobs.reconcile_processing_job import reconcile_loop
13  from app.jobs.savings_maturity_job import maturity_loop
14
15  app = FastAPI()
16
17  @app.on_event("startup")
18  async def _start_reconcile_job() -> None:
19      asyncio.create_task(reconcile_loop())
20
21  @app.on_event("startup")
22  async def _start_savings_maturity_job() -> None:
23      asyncio.create_task(maturity_loop())
24
25  app.add_middleware(
26      CORSMiddleware,
27      allow_origins=["http://localhost:5173"],
28      allow_credentials=True,
29      allow_methods=["*"],
30      allow_headers=["*"],
31  )
32
33  app.include_router(auth_client_router.router)
34  app.include_router(customer_info_router.router)
35  app.include_router(customer_home_router.router)
36  app.include_router(account_router.router)
37  app.include_router(transfer_router.router)
38  app.include_router(user_thread_router.router)
39  app.include_router(agent_proxy_router.router)
40  app.include_router(settings_router.router)
41  app.include_router(savings_router.router)
42  app.include_router(statistics_router.router)
43  app.include_router(auth_admin_router.router)
44  app.include_router(admin_user_bar_router.router)
45  app.include_router(knowledge_bases_router.router)
```

> ⚠️ **Lưu ý:** `@app.on_event("startup")` đã **deprecated** từ FastAPI 0.93+ (hiện 0.135.1). Nên dùng `lifespan` context manager. Ngoài phạm vi refactor DB nhưng đáng note.
>
> 🟡 Nếu sau refactor `database.py` raise `RuntimeError` lúc import (do thiếu env), việc raise sẽ xảy ra **trước** `app = FastAPI()` (vì các import chain: main → routers → database). Uvicorn sẽ fail-fast — đúng spec.

### 8.2. `Dockerfile` cho FastAPI

❌ **Không tồn tại** trong `my-app-BE`. Backend FastAPI hiện chạy **trực tiếp trên host** (conda env `backend311`), KHÔNG containerize.

### 8.3. Script `start.sh` / `run.sh` / `entrypoint.sh`

❌ **Không tồn tại.** Chạy bằng lệnh thủ công:
```
conda activate F:\PYTHON\CONDA_ENV\backend311
uvicorn app.main:app --reload
```

---

## TỔNG KẾT — Điểm cần lưu ý khi refactor

### Bắt buộc

1. **Bỏ được dead code:** `DATABASE_URL_LANGGRAPH`, `engine_langgraph`, `get_session_langgraph` — 0 file ngoài tham chiếu.
2. **Giữ nguyên public API:** `DATABASE_URL`, `DATABASE_URL_ADMIN`, `engine`, `engine_admin`, `get_session`, `get_session_admin` — 13 file ngoài đang dùng.
3. **`requirements.txt` UTF-16:** không cần đụng (`python-dotenv` đã có 1.2.2). Nếu phải sửa, dùng tool giữ encoding.
4. **`.gitignore` đã đủ:** không cần thêm pattern `.env`.

### Cần xử thêm (ngoài refactor `database.py`)

5. **`app-agent/my_agent/src/config.py:15`** còn fallback hardcode password — nên fix cùng dịp.
6. **2 file `dependencies.py`** (`app/dependencies.py` và `app/core/dependencies.py`) — verify cái nào active.
7. **Import lặp** ở `app/routers/client/auth_client_router.py:5,48` — `from app.db.database import get_session` 2 lần.
8. **Không có Alembic** — production deploy cần.
9. **Không có Dockerfile / docker-compose** trong my-app-BE — nếu sau này muốn đóng gói backend cũng cần bổ sung.

### Sau refactor

10. Tạo `.env` thật ở `my-app-BE/` với 2 biến: `DATABASE_URL`, `DATABASE_URL_ADMIN`, `DB_ECHO=false`.
11. Tạo `.env.example` (commit được, không có password thật).
12. Smoke test: chạy uvicorn → confirm import database không raise → gọi 1 endpoint client + 1 endpoint admin → confirm DB connect OK.

---

*End of report.*
