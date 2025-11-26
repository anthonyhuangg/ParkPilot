import enum

from database.setup import Base
from sqlalchemy import (
    JSON,
    TIMESTAMP,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)


class NodeType(enum.Enum):
    PARKING_SPOT = "PARKING_SPOT"
    ROAD = "ROAD"
    CAR_ENTRANCE = "CAR_ENTRANCE"
    CAR_EXIT = "CAR_EXIT"
    HUMAN_EXIT = "HUMAN_EXIT"
    WALL = "WALL"


class NodeStatus(enum.Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    RESERVED = "RESERVED"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"


class GraphNode(Base):
    __tablename__ = "graph_nodes"

    id = Column(Integer, primary_key=True)
    lot_id = Column(
        Integer,
        ForeignKey("parking_lots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type = Column(Enum(NodeType), nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    orientation = Column(Float)
    status = Column(Enum(NodeStatus), default=NodeStatus.AVAILABLE, nullable=False)
    label = Column(String)
    sensor_id = Column(String)
    attrs = Column(JSON, default={})
    expires_at = Column(DateTime)


class GraphEdge(Base):
    __tablename__ = "graph_edges"

    id = Column(Integer, primary_key=True)
    lot_id = Column(
        Integer,
        ForeignKey("parking_lots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_node_id = Column(Integer, ForeignKey("graph_nodes.id"), nullable=False)
    to_node_id = Column(Integer, ForeignKey("graph_nodes.id"), nullable=False)
    bidirectional = Column(Boolean, default=True)
    length_m = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    status = Column(String, default="OPEN", nullable=False)
    attrs = Column(JSON, default={})


class ParkingLot(Base):
    __tablename__ = "parking_lots"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=True)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    width = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(
        TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()
    )
