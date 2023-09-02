""" SAX Additive Backend """

from typing import Any, Dict, Tuple

import networkx as nx
from ..typing_ import SDict, SType, sdict

try:
    import jax.numpy as jnp

    JAX_AVAILABLE = True
except ImportError:
    import numpy as jnp

    JAX_AVAILABLE = False


def split_port(port: str) -> Tuple[str, str]:
    try:
        instance, port = port.split(",")
    except ValueError:
        (port,) = port.split(",")
        instance = ""
    return instance, port


def graph_edges(
    instances: Dict[str, SType], connections: Dict[str, str], ports: Dict[str, str]
):
    zero = jnp.array([0.0], dtype=float)
    edges = {}
    edges.update({split_port(k): split_port(v) for k, v in connections.items()})
    edges.update({split_port(v): split_port(k) for k, v in connections.items()})
    edges.update({split_port(k): split_port(v) for k, v in ports.items()})
    edges.update({split_port(v): split_port(k) for k, v in ports.items()})
    edges = [(n1, n2, {"type": "C", "length": zero}) for n1, n2 in edges.items()]

    _instances = {
        **{i1: None for (i1, _), (_, _), _ in edges},
        **{i2: None for (_, _), (i2, _), _ in edges},
    }
    del _instances[""]  # external ports don't belong to an instance

    for instance in _instances:
        s = instances[instance]
        edges += [
            (
                (instance, p1),
                (instance, p2),
                {"type": "S", "length": jnp.asarray(length, dtype=float).ravel()},
            )
            for (p1, p2), length in sdict(s).items()
        ]

    return edges


def prune_internal_output_nodes(graph):
    broken = True
    while broken:
        broken = False
        for (i, p), dic in list(graph.adjacency()):
            if (
                i != ""
                and len(dic) == 2
                and all(prop.get("type", "C") == "C" for prop in dic.values())
            ):
                graph.remove_node((i, p))
                graph.add_edge(*dic.keys(), type="C", length=0.0)
                broken = True
                break
    return graph


def get_possible_paths(graph, source, target):
    paths = []
    default_props = {"type": "C", "length": 0.0}
    for path in nx.all_simple_edge_paths(graph, source, target):
        prevtype = "C"
        for n1, n2 in path:
            curtype = graph.get_edge_data(n1, n2, default_props)["type"]
            if curtype == prevtype == "S":
                break
            else:
                prevtype = curtype
        else:
            paths.append(path)
    return paths


def path_lengths(graph, paths):
    lengths = []
    for path in paths:
        length = zero = jnp.array([0.0], dtype=float)
        default_edge_data = {"type": "C", "length": zero}
        for edge in path:
            edge_data = graph.get_edge_data(*edge, default_edge_data)
            length = (length[None, :] + edge_data.get("length", zero)[:, None]).ravel()
        lengths.append(length)
    return lengths


def analyze_circuit_additive(
    connections: Dict[str, str],
    ports: Dict[str, str],
) -> Any:
    return connections, ports


def evaluate_circuit_additive(
    analyzed: Any,
    instances: Dict[str, SDict],
) -> SDict:
    """evaluate a circuit for the given sdicts."""
    connections, ports = analyzed
    edges = graph_edges(instances, connections, ports)

    graph = nx.Graph()
    graph.add_edges_from(edges)
    prune_internal_output_nodes(graph)

    sdict = {}
    for source in ports:
        for target in ports:
            paths = get_possible_paths(graph, source=("", source), target=("", target))
            if not paths:
                continue
            sdict[source, target] = path_lengths(graph, paths)

    return sdict
