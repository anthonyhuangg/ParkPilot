from typing import Any, Dict, List, Optional

from database.models.parking import (
    GraphEdge,
    GraphNode,
    NodeStatus,
    NodeType,
    ParkingLot,
)
from sqlalchemy import func
from sqlalchemy.orm import Session


class NodeDatabase:
    def __init__(self, db: Session):
        self.db = db

    # --- Create ---
    def create_node(self, node_data: Dict[str, Any]) -> GraphNode:
        node = GraphNode(**node_data)
        self.db.add(node)
        self.db.commit()
        self.db.refresh(node)
        return node

    # --- Read ---
    def get_all_nodes_for_lot(self, lot_id: int) -> List[GraphNode]:
        return self.db.query(GraphNode).filter(GraphNode.lot_id == lot_id).all()

    def get_node_by_id(self, node_id: int) -> Optional[GraphNode]:
        return self.db.query(GraphNode).filter(GraphNode.id == node_id).one_or_none()

    # --- Update ---
    def update_node_status(self, node_id: int, status: str) -> Optional[GraphNode]:
        node = self.db.query(GraphNode).filter(GraphNode.id == node_id).one_or_none()
        if not node:
            return None

        node.status = status
        self.db.add(node)
        self.db.commit()
        self.db.refresh(node)
        return node

    def update_node_location(
        self, node_id: int, x: float, y: float
    ) -> Optional[GraphNode]:
        node = self.get_node_by_id(node_id)
        if not node:
            return None
        node.x = x
        node.y = y
        self.db.add(node)
        self.db.commit()
        self.db.refresh(node)
        return node

    # --- Delete ---
    def delete_node(self, node_id: int) -> bool:
        node = self.get_node_by_id(node_id)
        if not node:
            return False
        self.db.delete(node)
        self.db.commit()
        return True

    # --- Aggregates ---
    def count_nodes_by_type(self, lot_id: int, node_type: NodeType) -> int:
        return (
            self.db.query(func.count(GraphNode.id))
            .filter(GraphNode.lot_id == lot_id, GraphNode.type == node_type)
            .scalar()
        ) or 0

    def count_spots(self, lot_id: int) -> int:
        return self.count_nodes_by_type(lot_id, NodeType.PARKING_SPOT)

    def count_vacant_spots(self, lot_id: int) -> int:
        return (
            self.db.query(func.count(GraphNode.id))
            .filter(
                GraphNode.lot_id == lot_id,
                GraphNode.type == NodeType.PARKING_SPOT,
                GraphNode.status == NodeStatus.AVAILABLE,
            )
            .scalar()
        ) or 0

    def count_out_of_service_spots(self, lot_id: int) -> int:
        return (
            self.db.query(func.count(GraphNode.id))
            .filter(
                GraphNode.lot_id == lot_id,
                GraphNode.type == NodeType.PARKING_SPOT,
                GraphNode.status == NodeStatus.OUT_OF_SERVICE,
            )
            .scalar()
        ) or 0

    def count_occupied_spots(self, lot_id: int) -> int:
        return (
            self.db.query(func.count(GraphNode.id))
            .filter(
                GraphNode.lot_id == lot_id,
                GraphNode.type == NodeType.PARKING_SPOT,
                GraphNode.status == NodeStatus.OCCUPIED,
            )
            .scalar()
        ) or 0


class EdgeDatabase:
    def __init__(self, db: Session):
        self.db = db

    # --- Create ---
    def create_edge(self, edge_data: Dict[str, Any]) -> GraphEdge:
        edge = GraphEdge(**edge_data)
        self.db.add(edge)
        self.db.commit()
        self.db.refresh(edge)
        return edge

    # --- Read ---
    def get_all_edges_for_lot(self, lot_id: int) -> List[GraphEdge]:
        return self.db.query(GraphEdge).filter(GraphEdge.lot_id == lot_id).all()

    def get_edge_by_id(self, edge_id: int) -> Optional[GraphEdge]:
        return self.db.query(GraphEdge).filter(GraphEdge.id == edge_id).one_or_none()

    def get_edges_between(
        self, lot_id: int, from_node: int, to_node: int
    ) -> List[GraphEdge]:
        return (
            self.db.query(GraphEdge)
            .filter(
                GraphEdge.lot_id == lot_id,
                GraphEdge.from_node_id == from_node,
                GraphEdge.to_node_id == to_node,
            )
            .all()
        )

    # --- Update ---
    def update_edge_status(self, edge_id: int, status: str) -> Optional[GraphEdge]:
        edge = self.get_edge_by_id(edge_id)
        if not edge:
            return None
        edge.status = status
        self.db.add(edge)
        self.db.commit()
        self.db.refresh(edge)
        return edge

    def update_edge_weight(
        self, edge_id: int, weight: float, length_m: Optional[float] = None
    ) -> Optional[GraphEdge]:
        edge = self.get_edge_by_id(edge_id)
        if not edge:
            return None
        edge.weight = weight
        if length_m is not None:
            edge.length_m = length_m
        self.db.add(edge)
        self.db.commit()
        self.db.refresh(edge)
        return edge

    # --- Delete ---
    def delete_edge(self, edge_id: int) -> bool:
        edge = self.get_edge_by_id(edge_id)
        if not edge:
            return False
        self.db.delete(edge)
        self.db.commit()
        return True


class LotDatabase:
    def __init__(self, db: Session):
        self.db = db

    # --- Create ---
    def create_lot(self, lot_data: Dict[str, Any]) -> ParkingLot:
        lot = ParkingLot(**lot_data)
        self.db.add(lot)
        self.db.commit()
        self.db.refresh(lot)
        return lot

    # --- Read ---
    def get_lot_by_id(self, lot_id: int) -> Optional[ParkingLot]:
        return self.db.query(ParkingLot).filter(ParkingLot.id == lot_id).one_or_none()

    def get_all_lots(self) -> List[ParkingLot]:
        return self.db.query(ParkingLot).all()

    # --- Update ---
    def update_lot(self, lot_id: int, updates: Dict[str, Any]) -> Optional[ParkingLot]:
        lot = self.get_lot_by_id(lot_id)
        if not lot:
            return None
        for k, v in updates.items():
            if hasattr(lot, k):
                setattr(lot, k, v)
        self.db.add(lot)
        self.db.commit()
        self.db.refresh(lot)
        return lot

    # --- Delete ---
    def delete_lot(self, lot_id: int) -> bool:
        lot = self.get_lot_by_id(lot_id)
        if not lot:
            return False
        self.db.delete(lot)
        self.db.commit()
        return True
