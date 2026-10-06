from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, asdict
from typing import Any, Iterable

GRAPH_SCHEMA_VERSION = "corpus-graph.v1"

ENTITY_KINDS = {
    "problemset",
    "asset",
    "section",
    "task",
    "subtask",
    "answer",
    "criterion",
    "media",
}


ROLE_PREFIX_RE = re.compile(r"^(tasks?|ans(?:wers?)?|criteria|script|solutions?|audio)[-_]", re.I)


def stable_id(kind: str, *parts: str) -> str:
    material = "|".join(str(p).strip().lower() for p in parts)
    return f"{kind}_{hashlib.sha1(material.encode('utf-8')).hexdigest()[:20]}"


def entity_id(kind: str, parent_id: str, source_anchor: str, semantic_key: str = "") -> str:
    """Stable ID for canonical corpus entities, independent from parser version."""
    if kind not in ENTITY_KINDS:
        raise ValueError(f"unsupported_entity_kind:{kind}")
    return stable_id(kind, parent_id, source_anchor, semantic_key)


@dataclass(frozen=True)
class GraphNode:
    kind: str
    parent_id: str
    source_anchor: str
    semantic_key: str = ""
    provenance: dict[str, Any] | None = None

    @property
    def id(self) -> str:
        return entity_id(self.kind, self.parent_id, self.source_anchor, self.semantic_key)


@dataclass
class GraphEdge:
    source_id: str
    target_id: str
    edge_type: str
    confidence: float
    provenance: dict[str, Any]
    human_decision: str = "UNREVIEWED"

    @property
    def id(self) -> str:
        return stable_id("edge", self.source_id, self.target_id, self.edge_type)


def canonical_bundle_key(filename: str) -> str:
    stem = filename.rsplit("/", 1)[-1].rsplit(".", 1)[0].lower()
    stem = ROLE_PREFIX_RE.sub("", stem)
    stem = re.sub(r"[^a-z0-9а-яё]+", "-", stem, flags=re.I)
    return stem.strip("-")


@dataclass(frozen=True)
class Asset:
    sha256: str
    filename: str
    role: str
    subject: str = ""
    academic_year: str = ""
    stage: str = ""
    grades: str = ""
    region: str = ""
    tour: str = ""
    source_url: str = ""

    @property
    def id(self) -> str:
        return stable_id("asset", self.sha256)


@dataclass
class EdgeProposal:
    id: str
    problemset_id: str
    asset_id: str
    edge_type: str
    confidence: float
    provenance: dict[str, Any]
    human_decision: str = "UNREVIEWED"


def problemset_id_for(asset: Asset) -> str:
    key = canonical_bundle_key(asset.filename)
    return stable_id(
        "problemset",
        asset.subject,
        asset.academic_year,
        asset.stage,
        asset.grades,
        asset.region,
        asset.tour,
        key,
    )


def bundle_similarity(a: Asset, b: Asset) -> tuple[float, dict[str, Any]]:
    checks: list[tuple[str, float, bool]] = [
        ("bundle_key", 0.35, canonical_bundle_key(a.filename) == canonical_bundle_key(b.filename)),
        ("subject", 0.10, bool(a.subject and b.subject and a.subject == b.subject)),
        ("academic_year", 0.12, bool(a.academic_year and b.academic_year and a.academic_year == b.academic_year)),
        ("stage", 0.10, bool(a.stage and b.stage and a.stage == b.stage)),
        ("grades", 0.08, bool(a.grades and b.grades and a.grades == b.grades)),
        ("region", 0.12, bool(a.region and b.region and a.region == b.region)),
        ("tour", 0.08, bool(a.tour and b.tour and a.tour == b.tour)),
    ]
    score = sum(weight for _, weight, ok in checks if ok)
    complementary = a.role != b.role and a.role and b.role
    if complementary:
        score += 0.05
    return min(score, 1.0), {
        "signals": {name: ok for name, _, ok in checks},
        "complementary_roles": bool(complementary),
        "algorithm": "bundle_similarity.v1",
    }


def propose_problemsets(assets: Iterable[Asset], threshold: float = 0.70) -> dict[str, Any]:
    assets = list(assets)
    groups: dict[str, list[Asset]] = {}

    # Seed deterministic groups from canonical metadata/filename.
    for asset in assets:
        groups.setdefault(problemset_id_for(asset), []).append(asset)

    # Pairwise merge suggestions are retained as reviewable provenance.
    proposals: list[EdgeProposal] = []
    for i, a in enumerate(assets):
        for b in assets[i + 1 :]:
            score, provenance = bundle_similarity(a, b)
            if score < threshold:
                continue
            pid = problemset_id_for(a)
            for asset in (a, b):
                proposals.append(
                    EdgeProposal(
                        id=stable_id("edge", pid, asset.id, "contains"),
                        problemset_id=pid,
                        asset_id=asset.id,
                        edge_type="contains",
                        confidence=round(score, 3),
                        provenance={**provenance, "paired_with": b.id if asset is a else a.id},
                    )
                )

    problemsets = []
    for pid, members in groups.items():
        problemsets.append(
            {
                "id": pid,
                "assets": [asdict(a) | {"id": a.id} for a in members],
                "stable_key": canonical_bundle_key(members[0].filename),
            }
        )

    return {
        "schema_version": GRAPH_SCHEMA_VERSION,
        "problemsets": problemsets,
        "edge_proposals": [asdict(p) for p in proposals],
    }
