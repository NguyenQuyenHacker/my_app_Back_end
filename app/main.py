from fastapi import FastAPI
import asyncio
import sys

# Quan trọng cho Windows + psycopg để sửa lỗi ProactorEventLoop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.routers.client import user_router, account_router, transfer_router, user_thread_router,auth_client_router
from fastapi.middleware.cors import CORSMiddleware
from app.routers.admin import auth_admin_router, admin_user_bar_router,knowledge_bases_router
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_client_router.router) 
app.include_router(user_router.router)
app.include_router(account_router.router)
app.include_router(transfer_router.router)
app.include_router(user_thread_router.router)

app.include_router(auth_admin_router.router)
app.include_router(admin_user_bar_router.router)
app.include_router(knowledge_bases_router.router)
