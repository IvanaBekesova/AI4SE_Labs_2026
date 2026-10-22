"""LangGraph wiring of the requirements-refinement network."""
from langgraph.graph import END, START, StateGraph

import nodes
from schemas import State


def build_graph():
    g = StateGraph(State)
    g.add_node("load_corpus", nodes.load_corpus)                    # deterministic
    g.add_node("extract_requirements", nodes.extract_requirements)  # LLM
    g.add_node("consolidate", nodes.consolidate)                    # LLM
    g.add_node("trace_and_coverage", nodes.trace_and_coverage)      # deterministic
    g.add_node("detect_conflicts", nodes.detect_conflicts)          # LLM
    g.add_node("prioritize", nodes.prioritize)                      # LLM
    g.add_node("review", nodes.review)                              # LLM
    g.add_node("format_document", nodes.format_document)            # deterministic

    g.add_edge(START, "load_corpus")
    g.add_edge("load_corpus", "extract_requirements")
    g.add_edge("extract_requirements", "consolidate")
    g.add_edge("consolidate", "trace_and_coverage")
    g.add_edge("trace_and_coverage", "detect_conflicts")
    g.add_edge("detect_conflicts", "prioritize")
    g.add_edge("prioritize", "review")
    g.add_conditional_edges("review", nodes.route_after_review,     # feedback loop
                            {"consolidate": "consolidate", "format_document": "format_document"})
    g.add_edge("format_document", END)
    return g.compile()
