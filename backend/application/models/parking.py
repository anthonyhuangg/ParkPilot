from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class NodeOut(BaseModel):
    id: int
    lot_id: int
    type: str
    x: float
    y: float
    label: Optional[str]
    status: str
    expires_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class EdgeOut(BaseModel):
    id: int
    from_node_id: int
    to_node_id: int
    length_m: float


class NodeResponse(BaseModel):
    id: int
    lot_id: int
    type: str
    x: float
    y: float
    label: Optional[str]
    status: str
    expires_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class EdgeResponse(BaseModel):
    from_node_id: int
    to_node_id: int
    length_m: float
    weight: float
    status: str
    bidirectional: bool


class RouteResponse(BaseModel):
    node_ids: List[int]
    coords: List[List[float]]  # [[x,y],[x,y],...]
    total_distance_m: float


class LotResponse(BaseModel):
    lot_id: int
    dimensions: dict
    nodes: List[dict]


class LotSummary(BaseModel):
    lot_id: int
    lot_name: str
    location: str
    longitude: float
    latitude: float
    total_spots: int
    num_occupied: int
    num_available: int
    occupancy_percentage: float


class MultiLotSummary(BaseModel):
    lots_summary: List[LotSummary]


class SpotRecommendation(BaseModel):
    spot_node_id: int
    spot_label: Optional[str]
    spot_orientation: Optional[float]
    route: RouteResponse


class ExitRouteResponse(BaseModel):
    exit_node_id: int
    node_ids: List[int]
    coords: List[List[float]]
    total_distance_m: float


class AlternativeRoutesResponse(BaseModel):
    routes: List[RouteResponse]


class SpotPreferences(BaseModel):
    orientation: Optional[float] = None
    max_distance: Optional[float] = None


class PathValidationRequest(BaseModel):
    node_ids: List[int]


class PathValidationResponse(BaseModel):
    valid: bool
    reason: str
    blocked_edges: Optional[List[List[int]]] = None
