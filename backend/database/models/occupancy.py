from database.setup import Base
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func


class Occupancy(Base):
    __tablename__ = "occupancy"
    id = Column(Integer, primary_key=True)
    lot_id = Column(Integer, nullable=False)
    node_id = Column(Integer, nullable=False)
    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
