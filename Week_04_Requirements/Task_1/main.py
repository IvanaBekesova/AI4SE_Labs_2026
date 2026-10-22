"""Entry point.

Usage:
    python main.py data/corpus
    python main.py data/corpus --out output --max-iterations 3
"""
import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv


def main():
    load_dotenv()
    ap = argparse.ArgumentParser(description="Agentic network for software requirements refinement")
    ap.add_argument("input_dir", help="Directory with the input corpus (searched recursively)")
    ap.add_argument("--out", default="output", help="Output directory (default: output)")
    ap.add_argument("--max-iterations", type=int, default=5, help="Max consolidate/review loops (default: 3)")
    ap.add_argument("--graph", action="store_true", help="Only print the graph as Mermaid and exit")
    args = ap.parse_args()

    from graph import build_graph
    app = build_graph()
    if args.graph:
        print(app.get_graph().draw_mermaid())
        return

    Path(args.out).mkdir(parents=True, exist_ok=True)
    (Path(args.out) / "graph.mmd").write_text(app.get_graph().draw_mermaid(), encoding="utf-8")
    final = app.invoke(
        {"input_dir": args.input_dir, "output_dir": args.out, "max_iterations": args.max_iterations},
        config={"recursion_limit": 100},
    )
    print(f"\nDone. Requirements document: {final['output_file']}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
