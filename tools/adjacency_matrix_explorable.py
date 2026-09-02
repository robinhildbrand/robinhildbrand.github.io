#!/usr/bin/env python3
"""Part 2-style adjacency matrix explorable using NumPy + NetworkX."""

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

matplotlib.use("Agg")


def print_degree_comparison(matrix: np.ndarray, graph: nx.DiGraph, title: str) -> None:
    row_sums = matrix.sum(axis=1)
    col_sums = matrix.sum(axis=0)
    out_degree = dict(graph.out_degree(weight="weight"))
    in_degree = dict(graph.in_degree(weight="weight"))

    print(f"\n{title}")
    print("node | row_sum | out_degree | col_sum | in_degree")
    for node in range(matrix.shape[0]):
        print(
            f"{node:>4} | {row_sums[node]:>7.1f} | {out_degree[node]:>10.1f} |"
            f" {col_sums[node]:>7.1f} | {in_degree[node]:>9.1f}"
        )


def draw_graph(graph: nx.Graph, title: str, output_file: Path, directed: bool) -> None:
    pos = nx.spring_layout(graph, seed=7)
    plt.figure(figsize=(8, 6))
    nx.draw_networkx_nodes(graph, pos, node_color="#93c5fd", node_size=900)
    nx.draw_networkx_labels(graph, pos)
    nx.draw_networkx_edges(
        graph,
        pos,
        arrows=directed,
        arrowstyle="-|>" if directed else "-",
        arrowsize=18 if directed else 0,
        width=1.8,
        connectionstyle="arc3,rad=0.08",
    )
    nx.draw_networkx_edge_labels(
        graph,
        pos,
        edge_labels={(u, v): d["weight"] for u, v, d in graph.edges(data=True)},
        font_size=9,
    )
    plt.title(title)
    plt.axis("off")
    plt.tight_layout()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_file, dpi=160)
    plt.close()


def main() -> None:
    # Hand-written directed adjacency matrix (binary)
    A = np.array(
        [
            [0, 1, 1, 0, 0, 0],
            [0, 0, 1, 1, 0, 0],
            [1, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 1, 0],
            [1, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0],
        ],
        dtype=float,
    )

    G_directed = nx.from_numpy_array(A, create_using=nx.DiGraph)
    print_degree_comparison(A, G_directed, "Directed graph: row/column sums vs out/in degree")

    output_dir = Path("/tmp/adjacency_matrix_explorable")
    draw_graph(
        G_directed,
        "Directed graph from A (arrowheads visible)",
        output_dir / "directed_from_A.png",
        directed=True,
    )

    # Symmetrize and clip to 1
    A_sym = np.clip(A + A.T, 0, 1)
    G_undirected = nx.from_numpy_array(A_sym, create_using=nx.Graph)
    draw_graph(
        G_undirected,
        "Undirected graph from clip(A + A^T, 0, 1) (no arrowheads)",
        output_dir / "undirected_from_A_sym.png",
        directed=False,
    )

    # Plant a weighted edge, an isolate, and a self-loop
    A_special = A.copy()
    A_special[0, 2] = 4.0  # weighted edge 0 -> 2
    A_special[5, :] = 0.0  # isolate node 5
    A_special[:, 5] = 0.0
    A_special[3, 3] = 1.0  # self-loop at node 3

    G_special = nx.from_numpy_array(A_special, create_using=nx.DiGraph)
    print_degree_comparison(A_special, G_special, "Special directed graph with weight/isolate/self-loop")
    draw_graph(
        G_special,
        "Directed graph with planted weight/isolate/self-loop",
        output_dir / "directed_special.png",
        directed=True,
    )

    print("\nFeature checks:")
    print(f"Weighted edge 0->2 weight: {G_special[0][2]['weight']}")
    print(f"Isolates: {list(nx.isolates(G_special))}")
    print(f"Self-loops: {list(nx.selfloop_edges(G_special))}")
    print(f"\nSaved plots in: {output_dir}")


if __name__ == "__main__":
    main()
