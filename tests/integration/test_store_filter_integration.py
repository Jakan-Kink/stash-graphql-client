"""Integration tests for store Django-style filter lookups against real Stash.

Verifies inclusive bound semantics (__gte/__lte) end-to-end: Stash has no
>= / <= criterion modifier, so the store expresses them as NOT(strict
comparison) — these tests prove the boundary value is included, strict
lookups stay exclusive, and NULL-valued fields are excluded.
"""

import uuid

import pytest

from stash_graphql_client import StashClient, StashEntityStore
from stash_graphql_client.types import Performer
from tests.fixtures import capture_graphql_calls, dump_graphql_calls


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xdist_group(name="performer_mutations")
async def test_find_inclusive_bounds_round_trip(
    stash_client: StashClient,
    live_entity_store: StashEntityStore,
    stash_cleanup_tracker,
) -> None:
    """Test __gte/__lte include the boundary while __gt stays strict."""
    store = live_entity_store
    prefix = f"SGC Inttest Bounds {uuid.uuid4()}"

    async with (
        stash_cleanup_tracker(stash_client, auto_capture=False) as cleanup,
        capture_graphql_calls(stash_client) as calls,
    ):
        try:
            for rating in (40, 50, 60):
                performer = await stash_client.create_performer(
                    Performer(name=f"{prefix} r{rating}", rating100=rating)
                )
                cleanup["performers"].append(performer.id)
            unrated = await stash_client.create_performer(
                Performer(name=f"{prefix} unrated")
            )
            cleanup["performers"].append(unrated.id)
        finally:
            dump_graphql_calls(calls, "create rated performers")

        assert len(calls) == 4, "Expected 4 performerCreate calls"
        assert all("performerCreate" in c["query"] for c in calls)
        assert all(c["exception"] is None for c in calls)

        calls.clear()

        try:
            gte_results = await store.find(
                Performer, name__contains=prefix, rating100__gte=50
            )
        finally:
            dump_graphql_calls(calls, "find rating100__gte=50")

        # Request must carry the NOT-wrapped strict comparison
        assert all("findPerformers" in c["query"] for c in calls)
        assert all(
            c["variables"]["performer_filter"]["NOT"]
            == {"rating100": {"value": 50, "modifier": "LESS_THAN"}}
            for c in calls
        )

        # Boundary (50) included, below-boundary (40) and unrated excluded
        # (assert on names: rating100 is not in the base fragment)
        assert {p.name for p in gte_results} == {f"{prefix} r50", f"{prefix} r60"}

        calls.clear()

        try:
            lte_results = await store.find(
                Performer, name__contains=prefix, rating100__lte=50
            )
        finally:
            dump_graphql_calls(calls, "find rating100__lte=50")

        assert {p.name for p in lte_results} == {f"{prefix} r40", f"{prefix} r50"}

        calls.clear()

        try:
            range_results = await store.find(
                Performer,
                name__contains=prefix,
                rating100__gte=50,
                rating100__lte=50,
            )
        finally:
            dump_graphql_calls(calls, "find gte=50 lte=50 range")

        # De Morgan OR-chain inside one NOT: both bounds honored
        assert all(
            c["variables"]["performer_filter"]["NOT"]
            == {
                "rating100": {"value": 50, "modifier": "LESS_THAN"},
                "OR": {"rating100": {"value": 50, "modifier": "GREATER_THAN"}},
            }
            for c in calls
        )
        assert [p.name for p in range_results] == [f"{prefix} r50"]

        calls.clear()

        try:
            gt_results = await store.find(
                Performer, name__contains=prefix, rating100__gt=50
            )
        finally:
            dump_graphql_calls(calls, "find rating100__gt=50")

        # Strict > excludes the boundary
        assert [p.name for p in gt_results] == [f"{prefix} r60"]

        calls.clear()

        try:
            null_results = await store.find(
                Performer, name__contains=prefix, rating100__null=True
            )
        finally:
            dump_graphql_calls(calls, "find rating100__null=True")

        # IS_NULL on an Int-criterion field needs an int placeholder to pass
        # gqlgen validation; only the unrated performer matches
        assert all(
            c["variables"]["performer_filter"]["rating100"]
            == {"value": 0, "modifier": "IS_NULL"}
            for c in calls
        )
        assert [p.name for p in null_results] == [f"{prefix} unrated"]
