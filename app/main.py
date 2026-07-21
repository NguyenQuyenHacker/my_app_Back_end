from fastapi import FastAPI
import asyncio
import os
import sys

# Quan trọng cho Windows + psycopg để sửa lỗi ProactorEventLoop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.routers.client import customer_info_router, customer_home_router, account_router, transfer_router, user_thread_router,auth_client_router, settings_router, savings_router, statistics_router, quota_router
from fastapi.middleware.cors import CORSMiddleware
from app.routers.admin import auth_admin_router, admin_user_bar_router,knowledge_bases_router
from app.jobs.reconcile_processing_job import reconcile_loop
from app.jobs.savings_maturity_job import maturity_loop

app = FastAPI()


@app.on_event("startup")
async def _start_reconcile_job() -> None:
    asyncio.create_task(reconcile_loop())


@app.on_event("startup")
async def _start_savings_maturity_job() -> None:
    asyncio.create_task(maturity_loop())
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_client_router.router)
app.include_router(customer_info_router.router)
app.include_router(customer_home_router.router)
app.include_router(account_router.router)
app.include_router(transfer_router.router)
app.include_router(user_thread_router.router)
app.include_router(settings_router.router)
app.include_router(savings_router.router)
app.include_router(statistics_router.router)
app.include_router(quota_router.router)

app.include_router(auth_admin_router.router)
app.include_router(admin_user_bar_router.router)
app.include_router(knowledge_bases_router.router)
