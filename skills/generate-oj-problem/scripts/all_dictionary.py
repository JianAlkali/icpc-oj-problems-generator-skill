#!/usr/bin/env python3
"""Deterministic dictionaries for exhaustive small OJ generator modes."""

from __future__ import annotations

import argparse
import itertools
import json


def prufer_to_tree(seq: tuple[int, ...]) -> list[tuple[int, int]]:
    n = len(seq) + 2
    degree = [1] * (n + 1)
    for x in seq:
        degree[x] += 1
    edges = []
    for x in seq:
        leaf = next(i for i in range(1, n + 1) if degree[i] == 1)
        edges.append((leaf, x))
        degree[leaf] -= 1
        degree[x] -= 1
    leaves = [i for i in range(1, n + 1) if degree[i] == 1]
    edges.append((leaves[0], leaves[1]))
    return edges


def labeled_tree_by_id(n: int, one_based_id: int) -> list[tuple[int, int]]:
    if n == 1:
        if one_based_id != 1:
            raise ValueError("n=1 has exactly one tree")
        return []
    total = n ** (n - 2)
    if not 1 <= one_based_id <= total:
        raise ValueError(f"tree id out of range: 1..{total}")
    x = one_based_id - 1
    seq = []
    for _ in range(n - 2):
        seq.append(x % n + 1)
        x //= n
    return prufer_to_tree(tuple(reversed(seq)))


def graph_edges_by_id(n: int, one_based_id: int, directed: bool) -> list[tuple[int, int]]:
    pairs = []
    if directed:
        pairs = [(i, j) for i in range(1, n + 1) for j in range(1, n + 1) if i != j]
    else:
        pairs = [(i, j) for i in range(1, n + 1) for j in range(i + 1, n + 1)]
    total = 1 << len(pairs)
    if not 1 <= one_based_id <= total:
        raise ValueError(f"graph id out of range: 1..{total}")
    mask = one_based_id - 1
    return [edge for bit, edge in enumerate(pairs) if (mask >> bit) & 1]


def permutation_by_id(n: int, one_based_id: int) -> list[int]:
    perms = itertools.permutations(range(1, n + 1))
    for idx, perm in enumerate(perms, start=1):
        if idx == one_based_id:
            return list(perm)
    raise ValueError("permutation id out of range")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["tree", "graph", "digraph", "perm"])
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--ids", nargs="+", type=int, required=True)
    args = ap.parse_args()

    out = []
    for item_id in args.ids:
        if args.kind == "tree":
            obj = {"id": item_id, "n": args.n, "edges": labeled_tree_by_id(args.n, item_id)}
        elif args.kind == "graph":
            obj = {"id": item_id, "n": args.n, "edges": graph_edges_by_id(args.n, item_id, False)}
        elif args.kind == "digraph":
            obj = {"id": item_id, "n": args.n, "edges": graph_edges_by_id(args.n, item_id, True)}
        else:
            obj = {"id": item_id, "n": args.n, "permutation": permutation_by_id(args.n, item_id)}
        out.append(obj)
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
