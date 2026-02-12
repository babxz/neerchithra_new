# backend/app/main.py
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn

from app.core.database import SessionLocal, engine, Base
from app.api import water_bodies, satellite, ml, analysis
from app.services.gee_service import GEEService

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="NeerChitra API",
    description="AI-Powered Water Body Intelligence for Tamil Nadu",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Include routers
app.include_router(water_bodies.router, prefix="/api/v1/water-bodies", tags=["Water Bodies"])
app.include_router(satellite.router, prefix="/api/v1/satellite", tags=["Satellite Data"])
app.include_router(ml.router, prefix="/api/v1/ml", tags=["Machine Learning"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])

@app.get("/")
async def root():
    return {
        "message": "NeerChitra API - Tamil Nadu Water Intelligence",
        "version": "2.0.0",
        "endpoints": {
            "docs": "/docs",
            "water_bodies": "/api/v1/water-bodies",
            "satellite": "/api/v1/satellite",
            "ml": "/api/v1/ml"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "neerchithra-api"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
