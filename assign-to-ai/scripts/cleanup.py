#!/usr/bin/env python3
"""Delete the working files an assign-to-ai run leaves behind.

Keeps source files and the final document. Removes screenshots, crops,
compiled binaries, crash dumps, editor scratch, and backups.

Usage:
  python -I cleanup.py                 # dry run, prints what would go
  python -I cleanup.py --yes           # actually delete
  python -I cleanup.py --yes --dir D   # operate on directory D
"""

import argparse
import os
import sys

# Never deleted, whatever else matches.
KEEP_EXT = {
    ".c", ".h", ".cpp", ".cc", ".hpp",     # C / C++
    ".py", ".r", ".m", ".java", ".cs",     # other source
    ".ipynb",                              # Matplotlib / Jupyter notebooks
    ".md", ".txt", ".csv", ".json",        # notes and data
    ".docx", ".doc", ".pdf", ".odt",       # the deliverable
}

DROP_EXT = {
    ".png", ".jpg", ".jpeg", ".bmp", ".gif",   # screenshots and crops
    ".exe", ".o", ".obj", ".out", ".a", ".so", ".dll", ".class", ".pyc",
    ".log", ".bak", ".tmp", ".dmp", ".ilk", ".pdb", ".gcda", ".gcno",
}

DROP_NAMES = {
    "in.txt",            # stdin redirection file
    "a.out", "build", "dist", "__pycache__", ".pytest_cache",
    "capture_app.py", "docx_code_inserter.py", "cleanup.py", "spec.json",
}

DROP_PREFIX = ("shot", "screenshot", "screen_", "Screenshot ")


def classify(name, path):
    """Return ('drop', reason) or ('keep', reason) or ('ask', reason)."""
    low = name.lower()
    root, ext = os.path.splitext(name)

    if os.path.isdir(path):
        if low in DROP_NAMES:
            return "drop", "build/cache directory"
        if low == ".vscode":
            return "ask", "editor folder - may hold tasks.json you still want"
        if low in (".git", "graft", "node_modules"):
            return "keep", "not a build artifact"
        return "ask", "directory - inspect before removing"

    if ext.lower() in DROP_EXT and ext.lower() not in KEEP_EXT:
        if ext.lower() == ".png" and (
            low.startswith(DROP_PREFIX) or low.endswith("_crop.png") or low.endswith("_c.png")
        ):
            return "drop", "screenshot or crop"
        if ext.lower() == ".png":
            return "ask", "image - possibly a figure you want to keep"
        return "drop", "build artifact"

    if name in DROP_NAMES:
        return "drop", "scratch file"

    if low.endswith(".docx.bak"):
        return "drop", "document backup"

    if ext.lower() in KEEP_EXT:
        return "keep", "source or document"

    return "ask", "unrecognised"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=".")
    ap.add_argument("--yes", action="store_true", help="delete instead of listing")
    args = ap.parse_args()

    root = os.path.abspath(args.dir)
    drops, asks = [], []

    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        verdict, why = classify(name, path)
        if verdict == "drop":
            drops.append((path, why))
        elif verdict == "ask":
            asks.append((path, why))

    if not drops and not asks:
        print("nothing to clean")
        return

    for path, why in drops:
        if args.yes:
            if os.path.isdir(path):
                import shutil
                shutil.rmtree(path, ignore_errors=True)
            else:
                os.remove(path)
            print("removed", os.path.basename(path), "|", why)
        else:
            print("would remove", os.path.basename(path), "|", why)

    for path, why in asks:
        print("REVIEW", os.path.basename(path), "|", why)

    if not args.yes:
        print("\n(dry run - re-run with --yes to delete)")


if __name__ == "__main__":
    main()
