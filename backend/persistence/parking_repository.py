from typing import List, Optional
from application.models.parking import EdgeResponse, NodeResponse
from database.models.parking import GraphNode, ParkingLot
from database.parking_database import EdgeDatabase, LotDatabase, NodeDatabase
from sqlalchemy.orm import Session


class ParkingRepository:
    """Repository for parking lot, nodes and edges."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.node_db = NodeDatabase(db)
        self.edge_db = EdgeDatabase(db)
        self.lot_db = LotDatabase(db)

    # Nodes
    def get_all_nodes_for_lot(self, lot_id: int) -> List[NodeResponse]:
        nodes = self.node_db.get_all_nodes_for_lot(lot_id)
        return [NodeResponse.model_validate(n) for n in nodes]

    def update_node_status(self, node_id: int, status: str) -> Optional[NodeResponse]:
        node = self.node_db.update_node_status(node_id, status)
        return NodeResponse.model_validate(node) if node else None

    def count_spots(self, lot_id: int) -> int:
        return self.node_db.count_spots(lot_id)

    def count_occupied_spots(self, lot_id: int) -> int:
        return self.node_db.count_occupied_spots(lot_id)

    def count_vacant_spots(self, lot_id: int) -> int:
        return self.node_db.count_vacant_spots(lot_id)

    # Edges
    def get_all_edges_for_lot(self, lot_id: int) -> List[EdgeResponse]:
        edges = self.edge_db.get_all_edges_for_lot(lot_id)
        return [EdgeResponse.model_validate(e) for e in edges]

    def get_node(self, node_id: int):
        return self.db.query(GraphNode).filter(GraphNode.id == node_id).first()

    def save(self, node):
        self.db.commit()
        self.db.refresh(node)

    # Lots
    def get_all_lots(self) -> List[ParkingLot]:
        return self.lot_db.get_all_lots()

    # Occupancy
    def get_occupancy_percentage(self, lot_id: int) -> float:
        total_spots = self.node_db.count_spots(lot_id)
        if total_spots == 0:
            return 0.0
        num_occupied = self.node_db.count_occupied_spots(lot_id)
        return (num_occupied / total_spots) * 100
