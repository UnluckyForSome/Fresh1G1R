#!/usr/bin/env python3
"""
Pack, restore and compare the assets of Fresh1G1R's daily GitHub release.

Each release holds one zip per DAT folder, with the DATs at the top level of the zip:
  Fresh1G1R-<Config>-<Redump|No-Intro>.zip  <- daily-1g1r-dat/<Config>/<redump|no-intro>/
  Fresh1G1R-Original-<Redump|No-Intro>.zip  <- daily-virgin-dat/<redump|no-intro>/
  Fresh1G1R-Reports.zip                     <- report/ (Retool's reports for that run)

Commands:
  pack DIST               Write the release zips to DIST.
  unpack DIR              Extract the DAT zips found in DIR back into their folders.
  manifest OUT            Write a JSON hash of every DAT to OUT, ignoring Retool's per-run <date>.
  compare OLD NEW NOTES   Write release notes for the changes from manifest OLD to NEW to NOTES.
                          Exit 0 if any DAT changed, 3 if none did. OLD may be missing.
"""

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
PREFIX = "Fresh1G1R"
ORIGINAL = "Original"  # Asset name used for daily-virgin-dat, so no config may use it
COLLECTIONS = {"redump": "Redump", "no-intro": "No-Intro"}
LABEL_TO_COLLECTION = {label: collection for collection, label in COLLECTIONS.items()}
REPORTS_ASSET = f"{PREFIX}-Reports.zip"
ASSET_PATTERN = re.compile(rf"^{PREFIX}-([A-Za-z0-9-]+)-({'|'.join(COLLECTIONS.values())})\.zip$")
UNCHANGED_EXIT_CODE = 3
NOTES_LIST_LIMIT = 40

# Retool stamps the time of the run into each DAT's header, so every run would differ
HEADER_PATTERN = re.compile(rb"<header>.*?</header>", re.S)
HEADER_DATE_PATTERN = re.compile(rb"<date>[^<]*</date>")

# Parts of a file name that change when the source DAT is updated
SYSTEM_SUFFIXES = [
    re.compile(r" \(\d{8}-\d{6}\)$"),                                            # No-Intro
    re.compile(r" - Datfile \(\d+\) \(\d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2}\)$"),  # Redump
    re.compile(r" \((?:Redump|No-Intro) - Fresh1G1R - [^)]+\)$"),                # Fresh1G1R output
]


def dat_folders(root: Path = ROOT) -> dict[str, Path]:
    """Map each release zip name to the DAT folder it holds."""
    folders = {}
    sources = [(path.name, path) for path in sorted((root / "daily-1g1r-dat").glob("*")) if path.is_dir()]
    if any(name == ORIGINAL for name, _ in sources):
        raise ValueError(f"A config can't be named '{ORIGINAL}': that asset name holds daily-virgin-dat")
    sources.append((ORIGINAL, root / "daily-virgin-dat"))
    for name, source in sources:
        for collection, label in COLLECTIONS.items():
            folder = source / collection
            if folder.is_dir():
                folders[f"{PREFIX}-{name}-{label}.zip"] = folder
    return folders


def folder_for_asset(asset_name: str, root: Path = ROOT) -> Path | None:
    """Return the folder a release zip unpacks into, or None if it isn't a DAT zip."""
    match = ASSET_PATTERN.match(asset_name)
    if not match:
        return None
    name, label = match.groups()
    collection = LABEL_TO_COLLECTION[label]
    if name == ORIGINAL:
        return root / "daily-virgin-dat" / collection
    if not (root / "config" / name).is_dir():
        return None  # The config has been removed, so its DATs stop being published
    return root / "daily-1g1r-dat" / name / collection


def pack(dist: Path, root: Path = ROOT) -> list[Path]:
    dist.mkdir(parents=True, exist_ok=True)
    written = []
    for asset_name, folder in dat_folders(root).items():
        dats = sorted(folder.glob("*.dat"))
        if not dats:
            continue
        zip_path = dist / asset_name
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for dat in dats:
                zf.write(dat, dat.name)
        written.append(zip_path)

    reports = sorted((root / "report").glob("*/*/*.txt"))
    if reports:
        zip_path = dist / REPORTS_ASSET
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for report in reports:
                zf.write(report, report.relative_to(root / "report").as_posix())
        written.append(zip_path)
    return written


def unpack(source: Path, root: Path = ROOT) -> list[Path]:
    restored = []
    for zip_path in sorted(source.glob("*.zip")):
        folder = folder_for_asset(zip_path.name, root)
        if folder is None:
            continue
        folder.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as zf:
            for member in zf.infolist():
                name = member.filename
                if member.is_dir() or "/" in name or "\\" in name or not name.endswith(".dat"):
                    raise ValueError(f"Unexpected entry '{name}' in {zip_path.name}")
                (folder / name).write_bytes(zf.read(member))
        restored.append(folder)
    return restored


def system_name(dat_name: str) -> str:
    stem = dat_name.removesuffix(".dat")
    for pattern in SYSTEM_SUFFIXES:
        stem = pattern.sub("", stem)
    return stem


def content_hash(data: bytes) -> str:
    data = HEADER_PATTERN.sub(lambda m: HEADER_DATE_PATTERN.sub(b"", m.group(0)), data, count=1)
    return hashlib.sha256(data).hexdigest()


def build_manifest(root: Path = ROOT) -> dict[str, dict[str, str]]:
    """Map each release zip name to {system name: content hash} for the DATs it holds."""
    return {
        asset_name: {system_name(dat.name): content_hash(dat.read_bytes()) for dat in sorted(folder.glob("*.dat"))}
        for asset_name, folder in dat_folders(root).items()
    }


def _list(names: list[str]) -> str:
    shown = ", ".join(names[:NOTES_LIST_LIMIT])
    if len(names) > NOTES_LIST_LIMIT:
        shown += f" and {len(names) - NOTES_LIST_LIMIT} more"
    return shown


def compare(old: dict | None, new: dict) -> tuple[bool, str]:
    """Return (changed, Markdown summary of the changes)."""
    if old is None:
        return True, "First release built by the release workflow."

    lines = []
    for asset_name in sorted(set(old) | set(new)):
        before, after = old.get(asset_name, {}), new.get(asset_name, {})
        added = sorted(set(after) - set(before))
        removed = sorted(set(before) - set(after))
        updated = sorted(name for name in set(before) & set(after) if before[name] != after[name])
        if not (added or removed or updated):
            continue
        lines.append(f"**{asset_name.removeprefix(f'{PREFIX}-').removesuffix('.zip')}**")
        for label, names in (("Updated", updated), ("Added", added), ("Removed", removed)):
            if names:
                lines.append(f"- {label} ({len(names)}): {_list(names)}")
        lines.append("")
    if not lines:
        return False, "No DAT changed since the previous release."
    return True, "\n".join(["Changes since the previous release:", ""] + lines).rstrip() + "\n"


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    command, args = argv[1], argv[2:]
    if command == "pack" and len(args) == 1:
        for path in pack(Path(args[0]), ROOT):
            print(f"  {path.name} ({path.stat().st_size / 1_048_576:.1f} MB)")
        return 0
    if command == "unpack" and len(args) == 1:
        for folder in unpack(Path(args[0]), ROOT):
            print(f"  Restored {folder.relative_to(ROOT).as_posix()}")
        return 0
    if command == "manifest" and len(args) == 1:
        out = Path(args[0])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(build_manifest(ROOT), indent=1, sort_keys=True), encoding="utf-8")
        return 0
    if command == "compare" and len(args) == 3:
        old_path, new_path, notes_path = (Path(arg) for arg in args)
        old = json.loads(old_path.read_text(encoding="utf-8")) if old_path.exists() else None
        new = json.loads(new_path.read_text(encoding="utf-8"))
        changed, notes = compare(old, new)
        notes_path.parent.mkdir(parents=True, exist_ok=True)
        notes_path.write_text(notes, encoding="utf-8")
        print(notes)
        return 0 if changed else UNCHANGED_EXIT_CODE
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
