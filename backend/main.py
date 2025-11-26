import glob
import logging
import os
import socket
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from application.services.parking_service import parking_service
from database import SessionLocal
from database.models.parking import GraphEdge, GraphNode, ParkingLot
from database.models.occupancy import Occupancy
from database.seed import seed_demo_data, seed_occupancy_data
from database.setup import create_tables
from presentation.routes.parking import router as parking_router
from presentation.routes.sse import router as sse_router
from presentation.routes.user import router as user_router
from presentation.routes.carbon_saving import router as carbon_saving_router

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("parkpilot")


# CORS origins based on environment
def _cors_origins():
    ENV = os.getenv("ENV", "development")
    if ENV == "development":
        hostname = os.getenv("FRONTEND_HOST") or socket.gethostname()
        local_ip = os.getenv("EXPO_HOST") or socket.gethostbyname(hostname)
        origins = [
            f"http://{local_ip}:8081",
            f"exp://{local_ip}:8081",
            "http://localhost:8081",
            "http://127.0.0.1:8081",
        ]
        logger.info(f"[CORS] Development mode: allowing local origins {origins}")
        return origins
    else:
        origins = [
            "https://parkpilot.com",
            "https://admin.parkpilot.com",
        ]
        logger.info(f"[CORS] Production mode: allowing only {origins}")
        return origins


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting ParkPilot backend (lifespan startup)")
    app.state.initialized = False

    try:
        create_tables()
        logger.info("Ensured DB tables exist (create_tables()).")
    except Exception as e:
        logger.warning(f"create_tables() failed or not required: {e}")

    # Seed data
    try:
        if os.getenv("SEED_ON_STARTUP", "1") == "1":
            base_dir = os.path.dirname(os.path.abspath(__file__))
            seed_dir = os.path.join(base_dir, "seed")

            db = SessionLocal()
            try:
                db.query(ParkingLot).delete()
                db.query(GraphEdge).delete()
                db.query(GraphNode).delete()
                db.query(Occupancy).delete()
                db.commit()

                for seed_file in glob.glob(os.path.join(seed_dir, "*.json")):
                    seed_demo_data(db, seed_file)
                    logger.info(f"Seeded {seed_file} data into the database.")

                seed_occupancy_data(db)
                logger.info("Seeded random occupancy data for all lots.")
            finally:
                db.close()
    except Exception as e:
        logger.exception("Failed to seed demo data: %s", e)

    # Load graphs from DB into in-memory GraphService
    try:
        db = SessionLocal()
        try:
            rows = db.query(GraphNode.lot_id).distinct().all()
            lot_ids = [r[0] for r in rows]
            if not lot_ids:
                logger.info("No lots found in DB to load into graph.")
            for lot_id in lot_ids:
                nodes = db.query(GraphNode).filter(GraphNode.lot_id == lot_id).all()
                edges = db.query(GraphEdge).filter(GraphEdge.lot_id == lot_id).all()
                parking_service.build_graph(lot_id, nodes, edges)
                logger.info(
                    f"Loaded graph for lot {lot_id}: nodes={len(nodes)} \
                    edges={len(edges)}"
                )
        finally:
            db.close()
    except Exception as e:
        logger.exception("Failed to load graphs from DB on startup: %s", e)

    app.state.initialized = True

    try:
        yield
    finally:
        logger.info("ParkPilot backend shutting down.")


app = FastAPI(title="ParkPilot", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router, prefix="/api")
app.include_router(parking_router, prefix="/api")
app.include_router(sse_router, prefix="/api")
app.include_router(carbon_saving_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
