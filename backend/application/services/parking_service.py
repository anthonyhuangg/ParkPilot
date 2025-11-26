import logging
from datetime import datetime, timedelta
from typing import Any, Iterable, List

import networkx as nx
from application.models.parking import LotSummary, MultiLotSummary, EdgeResponse
from database.models.parking import NodeStatus
from fastapi import HTTPException
from infrastructure.events import broadcast_event
from infrastructure.scheduler import schedule_ttl_reset
from persistence.parking_repository import ParkingRepository
from requests import Session
from .helper_service import haversine, heuristic_euclidean
from persistence.occupancy_repository import OccupancyRepository

logger = logging.getLogger("parkpilot.graph")


def _get(obj: Any, attr: str, default=None):
    """
    Helper to get attribute from object or dict.

    Args:
        obj: The object or dictionary to retrieve the attribute from.
        attr: The attribute name to retrieve.
        default: The default value to return if the attribute is not found.
    Returns:
        The value of the attribute or the default value.
    """
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return getattr(obj, attr, default)


class ParkingService:
    """Service for managing parking lot graphs and related operations."""

    def __init__(self):
        self.graphs: dict[int, nx.DiGraph] = {}

    def build_graph(self, lot_id: int, nodes: Iterable, edges: Iterable) -> None:
        """
        Builds a directed graph for a parking lot from nodes and edges data.

        Args:
            lot_id: The ID of the parking lot.
            nodes: An iterable of node data (dicts or objects).
            edges: An iterable of edge data (dicts or objects).

        Returns:
            None
        """
        G = nx.DiGraph()

        for n in nodes:
            node_id = _get(n, "id", None)

            attrs = {
                "lot_id": _get(n, "lot_id", lot_id),
                "x": float(_get(n, "x", 0.0)),
                "y": float(_get(n, "y", 0.0)),
                "type": _get(n, "type").value,
                "orientation": _get(n, "orientation", None),
                "status": _get(n, "status").value,
                "label": _get(n, "label", None),
            }
            G.add_node(node_id, **attrs)

        for e in edges:
            from_id = _get(e, "from_node_id", _get(e, "source_id"))
            to_id = _get(e, "to_node_id", _get(e, "target_id"))

            length = float(_get(e, "length_m", _get(e, "distance", 0.0)))
            weight = float(_get(e, "weight", length))
            bidir = bool(_get(e, "bidirectional", True))
            status = _get(e, "status", "OPEN")

            G.add_edge(
                from_id,
                to_id,
                length=length,
                weight=weight,
                bidirectional=bidir,
                status=status,
            )
            if bidir:
                G.add_edge(
                    to_id,
                    from_id,
                    length=length,
                    weight=weight,
                    bidirectional=bidir,
                    status=status,
                )

        self.graphs[lot_id] = G
        logger.info(
            "Built graph for lot %s: nodes=%d edges=%d",
            lot_id,
            G.number_of_nodes(),
            G.number_of_edges(),
        )

    def get_road_edges(self, lot_id: int) -> List[EdgeResponse]:
        """
        Retrieve all road edges from the graph of a specified parking lot.

        Args:
            lot_id: The ID of the parking lot.

        Returns:
            A list of EdgeResponse objects representing the road edges.
        """
        G = self.graphs.get(lot_id)
        if not G:
            raise HTTPException(status_code=404, detail="Graph not loaded")

        sortable_edges = []

        for u, v, data in G.edges(data=True):
            u_type = G.nodes[u].get("type")
            v_type = G.nodes[v].get("type")
            if u_type == "ROAD" and v_type == "ROAD":
                x_u = float(G.nodes[u].get("x", 0.0))
                y_u = float(G.nodes[u].get("y", 0.0))
                x_v = float(G.nodes[v].get("x", 0.0))
                y_v = float(G.nodes[v].get("y", 0.0))

                center_x = (x_u + x_v) / 2.0
                center_y = (y_u + y_v) / 2.0

                edge_dict = {
                    "from_node_id": u,
                    "to_node_id": v,
                    "length_m": data.get("length"),
                    "weight": data.get("weight"),
                    "status": data.get("status"),
                    "bidirectional": data.get("bidirectional"),
                }

                sortable_edges.append((center_y, center_x, edge_dict))

        # Sort by y (from top to bottom), then x (left to right)
        sortable_edges.sort(key=lambda t: (t[0], t[1]))

        return [edge_dict for _, _, edge_dict in sortable_edges]

    def get_lot_summaries(self, db: Session) -> MultiLotSummary:
        """
        Retrieve summaries for all parking lots.

        Args:
            db: Database session

        Returns:
            MultiLotSummary containing summaries of all parking lots.
        """
        parking_repository = ParkingRepository(db)
        all_lots = parking_repository.get_all_lots()

        lot_summaries = []
        for lot in all_lots:
            summary = LotSummary(
                lot_id=lot.id,
                lot_name=lot.name,
                location=lot.location,
                longitude=lot.longitude,
                latitude=lot.latitude,
                total_spots=parking_repository.count_spots(lot.id),
                num_occupied=parking_repository.count_occupied_spots(lot.id),
                num_available=parking_repository.count_vacant_spots(lot.id),
                occupancy_percentage=parking_repository.get_occupancy_percentage(
                    lot.id
                ),
            )
            lot_summaries.append(summary)
        return MultiLotSummary(lots_summary=lot_summaries)

    def closest_parking_lot(
        self, longitude: float, latitude: float, db: Session
    ) -> LotSummary:
        """
        Find the closest parking lot to the given geographic coordinates.

        Args:
            longitude: Longitude of the location
            latitude: Latitude of the location
            db: Database session

        Returns:
            LotSummary of the closest parking lot
        """
        parking_repository = ParkingRepository(db)
        all_lots = parking_repository.get_all_lots()

        closest_lot = None
        min_distance = float("inf")
        for lot in all_lots:
            distance = haversine(longitude, latitude, lot.longitude, lot.latitude)
            if distance < min_distance:
                min_distance = distance
                closest_lot = lot

        if closest_lot is None:
            return None

        summary = LotSummary(
            lot_id=closest_lot.id,
            lot_name=closest_lot.name,
            location=closest_lot.location,
            longitude=closest_lot.longitude,
            latitude=closest_lot.latitude,
            total_spots=parking_repository.count_spots(closest_lot.id),
            num_occupied=parking_repository.count_occupied_spots(closest_lot.id),
            num_available=parking_repository.count_vacant_spots(closest_lot.id),
            occupancy_percentage=parking_repository.get_occupancy_percentage(
                closest_lot.id
            ),
        )

        return summary

    def shortest_path(self, lot_id: int, start_node: int, end_node: int):
        """
        Find the shortest path between two nodes in the parking lot graph.

        Args:
            lot_id: Parking lot ID
            start_node: Starting node ID
            end_node: Ending node ID

        Returns:
            Dict with path details including node IDs, coordinates, and total distance.
        """
        G = self.graphs.get(lot_id)
        if not G:
            raise ValueError("Graph not loaded")

        if start_node not in G or end_node not in G:
            raise ValueError("Start or end node not in graph")
        path = nx.astar_path(
            G,
            source=start_node,
            target=end_node,
            heuristic=lambda u, v: heuristic_euclidean(G, u, v),
            weight="weight",
        )
        coords = [[G.nodes[n]["x"], G.nodes[n]["y"]] for n in path]
        total_distance = sum(
            G.edges[u, v]["length"] for u, v in zip(path[:-1], path[1:])
        )
        return {"node_ids": path, "coords": coords, "total_distance_m": total_distance}

    async def update_node_status(
        self, lot_id: int, node_id: int, status: str, ttl: int, db
    ):
        """
        Update the status of a parking node (spot) with proper state transitions.

        Args:
            lot_id: Parking lot ID
            node_id: Node ID to update
            status: New status ("AVAILABLE", "RESERVED", "OCCUPIED")
            ttl: Time-to-live in seconds for reservations
            db: Database session

        Returns:
            Dict with updated node information
        """
        repo = ParkingRepository(db)
        node = repo.get_node(node_id)
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")

        now = datetime.utcnow()
        requested_status = status.upper()

        # available to reserved
        if requested_status == "RESERVED":
            if node.status == NodeStatus.AVAILABLE or (
                node.status == NodeStatus.RESERVED
                and node.expires_at
                and node.expires_at < now
            ):
                node.status = NodeStatus.RESERVED
                node.expires_at = now + timedelta(seconds=ttl)
                repo.save(node)
                schedule_ttl_reset(lot_id, node_id, ttl)
                message = "Node reserved successfully"
            else:
                raise HTTPException(
                    status_code=409, detail="Spot not available or still reserved"
                )

        # reserved to occupied
        elif requested_status == "OCCUPIED":
            if node.status != NodeStatus.RESERVED:
                raise HTTPException(
                    status_code=409, detail="Can only occupy a reserved spot"
                )
            node.status = NodeStatus.OCCUPIED
            node.expires_at = None
            repo.save(node)
            message = "Node marked as occupied"

            # record historical occupancy
            try:
                occ_repo = OccupancyRepository(db)
                occ_repo.record_occupancy(lot_id, node.id, timestamp=now)
            except Exception:
                logging.exception("Failed to record occupancy event")

        # occupied to available
        elif requested_status == "AVAILABLE":
            if node.status != NodeStatus.OCCUPIED:
                raise HTTPException(
                    status_code=409, detail="Can only free an occupied spot"
                )
            node.status = NodeStatus.AVAILABLE
            node.expires_at = None
            repo.save(node)
            message = "Node released and available"

        else:
            raise HTTPException(status_code=400, detail=f"Invalid status '{status}'")

        # Update in-memory graph as well
        G = self.graphs.get(lot_id)
        if G and node_id in G.nodes:
            G.nodes[node_id]["status"] = node.status.value

        # Broadcast SSE update
        await broadcast_event(
            {
                "lot_id": lot_id,
                "node_id": node.id,
                "status": node.status.value,
                "expires_at": node.expires_at.isoformat() if node.expires_at else None,
            }
        )

        return {
            "message": message,
            "lot_id": lot_id,
            "node_id": node.id,
            "status": node.status.value,
            "expires_at": node.expires_at.isoformat() if node.expires_at else None,
        }

    def find_nearest_available_spot(
        self, lot_id: int, entrance_node: int, spot_preferences: dict = None
    ):
        """
        Find the nearest available parking spot from an entrance.

        Args:
            lot_id: Parking lot ID
            entrance_node: Starting node (typically CAR_ENTRANCE)
            spot_preferences: Optional dict with preferences like {"orientation": 90.0}

        Returns:
            Dict with spot details and route
        """
        G = self.graphs.get(lot_id)
        if not G:
            raise ValueError("Graph not loaded")

        available_spots = [
            node
            for node, data in G.nodes(data=True)
            if data.get("type") == "PARKING_SPOT" and data.get("status") == "AVAILABLE"
        ]

        if not available_spots:
            return None

        # Apply preferences filter if provided
        if spot_preferences:
            filtered = []
            for spot in available_spots:
                spot_data = G.nodes[spot]
                matches = all(
                    spot_data.get(key) == value
                    for key, value in spot_preferences.items()
                )
                if matches:
                    filtered.append(spot)
            if filtered:
                available_spots = filtered

        # Find shortest path to each spot
        best_spot = None
        best_distance = float("inf")
        best_path = None

        for spot in available_spots:
            try:
                path = nx.astar_path(
                    G,
                    source=entrance_node,
                    target=spot,
                    heuristic=lambda u, v: heuristic_euclidean(G, u, v),
                    weight="weight",
                )
                # Validate the path before considering it
                validation = self.validate_path_availability(lot_id, path)
                if not validation["valid"]:
                    continue  # Skip this spot if path is blocked

                distance = sum(
                    G.edges[u, v]["length"] for u, v in zip(path[:-1], path[1:])
                )

                if distance < best_distance:
                    best_distance = distance
                    best_spot = spot
                    best_path = path
            except nx.NetworkXNoPath:
                continue

        if not best_spot:
            return None

        coords = [[G.nodes[n]["x"], G.nodes[n]["y"]] for n in best_path]
        spot_data = G.nodes[best_spot]

        return {
            "spot_node_id": best_spot,
            "spot_label": spot_data.get("label"),
            "spot_orientation": spot_data.get("orientation"),
            "route": {
                "node_ids": best_path,
                "coords": coords,
                "total_distance_m": best_distance,
            },
        }

    def route_to_exit(self, lot_id: int, current_node: int):
        """
        Find the shortest route from the current node to the nearest exit.

        Args:
            lot_id: Parking lot ID
            current_node: Current node ID

        Returns:
            Dict with exit route details
        """
        G = self.graphs.get(lot_id)
        if not G:
            raise ValueError("Graph not loaded")

        exits = [
            node for node, data in G.nodes(data=True) if data.get("type") == "CAR_EXIT"
        ]
        if not exits:
            raise ValueError("No exits found in parking lot")

        # Find shortest path to any exit
        best_exit = None
        best_distance = float("inf")
        best_path = None

        for exit_node in exits:
            try:
                path = nx.astar_path(
                    G,
                    source=current_node,
                    target=exit_node,
                    heuristic=lambda u, v: heuristic_euclidean(G, u, v),
                    weight="weight",
                )

                # Validate the path
                validation = self.validate_path_availability(lot_id, path)
                if not validation["valid"]:
                    continue

                distance = sum(
                    G.edges[u, v]["length"] for u, v in zip(path[:-1], path[1:])
                )

                if distance < best_distance:
                    best_distance = distance
                    best_exit = exit_node
                    best_path = path
            except nx.NetworkXNoPath:
                continue

        if not best_path:
            raise ValueError("No path to exit found")

        coords = [[G.nodes[n]["x"], G.nodes[n]["y"]] for n in best_path]

        return {
            "exit_node_id": best_exit,
            "node_ids": best_path,
            "coords": coords,
            "total_distance_m": best_distance,
        }

    def get_alternative_routes(
        self, lot_id: int, start_node: int, end_node: int, num_routes: int = 3
    ):
        """
        Find multiple alternative routes between two nodes in the parking lot graph.

        Args:
            lot_id: Parking lot ID
            start_node: Starting node ID
            end_node: Ending node ID
            num_routes: Number of alternative routes to find

        Returns:
            Dict with list of alternative routes
        """
        G = self.graphs.get(lot_id)
        if not G:
            raise ValueError("Graph not loaded")

        try:
            # Use k-shortest paths algorithm
            paths = list(
                nx.shortest_simple_paths(
                    G, source=start_node, target=end_node, weight="weight"
                )
            )

            routes = []
            for path in paths[:num_routes]:
                # Validate each path
                validation = self.validate_path_availability(lot_id, path)
                if not validation["valid"]:
                    continue

                coords = [[G.nodes[n]["x"], G.nodes[n]["y"]] for n in path]
                distance = sum(
                    G.edges[u, v]["length"] for u, v in zip(path[:-1], path[1:])
                )
                routes.append(
                    {"node_ids": path, "coords": coords, "total_distance_m": distance}
                )

            return {"routes": routes}
        except nx.NetworkXNoPath:
            raise ValueError("No path exists between nodes")

    def validate_path_availability(self, lot_id: int, node_ids: list[int]) -> dict:
        """
        Validate if a given path is available (i.e., all edges are open and
        destination spot is available or reserved).

        Args:
            lot_id: Parking lot ID
            node_ids: List of node IDs representing the path

        Returns:
            Dict indicating if the path is valid and reason if not
        """
        G = self.graphs.get(lot_id)
        if not G:
            return {"valid": False, "reason": "Graph not loaded"}

        # Check all nodes exist
        for node_id in node_ids:
            if node_id not in G.nodes:
                return {"valid": False, "reason": f"Node {node_id} does not exist"}

        # Check each edge in path is open
        blocked_edges = []
        for i in range(len(node_ids) - 1):
            if not G.has_edge(node_ids[i], node_ids[i + 1]):
                return {
                    "valid": False,
                    "reason": f"No edge between {node_ids[i]} and {node_ids[i + 1]}",
                }

            edge_data = G.edges[node_ids[i], node_ids[i + 1]]
            if edge_data.get("status") != "OPEN":
                blocked_edges.append((node_ids[i], node_ids[i + 1]))

        if blocked_edges:
            return {
                "valid": False,
                "reason": "Path blocked",
                "blocked_edges": blocked_edges,
            }

        # Check destination node status
        dest = node_ids[-1]
        dest_data = G.nodes[dest]
        if dest_data.get("type") == "PARKING_SPOT":
            dest_status = dest_data.get("status")
            if dest_status not in ["AVAILABLE", "RESERVED"]:
                return {"valid": False, "reason": f"Destination spot is {dest_status}"}

        return {"valid": True, "reason": "Path is clear"}


parking_service = ParkingService()
