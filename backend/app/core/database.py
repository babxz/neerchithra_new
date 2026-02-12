# backend/app/core/database.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Enum, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import enum

SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/neerchithra"
# For Supabase: "postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class WaterBodyType(str, enum.Enum):
    LAKE = "lake"
    RIVER = "river"
    TANK = "tank"
    RESERVOIR = "reservoir"
    CANAL = "canal"
    POND = "pond"

class Status(str, enum.Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    RESTORED = "restored"

class WaterBody(Base):
    __tablename__ = "water_bodies"
    
    id = Column(String, primary_key=True, index=True)  # WB-TN-001
    name = Column(String, index=True)
    name_tamil = Column(String, nullable=True)
    type = Column(Enum(WaterBodyType))
    district = Column(String, index=True)
    taluk = Column(String)
    village = Column(String)
    
    # Geospatial
    latitude = Column(Float)
    longitude = Column(Float)
    area_hectares = Column(Float)
    max_depth_m = Column(Float)
    capacity_mcm = Column(Float)
    boundary_geojson = Column(JSON)  # Polygon coordinates
    
    # Status
    status = Column(Enum(Status), default=Status.HEALTHY)
    health_score = Column(Float, default=100.0)  # 0-100
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    satellite_data = relationship("SatelliteData", back_populates="water_body")
    alerts = relationship("Alert", back_populates="water_body")
    restoration_projects = relationship("RestorationProject", back_populates="water_body")
    
    # ML Features
    degradation_rate = Column(Float, default=0.0)
    flood_risk_score = Column(Float, default=0.0)
    encroachment_percentage = Column(Float, default=0.0)

class SatelliteData(Base):
    __tablename__ = "satellite_data"
    
    id = Column(Integer, primary_key=True)
    water_body_id = Column(String, ForeignKey("water_bodies.id"))
    capture_date = Column(DateTime)
    image_url = Column(String)
    cloud_cover_percentage = Column(Float)
    resolution_m = Column(Float)
    
    # NDWI Analysis
    ndwi_score = Column(Float)  # -1 to 1
    water_spread_hectares = Column(Float)
    vegetation_index = Column(Float)
    
    # Change detection
    change_from_previous = Column(Float)  # Percentage
    change_type = Column(String)  # encroachment, drought, flood, stable
    
    source = Column(String, default="sentinel-2")  # sentinel-2, landsat-8
    processed_at = Column(DateTime, default=datetime.utcnow)
    
    water_body = relationship("WaterBody", back_populates="satellite_data")

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True)
    water_body_id = Column(String, ForeignKey("water_bodies.id"))
    alert_type = Column(String)  # encroachment, pollution, flood_risk, drought
    severity = Column(String)  # low, medium, high, critical
    detected_date = Column(DateTime, default=datetime.utcnow)
    description = Column(Text)
    evidence_image_urls = Column(JSON)  # List of URLs
    coordinates = Column(JSON)  # [lat, lon]
    status = Column(String, default="open")  # open, investigating, resolved, false_positive
    
    ai_confidence = Column(Float)  # 0-1
    model_version = Column(String)
    
    water_body = relationship("WaterBody", back_populates="alerts")

class RestorationProject(Base):
    __tablename__ = "restoration_projects"
    
    id = Column(String, primary_key=True)  # RP-TN-001
    water_body_id = Column(String, ForeignKey("water_bodies.id"))
    start_date = Column(DateTime)
    estimated_end_date = Column(DateTime)
    actual_end_date = Column(DateTime, nullable=True)
    
    budget_inr = Column(Float)
    funding_source = Column(String)  # state, central, ngo, private
    contractor_name = Column(String)
    contractor_contact = Column(String)
    
    current_phase = Column(String)  # planning, execution, monitoring, completed
    completion_percentage = Column(Float, default=0.0)
    
    impact_metrics = Column(JSON)  # {area_restored, biodiversity_score, water_quality_improvement}
    
    water_body = relationship("WaterBody", back_populates="restoration_projects")
