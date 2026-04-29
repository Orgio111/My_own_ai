"""Arajim — entrypoint. Starts FastAPI + supervisor + agent registry."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import agents, chat, memory, system, voice, ws
from app.config import settings
from app.core.nvidia_client import NvidiaError
from app.core.supervisor import Supervisor
from app.utils.logger import log


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("arajim.boot", host=settings.host, port=settings.port)
    supervisor = Supervisor()
    app.state.supervisor = supervisor
    task = asyncio.create_task(supervisor.run_forever())
    try:
        yield
    finally:
        log.info("arajim.shutdown")
        await supervisor.stop()
        task.cancel()


app = FastAPI(
    title="Arajim",
    description="Autonomous AI Operating System — NVIDIA-powered.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(NvidiaError)
async def _nvidia_error_handler(_: Request, exc: NvidiaError):
    msg = str(exc)
    status = 502
    if "NVIDIA_API_KEY not configured" in msg:
        status = 503
    return JSONResponse(status_code=status, content={"error": "nvidia_api", "detail": msg})


app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(system.router, prefix="/api/system", tags=["system"])
app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
app.include_router(voice.router, prefix="/api/voice", tags=["voice"])
app.include_router(ws.router, tags=["ws"])


@app.get("/")
async def root():
    return {"name": "Arajim", "status": "alive", "version": app.version}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
