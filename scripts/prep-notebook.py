#!/usr/bin/env python
"""
prep-notebook.py - run before committing a notebook.

For a chosen notebook:
  1. duplicates it to <name>_executed.ipynb
  2. executes the duplicate end-to-end
  3. sanitizes paths / hostname / IP / MAC from text outputs (images untouched)
  4. clears outputs on the original (clean diffable source)
  5. git-adds both files

Usage:
    python scripts/prep-notebook.py partitioning
    python scripts/prep-notebook.py src/notebooks/Partitioning.ipynb

Register new notebooks in NOTEBOOK_REGISTRY in src/GlobalVariables.py.
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

import nbformat
from nbconvert.preprocessors import ClearOutputPreprocessor, ExecutePreprocessor
from nbclient.exceptions import CellExecutionError

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
from GlobalVariables import NOTEBOOK_REGISTRY, NOTEBOOK_EXEC_TIMEOUT  # noqa: E402


# mimetypes that hold human-readable text and are safe to regex.
# anything not in this set (image/png, image/svg+xml, plotly json, etc.) is left alone.
SANITIZABLE_MIMETYPES = {
    "text/plain",
    "text/html",
    "text/markdown",
    "application/vnd.jupyter.stderr",
    "application/vnd.jupyter.stdout",
}


def build_sanitizers(repo_root: Path):
    """Return a list of (compiled_regex, replacement) pairs, applied in order."""
    # escape the repo root so it can sit inside a regex pattern
    repo_root_str = re.escape(str(repo_root))
    return [
        # repo-root paths first so we keep the useful tail, e.g. <REPO>/src/data/foo.gct
        (re.compile(repo_root_str), "<REPO>"),
        # generic home prefixes - works for any user on mac or linux
        (re.compile(r"/Users/[^/\s'\"`)\]<>]+"), "~"),
        (re.compile(r"/home/[^/\s'\"`)\]<>]+"), "~"),
        # bonjour-style hostnames (AnniesSpaceShip.local etc.) - but not 127.0.0.1.local
        (re.compile(r"\b[A-Za-z][\w-]*\.local\b"), "<HOST>"),
        # IPv4 - skip loopback so legitimate 127.0.0.1 references survive
        (re.compile(r"\b(?!127\.0\.0\.1\b)(?:\d{1,3}\.){3}\d{1,3}\b"), "<IP>"),
        # MAC addresses
        (re.compile(r"\b(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b"), "<MAC>"),
    ]


def sanitize_text(text: str, sanitizers) -> str:
    for pattern, replacement in sanitizers:
        text = pattern.sub(replacement, text)
    return text


def sanitize_notebook(nb_path: Path, sanitizers) -> int:
    """Walk all output cells and scrub text-flavored payloads. Returns count of edits."""
    nb = nbformat.read(nb_path, as_version=4)
    edits = 0

    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        for output in cell.get("outputs", []):
            # stream outputs (stdout / stderr from print, Spark warnings, etc.)
            if "text" in output and isinstance(output["text"], str):
                new = sanitize_text(output["text"], sanitizers)
                if new != output["text"]:
                    output["text"] = new
                    edits += 1
            # execute_result / display_data outputs - have a data dict keyed by mimetype
            if "data" in output and isinstance(output["data"], dict):
                for mime, payload in list(output["data"].items()):
                    if mime not in SANITIZABLE_MIMETYPES:
                        continue
                    if isinstance(payload, str):
                        new = sanitize_text(payload, sanitizers)
                        if new != payload:
                            output["data"][mime] = new
                            edits += 1
                    elif isinstance(payload, list):
                        # text/plain often comes back as a list of lines
                        new_list = [sanitize_text(line, sanitizers) for line in payload]
                        if new_list != payload:
                            output["data"][mime] = new_list
                            edits += 1

    nbformat.write(nb, nb_path)
    return edits


def resolve_notebook(arg: str) -> Path:
    """Map a CLI arg to an absolute notebook path."""
    looks_like_path = "/" in arg or arg.endswith(".ipynb")
    if looks_like_path:
        candidate = Path(arg)
        if not candidate.is_absolute():
            candidate = REPO_ROOT / candidate
        return candidate.resolve()

    if arg not in NOTEBOOK_REGISTRY:
        valid = ", ".join(sorted(NOTEBOOK_REGISTRY)) or "(registry is empty)"
        sys.exit(
            f"error: '{arg}' is not in NOTEBOOK_REGISTRY.\n"
            f"  valid short names: {valid}\n"
            f"  or pass an explicit path like src/notebooks/Foo.ipynb"
        )

    return (REPO_ROOT / NOTEBOOK_REGISTRY[arg]).resolve()


def execute_notebook(executed_path: Path, exec_cwd: Path) -> None:
    """Run the notebook in place. Raises on failure.

    exec_cwd is the working directory the notebook sees while executing - we set
    it to the SOURCE notebook's parent so any relative paths in cells (like
    `sys.path.insert(0, os.path.abspath('..'))`) keep working even though the
    executed copy lives in a different folder.
    """
    nb = nbformat.read(executed_path, as_version=4)
    kernel_name = nb.metadata.get("kernelspec", {}).get("name", "python3")
    ep = ExecutePreprocessor(timeout=NOTEBOOK_EXEC_TIMEOUT, kernel_name=kernel_name)
    ep.preprocess(nb, {"metadata": {"path": str(exec_cwd)}})
    nbformat.write(nb, executed_path)


def clear_outputs(nb_path: Path) -> None:
    nb = nbformat.read(nb_path, as_version=4)
    ClearOutputPreprocessor().preprocess(nb, {})
    nbformat.write(nb, nb_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("notebook", help="short name from NOTEBOOK_REGISTRY or a path to a .ipynb")
    parser.add_argument("--no-stage", action="store_true", help="skip the final 'git add' step")
    args = parser.parse_args()

    src = resolve_notebook(args.notebook)
    if not src.exists():
        sys.exit(f"error: notebook not found: {src}")
    if src.suffix != ".ipynb":
        sys.exit(f"error: not a notebook: {src}")
    if src.stem.endswith(("_Executed", "_executed")):
        sys.exit(f"error: refusing to run on an already-executed notebook: {src.name}")

    # executed copies live in a sibling "Executed/" folder, named NameOfNotebook_Executed.ipynb
    executed_dir = src.parent / "Executed"
    executed_dir.mkdir(exist_ok=True)
    executed = executed_dir / f"{src.stem}_Executed.ipynb"

    print(f"source:   {src.relative_to(REPO_ROOT)}")
    print(f"executed: {executed.relative_to(REPO_ROOT)}")
    print()

    # step 1: duplicate
    shutil.copy(src, executed)

    # step 2: execute the duplicate (cwd pinned to source's parent so relative imports work)
    print("executing notebook (this can take a while for spark jobs)...")
    try:
        execute_notebook(executed, src.parent)
    except CellExecutionError as e:
        executed.unlink(missing_ok=True)
        sys.exit(
            f"\nexecution failed - source notebook left untouched so you can debug.\n"
            f"removed half-baked: {executed.name}\n\n{e}"
        )
    print("execution ok.")

    # step 3: sanitize the executed copy
    sanitizers = build_sanitizers(REPO_ROOT)
    edits = sanitize_notebook(executed, sanitizers)
    print(f"sanitized {edits} text output field(s) in {executed.name}.")

    # step 4: clear the original
    clear_outputs(src)
    print(f"cleared outputs on {src.name}.")

    # step 5: stage both
    if args.no_stage:
        print("\nskipped git add (--no-stage).")
        return
    try:
        subprocess.run(
            ["git", "add", str(src), str(executed)],
            check=True,
            cwd=REPO_ROOT,
        )
        print(f"\nstaged: {src.name} and {executed.name}.")
    except subprocess.CalledProcessError as e:
        sys.exit(f"git add failed: {e}")


if __name__ == "__main__":
    main()
