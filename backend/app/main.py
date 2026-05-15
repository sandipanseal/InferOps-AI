from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.api.routes_chat import router as chat_router
from app.api.routes_dashboard import router as dashboard_router
from app.api.routes_evals import router as evals_router
from app.api.routes_rag import router as rag_router
from app.db.init_db import init_db
from app.api.routes_logs import router as logs_router
from app.api.routes_budget import router as budget_router
from app.api.routes_models import router as models_router

app = FastAPI(
    title="InferOps AI",
    description="LLM Deployment Console",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    await init_db()


@app.get("/health")
async def health():
    return {"status": "healthy"}


app.include_router(chat_router)
app.include_router(dashboard_router)
app.include_router(evals_router)
app.include_router(rag_router)
app.include_router(logs_router)
app.include_router(budget_router)
app.include_router(models_router)

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)