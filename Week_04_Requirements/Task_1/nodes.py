"""Nodes of the requirements-refinement network.

LLM nodes:            extract_requirements, consolidate, detect_conflicts, prioritize, review
Deterministic nodes:  load_corpus, trace_and_coverage, format_document
"""
from __future__ import annotations

import json
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

from langchain_openai import ChatOpenAI

import prompts
from schemas import (
    ConflictResult,
    ConsolidationPatch,
    ConsolidationResult,
    ExtractionResult,
    PriorityResult,
    ReviewResult,
    State,
)

# ------------------------------------------------------------------ models
# Different models for different jobs (ANS4). Can be overridden via env vars.
MODELS = {
    "extractor": os.getenv("MODEL_EXTRACTOR", "gpt-4o-mini"),      # cheap + fast, runs once per document
    "consolidator": os.getenv("MODEL_CONSOLIDATOR", "gpt-5-mini"),  # long context, careful merging
    "conflicts": os.getenv("MODEL_CONFLICTS", "gpt-6-luna"),        # strongest reasoning for contradictions
    "prioritizer": os.getenv("MODEL_PRIORITIZER", "gpt-5.4-nano"),  # simple classification task
    "reviewer": os.getenv("MODEL_REVIEWER", "gpt-6-luna"),          # quality gate
}

TEXT_EXTENSIONS = {".txt", ".eml", ".md", ".csv", ".json", ".html", ".htm", ".xml", ".log", ""}
CHUNK_CHARS = 40_000  # documents longer than this are split for the extractor


def make_llm(role: str) -> ChatOpenAI:
    model = MODELS[role]
    kwargs = dict(model=model, timeout=900, max_retries=3)
    if model.startswith(("gpt-4o", "gpt-4.1")):
        kwargs["temperature"] = 0  # reasoning models (gpt-5+) do not accept temperature
    return ChatOpenAI(**kwargs)


def structured(role: str, schema):
    return make_llm(role).with_structured_output(schema)


def log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def dump(state: State, name: str, data) -> None:
    """Save intermediate results for debugging / the report."""
    d = Path(state["output_dir"]) / "intermediate"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{name}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ======================================================= 1. load_corpus (deterministic)
def load_corpus(state: State) -> State:
    root = Path(state["input_dir"])
    if not root.is_dir():
        raise SystemExit(f"Input directory not found: {root}")
    docs = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if path.suffix.lower() not in TEXT_EXTENSIONS or path.name.startswith("."):
            continue
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        if not text:
            continue
        docs.append({"doc_id": f"D{len(docs) + 1:02d}", "path": path.relative_to(root).as_posix(), "text": text})
    if not docs:
        raise SystemExit(f"No text documents found in {root}")
    log(f"load_corpus: {len(docs)} documents loaded from {root}")
    dump(state, "01_documents", [{k: d[k] for k in ("doc_id", "path")} | {"chars": len(d["text"])} for d in docs])
    return {"documents": docs, "iteration": 0, "feedback": []}


def _chunks(text: str, size: int = CHUNK_CHARS):
    if len(text) <= size:
        return [text]
    parts, cur = [], ""
    for para in re.split(r"\n\s*\n", text):
        if len(cur) + len(para) > size and cur:
            parts.append(cur)
            cur = ""
        cur += para + "\n\n"
    if cur.strip():
        parts.append(cur)
    return parts


# ================================================= 2. extract_requirements (LLM)
def extract_requirements(state: State) -> State:
    llm = structured("extractor", ExtractionResult)
    jobs, origins = [], []
    for d in state["documents"]:
        chunks = _chunks(d["text"])
        for i, chunk in enumerate(chunks):
            part = f" (part {i + 1}/{len(chunks)})" if len(chunks) > 1 else ""
            jobs.append([("system", prompts.EXTRACTOR),
                         ("human", f"Document: {d['path']}{part}\n\n{chunk}")])
            origins.append(d["path"])
    log(f"extract_requirements [{MODELS['extractor']}]: {len(jobs)} calls in parallel ...")
    results = llm.batch(jobs, config={"max_concurrency": 8})

    raw = []
    for source, res in zip(origins, results):
        for r in res.requirements:
            raw.append({"raw_id": f"R{len(raw) + 1:03d}", "source": source,
                        "name": r.name, "description": r.description, "evidence": r.evidence})
    log(f"extract_requirements: {len(raw)} raw requirements")
    dump(state, "02_raw_requirements", raw)
    return {"raw_reqs": raw}


# ======================================================== 3. consolidate (LLM)
def consolidate(state: State) -> State:
    it = state.get("iteration", 0) + 1
    raw_lines = "\n".join(
        f"{r['raw_id']} [{r['source']}] {r['name']}: {r['description']}" for r in state["raw_reqs"])
    msg = f"RAW REQUIREMENTS ({len(state['raw_reqs'])}):\n{raw_lines}"
    if state.get("feedback"):
        return _consolidate_patch(state, it, msg)
    log(f"consolidate [{MODELS['consolidator']}] iteration {it} ...")
    res = structured("consolidator", ConsolidationResult).invoke(
        [("system", prompts.CONSOLIDATOR), ("human", msg)])
    data = res.model_dump()
    log(f"consolidate: {len(data['requirements'])} requirements, {len(data['dropped'])} dropped as noise")
    dump(state, f"03_consolidated_iter{it}", data)
    return {"consolidated": data["requirements"], "dropped": data["dropped"],
            "glossary": data["glossary"], "iteration": it}


def _consolidate_patch(state: State, it: int, raw_msg: str) -> State:
    """Feedback iteration: the LLM returns only changes, which are applied deterministically.
    This keeps already-good requirements stable instead of regenerating (and losing) them."""
    reqs = {r["key"]: dict(r) for r in state["consolidated"]}
    bl = {b["discarded_key"] for b in state.get("blacklist", [])}
    cur = "\n".join(f"- key={r['key']} | {r['category']} | {r['name']} (raw: {', '.join(r['source_raw_ids'])})"
                    f"{' [BLACKLISTED]' if k in bl else ''}\n  {r['description']}" for k, r in reqs.items())
    uncovered = ", ".join(state["coverage"]["uncovered"]) or "(none)"
    glossary = "; ".join(f"{g['term']} (not: {', '.join(g['replaces'])})" for g in state.get("glossary", []))
    msg = (f"{raw_msg}\n\nCURRENT REQUIREMENTS ({len(reqs)}):\n{cur}\n\nGLOSSARY: {glossary}\n\n"
           f"UNCOVERED RAW IDS: {uncovered}\n\nREVIEWER FEEDBACK - fix all of these:\n- "
           + "\n- ".join(state["feedback"]))
    log(f"consolidate [{MODELS['consolidator']}] iteration {it} (patch mode) ...")
    p = structured("consolidator", ConsolidationPatch).invoke(
        [("system", prompts.CONSOLIDATOR_PATCH), ("human", msg)])

    for a in p.attach:
        if a.key in reqs and a.raw_id not in reqs[a.key]["source_raw_ids"]:
            reqs[a.key]["source_raw_ids"].append(a.raw_id)
    for m in p.merges:
        if m.keep_key not in reqs:
            continue
        for k in m.remove_keys:
            if k in reqs and k != m.keep_key:
                reqs[m.keep_key]["source_raw_ids"] += reqs.pop(k)["source_raw_ids"]
        if m.new_description:
            reqs[m.keep_key]["description"] = m.new_description
    for e in p.edits:
        if e.key in reqs:
            reqs[e.key].update(name=e.name, description=e.description)
    for n in p.new_requirements:
        reqs.setdefault(n.key, n.model_dump())
    dropped = state.get("dropped", []) + [d.model_dump() for d in p.dropped]

    data = p.model_dump()
    log(f"consolidate patch: +{len(p.attach)} attached, +{len(p.new_requirements)} new, "
        f"{len(p.merges)} merges, {len(p.edits)} edits, +{len(p.dropped)} dropped")
    dump(state, f"03_patch_iter{it}", data)
    return {"consolidated": list(reqs.values()), "dropped": dropped, "iteration": it}


# ============================================ 4. trace_and_coverage (deterministic)
def trace_and_coverage(state: State) -> State:
    """Validates the LLM output and computes traceability + coverage without any AI."""
    raw_ids = {r["raw_id"] for r in state["raw_reqs"]}
    reqs, seen_keys = [], Counter()
    hallucinated, used = set(), Counter()
    for r in state["consolidated"]:
        r = dict(r)
        key = re.sub(r"[^a-z0-9]+", "-", r["key"].lower()).strip("-") or "req"
        seen_keys[key] += 1
        r["key"] = key if seen_keys[key] == 1 else f"{key}-{seen_keys[key]}"  # unique keys
        valid = [x for x in r["source_raw_ids"] if x in raw_ids]
        hallucinated |= set(r["source_raw_ids"]) - raw_ids
        r["source_raw_ids"] = sorted(set(valid))
        used.update(r["source_raw_ids"])
        reqs.append(r)

    dropped, dropped_ids = [], set()  # a raw ID that is used by a requirement cannot also be dropped
    for d in state.get("dropped", []):
        if d["raw_id"] in raw_ids and d["raw_id"] not in used and d["raw_id"] not in dropped_ids:
            dropped_ids.add(d["raw_id"])
            dropped.append(d)
    uncovered = sorted(raw_ids - set(used) - dropped_ids)
    multi = sorted(x for x, n in used.items() if n > 1)
    no_source = [r["key"] for r in reqs if not r["source_raw_ids"]]
    coverage = {
        "raw_total": len(raw_ids),
        "covered": len(set(used)),
        "dropped_as_noise": len(dropped_ids),
        "uncovered": uncovered,
        "raw_ids_in_multiple_requirements": multi,
        "requirements_without_valid_source": no_source,
        "hallucinated_raw_ids_removed": sorted(hallucinated),
    }
    log(f"trace_and_coverage: {coverage['covered']}/{len(raw_ids)} covered, "
        f"{len(dropped_ids)} noise, {len(uncovered)} uncovered")
    dump(state, f"04_coverage_iter{state['iteration']}", coverage)
    return {"consolidated": reqs, "coverage": coverage, "dropped": dropped}


# ===================================================== 5. detect_conflicts (LLM)
def _req_lines(reqs, raw_by_id, with_raw=False):
    out = []
    for r in reqs:
        srcs = sorted({raw_by_id[x]["source"] for x in r["source_raw_ids"]})
        out.append(f"- key={r['key']} | {r['name']} | sources={len(srcs)} ({', '.join(srcs)})\n  {r['description']}")
        if with_raw:
            out += [f"    > {x} [{raw_by_id[x]['source']}]: {raw_by_id[x]['description']}" for x in r["source_raw_ids"]]
    return "\n".join(out)


def detect_conflicts(state: State) -> State:
    raw_by_id = {r["raw_id"]: r for r in state["raw_reqs"]}
    log(f"detect_conflicts [{MODELS['conflicts']}] ...")
    res = structured("conflicts", ConflictResult).invoke(
        [("system", prompts.CONFLICT_CHECKER),
         ("human", "REQUIREMENTS (with their raw source statements):\n"
          + _req_lines(state["consolidated"], raw_by_id, with_raw=True))])
    keys = {r["key"] for r in state["consolidated"]}
    blacklist, seen = [], set()
    for d in res.decisions:
        if d.discarded_key in keys and d.discarded_key not in seen:
            seen.add(d.discarded_key)
            blacklist.append(d.model_dump())
    log(f"detect_conflicts: {len(blacklist)} requirements blacklisted")
    dump(state, f"05_blacklist_iter{state['iteration']}", blacklist)
    return {"blacklist": blacklist}


def _active(state: State):
    bl = {b["discarded_key"] for b in state.get("blacklist", [])}
    return [r for r in state["consolidated"] if r["key"] not in bl]


# ========================================================= 6. prioritize (LLM)
def prioritize(state: State) -> State:
    raw_by_id = {r["raw_id"]: r for r in state["raw_reqs"]}
    active = _active(state)
    log(f"prioritize [{MODELS['prioritizer']}]: {len(active)} requirements ...")
    res = structured("prioritizer", PriorityResult).invoke(
        [("system", prompts.PRIORITIZER), ("human", "REQUIREMENTS:\n" + _req_lines(active, raw_by_id))])
    pr = {a.key: {"priority": a.priority, "rationale": a.rationale} for a in res.assignments}
    for r in active:  # deterministic fallback if the model skipped something
        pr.setdefault(r["key"], {"priority": "Should", "rationale": "Default priority (not assigned by the model)."})
    dump(state, f"06_priorities_iter{state['iteration']}", pr)
    return {"priorities": pr}


# ============================================================= 7. review (LLM)
def review(state: State) -> State:
    raw_by_id = {r["raw_id"]: r for r in state["raw_reqs"]}
    active = _active(state)
    cov = state["coverage"]
    lines = []
    for r in active:
        p = state["priorities"].get(r["key"], {}).get("priority", "?")
        lines.append(f"- key={r['key']} [{p}] {r['name']} (raw: {', '.join(r['source_raw_ids'])})\n  {r['description']}")
    uncovered = "\n".join(f"{x} [{raw_by_id[x]['source']}] {raw_by_id[x]['name']}: {raw_by_id[x]['description']}"
                          for x in cov["uncovered"]) or "(none)"
    bl = "\n".join(f"- {b['discarded_key']} ({b['kind']}): {b['reason']}" for b in state["blacklist"]) or "(none)"
    msg = (f"REQUIREMENTS ({len(active)}):\n" + "\n".join(lines) +
           f"\n\nBLACKLIST:\n{bl}\n\nCOVERAGE: {cov['covered']}/{cov['raw_total']} raw statements covered, "
           f"{cov['dropped_as_noise']} dropped as noise.\nUNCOVERED RAW STATEMENTS:\n{uncovered}\n"
           f"RAW IDS USED IN MORE THAN ONE REQUIREMENT (possible duplicates): {cov['raw_ids_in_multiple_requirements']}")
    log(f"review [{MODELS['reviewer']}] iteration {state['iteration']} ...")
    res = structured("reviewer", ReviewResult).invoke([("system", prompts.REVIEWER), ("human", msg)])
    data = res.model_dump()
    log(f"review: approved={data['approved']}, {len(data['issues'])} issues")
    dump(state, f"07_review_iter{state['iteration']}", data)
    return {"review": data, "feedback": data["issues"]}


def route_after_review(state: State) -> str:
    """Feedback loop (ANS3): back to the consolidator until approved or the limit is reached."""
    if state["review"]["approved"]:
        return "format_document"
    if state["iteration"] >= state.get("max_iterations", 3):
        log("review: iteration limit reached, finishing with the current version")
        return "format_document"
    return "consolidate"


# ================================================ 8. format_document (deterministic)
PRIORITY_ORDER = {"Must": 0, "Should": 1, "Could": 2, "Won't": 3}

PRIORITY_SCALE = """| Priority | Meaning |
|---|---|
| **Must** | Essential. The system is not acceptable without it (core function, legal or security constraint, demanded by many stakeholders or by the official specification). |
| **Should** | Important and expected, but a temporary workaround exists, so it may follow shortly after the first release. |
| **Could** | Desirable nice-to-have. Implemented only if time and budget allow. |
| **Won't** | Agreed not to be delivered in this release; recorded for future versions. |

Priorities were assigned by the prioritisation agent based on how essential the requirement is, how many independent sources mention it and how strongly the stakeholders worded it."""


def format_document(state: State) -> State:
    raw_by_id = {r["raw_id"]: r for r in state["raw_reqs"]}
    active = _active(state)
    pr = state["priorities"]
    active.sort(key=lambda r: (r["category"].lower(), PRIORITY_ORDER.get(pr.get(r["key"], {}).get("priority"), 9),
                               r["name"].lower()))
    ids = {r["key"]: f"REQ-{i:03d}" for i, r in enumerate(active, 1)}
    bl_ids = {b["discarded_key"]: f"BL-{i:03d}" for i, b in enumerate(state["blacklist"], 1)}
    by_key = {r["key"]: r for r in state["consolidated"]}

    def sources(r):
        return sorted({raw_by_id[x]["source"] for x in r["source_raw_ids"]})

    docs = state["documents"]
    cov = state["coverage"]
    counts = Counter(pr.get(r["key"], {}).get("priority", "?") for r in active)
    out = []
    w = out.append
    w("# Software Requirements Specification\n")
    w(f"*Generated by the requirements-refinement agentic network on {datetime.now():%Y-%m-%d %H:%M}.*\n")
    w("## 1. Introduction\n")
    w(f"This document consolidates the software requirements derived from **{len(docs)} input documents** "
      f"(`{state['input_dir']}`). {len(state['raw_reqs'])} raw statements were extracted and merged into "
      f"**{len(active)} unique requirements**; {len(state['blacklist'])} requirement(s) were discarded as conflicting/nonsensical and "
      f"{cov['dropped_as_noise']} statement(s) as non-requirements (see the Blacklist). "
      f"Each requirement has a unique identifier (REQ-###), a short name, an explanatory paragraph, a priority "
      f"and a list of source documents it was derived from.\n")
    w("**Summary by priority:** " + ", ".join(f"{p}: {counts.get(p, 0)}" for p in PRIORITY_ORDER) + "\n")
    w("## 2. Priority scale (MoSCoW)\n")
    w(PRIORITY_SCALE + "\n")
    if state.get("glossary"):
        w("## 3. Glossary (consistent vocabulary)\n")
        w("| Term | Definition | Replaces |\n|---|---|---|")
        for g in sorted(state["glossary"], key=lambda g: g["term"].lower()):
            w(f"| {g['term']} | {g['definition']} | {', '.join(g['replaces']) or '-'} |")
        w("")

    w("## 4. Requirements\n")
    current = None
    for r in active:
        if r["category"] != current:
            current = r["category"]
            w(f"### {current}\n")
        p = pr.get(r["key"], {})
        w(f"#### {ids[r['key']]}: {r['name']}\n")
        w(f"- **Priority:** {p.get('priority', '?')} – {p.get('rationale', '')}")
        w(f"- **Sources:** " + ", ".join(f"`{s}`" for s in sources(r)))
        w("")
        w(r["description"] + "\n")

    dropped = state.get("dropped", [])

    w("## 5. Blacklist (discarded requirements)\n")
    w("Requirements identified in the inputs but deliberately NOT included in Section 4, with the reason.\n")
    w("### 5.1 Conflicting, nonsensical, infeasible or out-of-scope requirements\n")
    if not state["blacklist"]:
        w("The conflict-checking agent found no requirement that had to be discarded.\n")
    for b in state["blacklist"]:
        r = by_key[b["discarded_key"]]
        other = b.get("conflicts_with_key")
        w(f"#### {bl_ids[b['discarded_key']]}: {r['name']}\n")
        w(f"- **Reason:** {b['kind']}" + (f" (conflicts with {ids.get(other, other)})" if other else ""))
        w(f"- **Sources:** " + ", ".join(f"`{s}`" for s in sources(r)))
        w("")
        w(f"*Original statement:* {r['description']}\n")
        w(f"*Why discarded:* {b['reason']}\n")
    w("### 5.2 Extracted statements that are not software requirements\n")
    if not dropped:
        w("None.\n")
    else:
        w("| ID | Statement | Source | Why discarded |\n|---|---|---|---|")
        for i, d in enumerate(dropped, len(state["blacklist"]) + 1):
            rr = raw_by_id[d["raw_id"]]
            w(f"| BL-{i:03d} | {rr['name']}: {rr['description']} | `{rr['source']}` | {d['reason']} |")
        w("")

    w("## Appendix A: Traceability matrix\n")
    w("| Document | Requirements derived from it |\n|---|---|")
    for d in docs:
        rs = [ids[r["key"]] for r in active if d["path"] in sources(r)]
        w(f"| `{d['path']}` | {', '.join(rs) or '-'} |")
    w("")

    w("## Appendix B: Completeness report\n")
    w(f"- Raw statements extracted: {cov['raw_total']}")
    w(f"- Covered by a requirement: {cov['covered']}")
    w(f"- Discarded as non-requirements: {cov['dropped_as_noise']} (see Section 5.2)")
    w(f"- Review iterations: {state['iteration']}, final review approved: {state['review']['approved']}")
    if state["review"]["issues"]:
        w("- Open reviewer remarks:")
        for i in state["review"]["issues"]:
            w(f"  - {i}")
    if cov["uncovered"]:
        w("\nRaw statements not covered by any requirement (kept here so nothing is silently lost):\n")
        for x in cov["uncovered"]:
            rr = raw_by_id[x]
            w(f"- {x} (`{rr['source']}`): **{rr['name']}** – {rr['description']}")
    w("")

    path = Path(state["output_dir"]) / "requirements.md"
    path.write_text("\n".join(out), encoding="utf-8")
    log(f"format_document: written {path}")
    return {"output_file": str(path)}