import uuid

from sqlalchemy import Column, Text, Integer, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from geoalchemy2 import Geometry

from app.db import Base


class RegionalObservation(Base):
    __tablename__ = "regional_observations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    source_name = Column(Text, nullable=False)
    source_url = Column(Text)
    dataset_category = Column(Text, nullable=False)
    observation_type = Column(Text)

    observed_at = Column(DateTime(timezone=True))
    year = Column(Integer)

    state = Column(Text, default="Oregon")
    county = Column(Text)
    city = Column(Text)
    zip_code = Column(Text)

    latitude = Column(Float)
    longitude = Column(Float)
    geometry = Column(Geometry("GEOMETRY", srid=4326))

    metric_name = Column(Text)
    metric_value = Column(Float)
    unit = Column(Text)

    confidence_level = Column(Text)
    raw_properties_json = Column(JSONB, default={})