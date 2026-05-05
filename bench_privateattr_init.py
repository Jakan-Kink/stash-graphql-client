"""Measure tracemalloc peak/retained bytes for entity construction at scale."""

from __future__ import annotations

import gc
import time
import tracemalloc

from stash_graphql_client.types.scene import Scene
from stash_graphql_client.types.tag import Tag


def measure(label: str, fn, n: int) -> None:
    """Run fn() n times, report peak + retained allocations."""
    # Warm up: import-time / class-init allocations should not be charged
    fn(0)
    gc.collect()

    tracemalloc.start()
    gc.collect()
    base_current, _ = tracemalloc.get_traced_memory()

    t0 = time.perf_counter()
    fn(n)
    t1 = time.perf_counter()

    _current, peak = tracemalloc.get_traced_memory()
    gc.collect()
    after_gc, _ = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_delta = peak - base_current
    retained = after_gc - base_current
    print(
        f"{label:50} n={n:>7,}  "
        f"peak={peak_delta / 2**20:>8.2f} MB  "
        f"retained={retained / 2**20:>7.2f} MB  "
        f"per-inst-peak={peak_delta / max(n, 1):>7,.0f} B  "
        f"per-inst-retained={retained / max(n, 1):>5,.0f} B  "
        f"time={(t1 - t0):>5.2f} s"
    )


def make_tag_dicts(n: int) -> list[dict]:
    return [
        {
            "__typename": "Tag",
            "id": str(i),
            "name": f"tag-{i}",
            "description": f"Description for tag {i}",
        }
        for i in range(1, n + 1)
    ]


def make_scene_dicts(n: int) -> list[dict]:
    return [
        {
            "__typename": "Scene",
            "id": str(i),
            "title": f"scene-{i}",
            "code": f"CODE-{i:05d}",
            "details": "Lorem ipsum " * 10,
            "organized": False,
            "rating100": 80,
            "play_count": 0,
            "o_counter": 0,
        }
        for i in range(1, n + 1)
    ]


def bench_tag_from_graphql(n: int) -> None:
    """Production path: from_graphql → _process_nested_graphql → model_validate."""
    payloads = make_tag_dicts(n)
    # Hold references so identity-map cache + entities stay alive during measurement
    return [Tag.from_graphql(p) for p in payloads]


def bench_tag_model_validate(n: int) -> None:
    """Direct model_validate path (no from_graphql preprocessing)."""
    payloads = make_tag_dicts(n)
    return [Tag.model_validate(p) for p in payloads]


def bench_scene_from_graphql(n: int) -> None:
    payloads = make_scene_dicts(n)
    return [Scene.from_graphql(p) for p in payloads]


def main() -> None:
    print("Benchmarking PrivateAttr-init allocation overhead")
    print("=" * 100)
    print(
        "  peak              = tracemalloc peak during construction "
        "(net of pre-loop baseline)"
    )
    print(
        "  retained          = tracemalloc current after gc.collect() "
        "(net of baseline; should be live entities + cache)"
    )
    print(
        "  per-inst-peak     = peak / n  -- includes throwaway allocations from "
        "signature inspection"
    )
    print("  per-inst-retained = retained / n  -- size of live entity + cache entry")
    print()

    sizes = [1_000, 10_000, 50_000]
    for n in sizes:
        measure("Tag.from_graphql (production path)", bench_tag_from_graphql, n)
    print()
    for n in sizes:
        measure("Tag.model_validate", bench_tag_model_validate, n)
    print()
    for n in sizes[:2]:
        measure("Scene.from_graphql", bench_scene_from_graphql, n)


if __name__ == "__main__":
    main()
