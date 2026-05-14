from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.observability.logger import setup_logging, get_logger
from src.api.routes import review, workflow, agent, knowledge
from src.api.ws import router as ws_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("agentflow_startup", host=settings.host, port=settings.port)
    yield
    logger.info("agentflow_shutdown")


app = FastAPI(
    title="AgentFlow",
    description="Multi-Agent Development Workflow System",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(review.router, prefix="/api/v1")
app.include_router(workflow.router, prefix="/api/v1")
app.include_router(agent.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(ws_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
