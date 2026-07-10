from backend.app.services.retrieval_ranking_service import (
    RankedCandidate,
    coerce_vector_to_float_list,
    select_mmr_candidates,
)


def _candidate(
    name: str,
    embedding: list[float],
    similarity_score: float,
) -> RankedCandidate:
    return RankedCandidate(
        item=name,
        embedding=embedding,
        distance=1.0 - similarity_score,
        similarity_score=similarity_score,
    )


def test_coerce_vector_to_float_list() -> None:
    result = coerce_vector_to_float_list((1, 2.5, 3))

    assert result == [1.0, 2.5, 3.0]


def test_mmr_returns_empty_list_for_empty_candidates() -> None:
    result = select_mmr_candidates(
        candidates=[],
        query_embedding=[1.0, 0.0],
        top_k=3,
        lambda_mult=0.65,
    )

    assert result == []


def test_mmr_selects_relevant_and_diverse_candidates() -> None:
    candidates = [
        _candidate("most-relevant", [1.0, 0.0], 1.0),
        _candidate("near-duplicate", [0.99, 0.01], 0.99),
        _candidate("diverse", [0.0, 1.0], 0.50),
    ]

    result = select_mmr_candidates(
        candidates=candidates,
        query_embedding=[1.0, 0.0],
        top_k=2,
        lambda_mult=0.30,
    )

    selected_names = [candidate.item for candidate in result]

    assert selected_names == ["most-relevant", "diverse"]


def test_mmr_respects_top_k() -> None:
    candidates = [
        _candidate("one", [1.0, 0.0], 1.0),
        _candidate("two", [0.8, 0.2], 0.8),
        _candidate("three", [0.0, 1.0], 0.4),
    ]

    result = select_mmr_candidates(
        candidates=candidates,
        query_embedding=[1.0, 0.0],
        top_k=1,
        lambda_mult=0.65,
    )

    assert len(result) == 1
    assert result[0].item == "one"
