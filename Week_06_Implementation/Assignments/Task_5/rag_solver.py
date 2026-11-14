import ast
import json
import re
import sys
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSIGNMENTS = HERE.parent
REPO_ROOT = ASSIGNMENTS / "Task_1" / "AI4SE_Playground"
TASKS_FILE = ASSIGNMENTS / "missing_code.json"
STORE_FILE = ASSIGNMENTS / "Task_3" / "embeddings.json"
TOP_K = 5
DEFAULT_MODEL = "gpt-5-mini"

# reuse the matching mechanism from Task 4
sys.path.insert(0, str(ASSIGNMENTS / "Task_4"))
from find_relevant_chunks import retrieve  # noqa: E402


def find_method(source, class_name, method_name):
    """Return (start, end, indent, signature) of the method; lines are 0-based, end exclusive."""
    lines = source.splitlines()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                        and item.name == method_name:
                    start = min([item.lineno] + [d.lineno for d in item.decorator_list]) - 1
                    end = item.end_lineno
                    indent = re.match(r"\s*", lines[start]).group(0)
                    signature = textwrap.dedent(
                        "\n".join(lines[start:item.body[0].lineno - 1]))
                    return start, end, indent, signature
    raise ValueError(f"{class_name}.{method_name} not found")


def build_task_text(task, signature):
    return (f"Implement method `{task['method']}` of class `{task['class']}` "
            f"in file `{task['file']}`.\n"
            f"Docstring: {task['docstring'].strip()}\n"
            f"Signature:\n{signature}")


def build_prompt(task_text, chunks):
    context = "\n\n".join(
        f"# {c['file']} (lines {c['start_line']}-{c['end_line']})\n{c['content']}"
        for c in chunks)
    return (
        "You are implementing a missing method in a Python repository.\n\n"
        f"TASK:\n{task_text}\n\n"
        f"RELEVANT CODE FROM THE REPOSITORY:\n{context}\n\n"
        "Return ONLY the complete method (decorators, the def line exactly as in the "
        "signature, the given docstring and the body). No explanations, no other code."
    )


def ask_llm(client, model, prompt):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def clean_code(answer):
    """Strip markdown fences and common indentation from the LLM answer."""
    match = re.search(r"```(?:python)?\n(.*?)```", answer, re.DOTALL)
    code = match.group(1) if match else answer
    return textwrap.dedent(code).strip("\n")


def write_method(path, task, code):
    """Replace the stub method in the file with the generated code."""
    source = path.read_text(encoding="utf-8")
    start, end, indent, _ = find_method(source, task["class"], task["method"])
    lines = source.splitlines()
    new_lines = [indent + line if line.strip() else "" for line in code.splitlines()]
    new_source = "\n".join(lines[:start] + new_lines + lines[end:]) + "\n"
    ast.parse(new_source)  # raises SyntaxError if the generated code is broken
    path.write_text(new_source, encoding="utf-8")


def main():
    from openai import OpenAI

    model = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL
    client = OpenAI()  # reads OPENAI_API_KEY from the environment
    tasks = json.loads(TASKS_FILE.read_text(encoding="utf-8"))

    for i, task in enumerate(tasks, start=1):
        name = f"{task['class']}.{task['method']} ({task['file']})"
        path = REPO_ROOT / task["file"]
        try:
            _, _, _, signature = find_method(path.read_text(encoding="utf-8"),
                                             task["class"], task["method"])
            task_text = build_task_text(task, signature)
            chunks = retrieve(task_text, TOP_K, str(STORE_FILE))
            code = clean_code(ask_llm(client, model, build_prompt(task_text, chunks)))
            write_method(path, task, code)
            print(f"[{i}/{len(tasks)}] OK    {name}")
        except Exception as exc:
            print(f"[{i}/{len(tasks)}] FAIL  {name}: {exc}")


if __name__ == "__main__":
    main()
