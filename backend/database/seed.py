import json
import os
from math import sqrt

from database.models.parking import GraphEdge, GraphNode, ParkingLot
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
from database.models.occupancy import Occupancy

# Global offset to construct ids across multiple lots
node_id_offset = 0


def seed_demo_data(db: Session, json_path: str):
    """
    Load a parking lot graph (nodes + edges) from a JSON file and insert
    into the db.

    Args:
        db (Session): Active SQLAlchemy session
        json_path (str): Path to the seed JSON file containing lot layout

    Raises:
        FileNotFoundError: If the seed file doesn't exist
    """
    global node_id_offset

    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Seed JSON not found: {json_path}")

    with open(json_path, "r") as f:
        data = json.load(f)

    # Create parking lot
    new_lot = ParkingLot(
        name=data.get("name"),
        location=data.get("location"),
        width=data.get("width"),
        height=data.get("height"),
        latitude=data.get("latitude", 0.0),
        longitude=data.get("longitude", 0.0),
    )
    db.add(new_lot)
    db.commit()
    lot_id = new_lot.id

    nodes = []
    id_map = {}

    # Build vertices
    for v in data.get("nodes"):
        vid = v["id"] + node_id_offset

        node_obj = GraphNode(
            id=vid,
            lot_id=lot_id,
            type=v["type"],
            x=float(v["x"]),
            y=float(v["y"]),
            orientation=v.get("orientation"),
            status=v.get("status"),
            label=v.get("label"),
            attrs={
                k: val
                for k, val in v.items()
                if k not in ("id", "x", "y", "type", "status", "label", "orientation")
            },
        )

        nodes.append(node_obj)
        id_map[vid] = node_obj

    # Build edges
    edges = []
    missing_refs = []
    for e in data.get("edges", []):
        from_id = e.get("from_node_id") + node_id_offset
        to_id = e.get("to_node_id") + node_id_offset

        if from_id not in id_map or to_id not in id_map:
            msg_parts = []
            if from_id not in id_map:
                msg_parts.append(f"missing from_node_id={from_id}")
            if to_id not in id_map:
                msg_parts.append(f"missing to_node_id={to_id}")

            msg = f"[Seed] Edge references missing node(s): \
                    {', '.join(msg_parts)}. Edge: {e}"
            print(msg + " — skipping.")
            missing_refs.append(e)

        from_node = id_map[from_id]
        to_node = id_map[to_id]

        # Calculate euclidean length
        default_len = float(
            sqrt((to_node.x - from_node.x) ** 2 + (to_node.y - from_node.y) ** 2)
        )
        length_m = float(e.get("length_m", default_len))
        weight = float(e.get("weight", length_m))

        edge_obj = GraphEdge(
            lot_id=lot_id,
            from_node_id=from_id,
            to_node_id=to_id,
            bidirectional=bool(e.get("bidirectional", True)),
            length_m=length_m,
            weight=weight,
            status=e.get("status", "OPEN"),
            attrs={
                k: v
                for k, v in e.items()
                if k
                not in (
                    "from_node_id",
                    "to_node_id",
                    "bidirectional",
                    "length_m",
                    "weight",
                    "status",
                )
            },
        )
        edges.append(edge_obj)

    node_id_offset += len(nodes)
    db.add_all(nodes + edges)
    db.commit()

    print(f"[Seed] Inserted {len(nodes)} nodes and {len(edges)} edges successfully.")
    if missing_refs:
        print(f"[Seed] Warning: skipped {len(missing_refs)} invalid edges.")


def seed_occupancy_data(db: Session):
    """
    Generate historical occupancy data (one record per occupied spot per hour)
    for the past 60 days.

    Args:
        db (Session): Active SQLAlchemy session
    """
    print("[Seed] Starting occupancy data generation for one year...")

    # Fix seed
    random.seed(42)

    # Start one year ago from now, at the top of the hour.
    end_date = datetime.now().replace(minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=60)

    lots = db.query(ParkingLot).all()
    lot_data = {}
    for lot in lots:
        parking_spots = (
            db.query(GraphNode.id)
            .filter(GraphNode.lot_id == lot.id, GraphNode.type == "PARKING_SPOT")
            .all()
        )
        lot_data[lot.id] = [r[0] for r in parking_spots]

    if not any(lot_data.values()):
        print("[Seed] No parking spots found to seed occupancy data.")
        return

    current_time = start_date
    all_occupancy_records = []

    while current_time < end_date:
        hour = current_time.hour
        # Low occupancy (2am - 6am)
        if 2 <= hour <= 6:
            base_occupancy = 0.15
        # Peak occupancy (9am - 5pm)
        elif 9 <= hour <= 17:
            base_occupancy = 0.70
        # Regular occupancy
        else:
            base_occupancy = 0.40

        # Add 10% randomness
        random_factor = random.uniform(-0.10, 0.10)
        target_occupancy_ratio = max(0, min(1, base_occupancy + random_factor))

        for lot_id, spot_ids in lot_data.items():
            if not spot_ids:
                continue

            num_spots = len(spot_ids)
            num_occupied = int(num_spots * target_occupancy_ratio)

            occupied_spots = random.sample(spot_ids, num_occupied)

            for node_id in occupied_spots:
                occ_obj = Occupancy(
                    lot_id=lot_id,
                    node_id=node_id,
                    timestamp=current_time,
                )
                all_occupancy_records.append(occ_obj)

        current_time += timedelta(hours=1)

    db.add_all(all_occupancy_records)
    db.commit()

    print(
        f"[Seed] Successfully generated and inserted {len(all_occupancy_records)}\
        occupancy records."
    )
