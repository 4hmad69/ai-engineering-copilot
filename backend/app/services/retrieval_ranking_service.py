from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RankedCandidate:
    item: Any
    embedding: list[float]
    distance: float
    similarity_score: float


def coerce_vector_to_float_list(vector: Any) -> list[float]:
    if vector is None:
        return []

    if hasattr(vector, "tolist"):
        vector = vector.tolist()

    return [float(value) for value in vector]


def dot_product(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        return 0.0

    return sum(left_value * right_value for left_value, right_value in zip(left, right, strict=True))


def select_mmr_candidates(
    candidates: list[RankedCandidate],
    query_embedding: list[float],
    top_k: int,
    lambda_mult: float,
) -> list[RankedCandidate]:
    if not candidates:
        return []

    if top_k <= 0:
        return []

    if len(candidates) <= top_k:
        return candidates

    lambda_mult = min(max(lambda_mult, 0.0), 1.0)

    remaining = sorted(
        candidates,
        key=lambda candidate: candidate.similarity_score,
        reverse=True,
    )

    selected: list[RankedCandidate] = []

    first_candidate = remaining.pop(0)
    selected.append(first_candidate)

    while remaining and len(selected) < top_k:
        best_candidate: RankedCandidate | None = None
        best_score = float("-inf")

        for candidate in remaining:
            relevance_score = dot_product(candidate.embedding, query_embedding)

            diversity_penalty = max(
                dot_product(candidate.embedding, selected_candidate.embedding)
                for selected_candidate in selected
            )

            mmr_score = (lambda_mult * relevance_score) - (
                (1.0 - lambda_mult) * diversity_penalty
            )

            if mmr_score > best_score:
                best_score = mmr_score
                best_candidate = candidate

        if best_candidate is None:
            break

        selected.append(best_candidate)
        remaining.remove(best_candidate)

    return selected