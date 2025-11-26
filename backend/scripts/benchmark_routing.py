import argparse
import random
import time
from statistics import mean, median
from math import hypot

import networkx as nx
from sqlalchemy.orm import Session

from database import SessionLocal
from database.models.parking import GraphNode, GraphEdge


def load_graph(db: Session, lot_id: int) -> nx.DiGraph:
    """
    Load a directed graph for a specific parking lot from the database.

    Args:
        db: Database session.
        lot_id: The ID of the parking lot.

    Returns:
        nx.DiGraph: A directed graph representing the parking lot.
    """
    G = nx.DiGraph()

    nodes = db.query(GraphNode).filter(GraphNode.lot_id == lot_id).all()
    for n in nodes:
        G.add_node(n.id, x=float(n.x), y=float(n.y))

    edges = (
        db.query(GraphEdge)
        .join(GraphNode, GraphNode.id == GraphEdge.from_node_id)
        .filter(GraphNode.lot_id == lot_id)
        .all()
    )

    for e in edges:
        length = float(getattr(e, "length_m", getattr(e, "length", 1.0)))
        G.add_edge(e.from_node_id, e.to_node_id, weight=length, length=length)

    if G.number_of_nodes() == 0 or G.number_of_edges() == 0:
        raise RuntimeError(f"Lot {lot_id} has empty graph.")
    return G


def heuristic_euclidean(G: nx.DiGraph, u, v) -> float:
    """Calculate the Euclidean distance between two nodes in the graph."""
    ux, uy = G.nodes[u]["x"], G.nodes[u]["y"]
    vx, vy = G.nodes[v]["x"], G.nodes[v]["y"]
    return hypot(vx - ux, vy - uy)


def pick_pairs(G: nx.DiGraph, k: int, seed: int):
    """Pick k random (source, target) node pairs from the graph."""
    rng = random.Random(seed)
    nodes = list(G.nodes())
    pairs = []
    for _ in range(k):
        s, t = rng.sample(nodes, 2)
        pairs.append((s, t))
    return pairs


def run_one(G: nx.DiGraph, s, t, algo: str):
    """Run a single routing algorithm (Dijkstra or A*) on the graph."""
    if algo == "dijkstra":
        t0 = time.perf_counter()
        path = nx.shortest_path(G, source=s, target=t, weight="weight")
        dt = time.perf_counter() - t0
        return dt, path
    elif algo == "astar":
        t0 = time.perf_counter()
        path = nx.astar_path(
            G,
            source=s,
            target=t,
            heuristic=lambda u, v: heuristic_euclidean(G, u, v),
            weight="weight",
        )
        dt = time.perf_counter() - t0
        return dt, path
    else:
        raise ValueError("algo must be 'dijkstra' or 'astar'")


def summarize(times):
    """Summarize a list of timing measurements."""
    if not times:
        return {"n": 0, "mean": None, "median": None, "p95": None, "max": None}
    times_sorted = sorted(times)
    n = len(times_sorted)
    p95 = times_sorted[int(0.95 * (n - 1))]
    return {
        "n": n,
        "mean": mean(times_sorted),
        "median": median(times_sorted),
        "p95": p95,
        "max": times_sorted[-1],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lot-id", type=int, default=1)
    ap.add_argument("--runs", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--warmup", type=int, default=20)
    args = ap.parse_args()

    db = SessionLocal()
    try:
        G = load_graph(db, args.lot_id)
    finally:
        db.close()

    pairs = pick_pairs(G, args.warmup + args.runs, args.seed)

    # Warm-up
    for s, t in pairs[: args.warmup]:
        for algo in ("dijkstra", "astar"):
            try:
                run_one(G, s, t, algo)
            except Exception:
                pass  # ignore warmup failures

    # Timed runs
    d_times, a_times = [], []
    d_fail, a_fail = 0, 0
    for s, t in pairs[args.warmup :]:
        # Dijkstra
        try:
            dt, _ = run_one(G, s, t, "dijkstra")
            d_times.append(dt)
        except Exception:
            d_fail += 1
        # A*
        try:
            dt, _ = run_one(G, s, t, "astar")
            a_times.append(dt)
        except Exception:
            a_fail += 1

    d_stats = summarize(d_times)
    a_stats = summarize(a_times)

    print("\n=== Benchmark Results (seconds) ===")
    print(f"Lot ID: {args.lot_id}, Runs: {args.runs}, Warmup: {args.warmup}")
    print("\nDijkstra:")
    print(d_stats, f"failures={d_fail}")
    print("\nA* (Euclidean heuristic):")
    print(a_stats, f"failures={a_fail}")

    if d_stats["mean"] and a_stats["mean"]:
        speedup = d_stats["mean"] / a_stats["mean"]
        print(
            f"\nRelative speedup (mean): A* is {speedup:.2f}× "
            f"{'faster' if speedup > 1 else 'slower'} than Dijkstra."
        )
    print()


if __name__ == "__main__":
    main()
