from math import radians, cos, sin, asin, sqrt, hypot
import networkx as nx

EARTH_RADIUS_KM = 6371


def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth using the
    Haversine formula.

    Args:
        lon1: Longitude of the first point (degrees).
        lat1: Latitude of the first point (degrees).
        lon2: Longitude of the second point (degrees).
        lat2: Latitude of the second point (degrees).

    Returns:
        Distance between the two points in kilometres (float).
    """
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return c * EARTH_RADIUS_KM


def heuristic_euclidean(G: nx.DiGraph, u, v) -> float:
    """
    Euclidean distance heuristic for A* algorithm in a graph.

    Args:
        G: The graph containing the nodes.
        u: The starting node ID.
        v: The target node ID.

    Returns:
        The Euclidean distance between nodes u and v.
    """
    ux, uy = G.nodes[u]["x"], G.nodes[u]["y"]
    vx, vy = G.nodes[v]["x"], G.nodes[v]["y"]
    return hypot(vx - ux, vy - uy)
