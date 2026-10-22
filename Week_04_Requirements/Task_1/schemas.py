"""Pydantic schemas for structured LLM outputs and the shared LangGraph state."""
from __future__ import annotations

from typing import List, Literal, Optional, TypedDict

from pydantic import BaseModel, Field


# ---------------------------------------------------------------- Extractor
class ExtractedReq(BaseModel):
    name: str = Field(description="Short descriptive name of the requirement (max ~8 words).")
    description: str = Field(description="1-3 sentences: what the system shall do / which quality it shall have.")
    evidence: str = Field(description="Short verbatim quote from the document that supports this requirement.")


class ExtractionResult(BaseModel):
    requirements: List[ExtractedReq]


# ------------------------------------------------------------- Consolidator
class GlossaryTerm(BaseModel):
    term: str = Field(description="Canonical term used in all requirements.")
    definition: str
    replaces: List[str] = Field(description="Synonyms found in the inputs that were replaced by this term.")


class ConsolidatedReq(BaseModel):
    key: str = Field(description="Short unique kebab-case slug, e.g. 'shelf-space-utilisation-report'.")
    name: str = Field(description="Short descriptive name (max ~8 words).")
    description: str = Field(description="One paragraph (3-6 sentences) explaining the requirement, using glossary terms.")
    category: str = Field(description="Functional area, e.g. 'Inventory Control', 'Patron Records', 'Reporting Infrastructure'.")
    source_raw_ids: List[str] = Field(description="ALL raw requirement IDs (e.g. 'R012') merged into this requirement.")


class DroppedRaw(BaseModel):
    raw_id: str
    reason: str = Field(description="Why this raw statement is not a software requirement (off-topic, chit-chat, ...).")


class ConsolidationResult(BaseModel):
    requirements: List[ConsolidatedReq]
    dropped: List[DroppedRaw]
    glossary: List[GlossaryTerm]


class Attach(BaseModel):
    raw_id: str
    key: str = Field(description="Key of an EXISTING requirement the raw statement belongs to.")


class Merge(BaseModel):
    keep_key: str
    remove_keys: List[str] = Field(description="Duplicate requirement keys merged into keep_key.")
    new_description: Optional[str] = Field(description="Updated paragraph for keep_key, or null to keep the old one.")


class Edit(BaseModel):
    key: str
    name: str
    description: str


class ConsolidationPatch(BaseModel):
    """Incremental fix of an existing consolidation (used in feedback-loop iterations)."""
    attach: List[Attach]
    new_requirements: List[ConsolidatedReq]
    merges: List[Merge]
    edits: List[Edit]
    dropped: List[DroppedRaw]


# ---------------------------------------------------------- Conflict checker
class ConflictDecision(BaseModel):
    discarded_key: str = Field(description="Key of the requirement that is removed and moved to the blacklist.")
    kind: Literal["conflict", "nonsensical", "infeasible", "out_of_scope"]
    conflicts_with_key: Optional[str] = Field(description="Key of the requirement it conflicts with (kept one), or null.")
    reason: str = Field(description="Explanation why it was discarded and, for conflicts, why the other one was kept.")


class ConflictResult(BaseModel):
    decisions: List[ConflictDecision]


# ---------------------------------------------------------------- Prioritizer
class PriorityAssignment(BaseModel):
    key: str
    priority: Literal["Must", "Should", "Could", "Won't"]
    rationale: str = Field(description="One sentence justifying the priority.")


class PriorityResult(BaseModel):
    assignments: List[PriorityAssignment]


# ------------------------------------------------------------------- Reviewer
class ReviewResult(BaseModel):
    approved: bool = Field(description="True only if the requirement set is complete, non-duplicated and consistent.")
    issues: List[str] = Field(description="Concrete, actionable problems for the consolidator to fix (empty if approved).")


# ---------------------------------------------------------------- Graph state
class State(TypedDict, total=False):
    input_dir: str
    output_dir: str
    max_iterations: int

    documents: list          # [{doc_id, path, text}]
    raw_reqs: list           # [{raw_id, source, name, description, evidence}]
    consolidated: list       # [ConsolidatedReq as dict]
    dropped: list            # [DroppedRaw as dict]
    glossary: list           # [GlossaryTerm as dict]
    coverage: dict           # deterministic coverage report
    blacklist: list          # [ConflictDecision as dict]
    priorities: dict         # key -> {priority, rationale}
    review: dict             # ReviewResult as dict
    feedback: list           # reviewer issues fed back into the consolidator
    iteration: int
    output_file: str