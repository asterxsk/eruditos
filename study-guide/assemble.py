"""Combine ordered chapter fragments into the build tool's canonical YAML input."""
from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def read_mapping(path: Path) -> dict:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Expected a mapping in {path}")
    return value


def resolve_files(value, base: Path):
    if isinstance(value, list):
        return [resolve_files(item, base) for item in value]
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if key in ("file", "path") and isinstance(item, str):
                source = base / item
                if key == "file" and not source.exists() and (base / "code" / item).is_file():
                    source = base / "code" / item
                out[key] = str(source.resolve())
            else:
                out[key] = resolve_files(item, base)
        return out
    return value


def assemble(manifest: Path) -> dict:
    root = read_mapping(manifest)
    if "type" in root or "depth" in root:
        raise ValueError("Delete type/depth; use mode: full or mode: quick")
    if root.get("mode", "full") not in ("full", "quick"):
        raise ValueError("mode must be full or quick")
    paths = root.pop("chapters", None)
    if "sections" in root or not isinstance(paths, list) or not paths:
        raise ValueError("Manifest needs a non-empty chapters list and no sections")
    sections = []
    for name in paths:
        if not isinstance(name, str):
            raise ValueError("Each chapters entry must be a file path")
        path = (manifest.parent / name).resolve()
        fragment = read_mapping(path)
        if set(fragment) != {"sections"} or not isinstance(fragment["sections"], list) or not fragment["sections"]:
            raise ValueError(f"{path}: a chapter fragment must contain only a non-empty sections list")
        for section in fragment["sections"]:
            if not isinstance(section, dict):
                raise ValueError(f"{path}: each section must be a mapping")
        sections.extend(resolve_files(fragment["sections"], path.parent))
    identifiers = set()
    for index, section in enumerate(sections, 1):
        identifier = str(section.get("num") or f"{index:02d}")
        if identifier in identifiers:
            raise ValueError(f"Duplicate section number {identifier!r}; omit num in fragments for global numbering")
        identifiers.add(identifier)
    root["sections"] = sections
    return root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("-o", "--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.resolve() == args.manifest.resolve():
        parser.error("output must differ from the manifest")
    try:
        manifest_data = read_mapping(args.manifest)
        for fragment in manifest_data.get("chapters") or []:
            if isinstance(fragment, str) and (args.manifest.parent / fragment).resolve() == args.out.resolve():
                parser.error("output must differ from every chapter fragment")
        content = assemble(args.manifest.resolve())
    except ValueError as exc:
        parser.error(str(exc))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(yaml.safe_dump(content, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"{args.out}: {len(content['sections'])} sections")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
