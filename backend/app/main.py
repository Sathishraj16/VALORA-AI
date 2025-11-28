"""
VALORA FastAPI Application
Production-grade API with WebSocket support
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
import logging
import json
from typing import List, Dict

from .core.config import settings
from .models import init_db

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database initialization skipped: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down VALORA")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Multi-Agent Economic Digital Twin & Policy Intelligence Platform",
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# WebSocket connection manager
class ConnectionManager:
    """Manage WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, simulation_id: str):
        await websocket.accept()
        if simulation_id not in self.active_connections:
            self.active_connections[simulation_id] = []
        self.active_connections[simulation_id].append(websocket)
        logger.info(f"WebSocket connected to simulation {simulation_id}")
    
    def disconnect(self, websocket: WebSocket, simulation_id: str):
        if simulation_id in self.active_connections:
            self.active_connections[simulation_id].remove(websocket)
            logger.info(f"WebSocket disconnected from simulation {simulation_id}")
    
    async def broadcast(self, simulation_id: str, message: dict):
        if simulation_id in self.active_connections:
            for connection in self.active_connections[simulation_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send message: {e}")


manager = ConnectionManager()


# Import routers
from .api.simulations import router as simulations_router
from .api.policy import router as policy_router
from .api.blockchain import router as blockchain_router
from .api.auth import router as auth_router
from .api.agents import router as agents_router
from .api.crew import router as crew_router

# Include routers
app.include_router(
    auth_router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["Authentication"]
)

app.include_router(
    simulations_router,
    prefix=f"{settings.API_V1_PREFIX}/simulations",
    tags=["Simulations"]
)

app.include_router(
    policy_router,
    prefix=f"{settings.API_V1_PREFIX}/policy",
    tags=["Policy Intelligence"]
)

app.include_router(
    blockchain_router,
    prefix=f"{settings.API_V1_PREFIX}/blockchain",
    tags=["Blockchain"]
)

app.include_router(
    agents_router,
    prefix=f"{settings.API_V1_PREFIX}/agents",
    tags=["Agents"]
)

app.include_router(
    crew_router,
    prefix=f"{settings.API_V1_PREFIX}/crew",
    tags=["CrewAI Analytics"]
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "AI-Powered Multi-Agent Economic Digital Twin Platform",
        "docs": "/api/docs",
        "endpoints": {
            "simulations": f"{settings.API_V1_PREFIX}/simulations",
            "policy": f"{settings.API_V1_PREFIX}/policy",
            "blockchain": f"{settings.API_V1_PREFIX}/blockchain",
            "agents": f"{settings.API_V1_PREFIX}/agents",
            "crew": f"{settings.API_V1_PREFIX}/crew"
        }
    }


# WebSocket endpoint for real-time simulation updates
@app.websocket("/ws/simulation/{simulation_id}")
async def websocket_simulation(websocket: WebSocket, simulation_id: str):
    """WebSocket endpoint for real-time simulation streaming"""
    await manager.connect(websocket, simulation_id)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "subscribe":
                await websocket.send_json({
                    "type": "subscribed",
                    "simulation_id": simulation_id
                })
            elif message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, simulation_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, simulation_id)


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": 500
        }
    )
