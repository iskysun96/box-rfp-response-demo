#!/usr/bin/env python3
"""Build a Box AI evidence packet for a local RFP-writing model.

The script uses the authenticated Box CLI to enumerate the received-RFP and
approved-source folders through a Box Hub. It downloads the RFP locally, then
uses ``box ai:ask`` to query the Hub's indexed content with the extracted RFP
questions. Box AI returns source-grounded research notes.

Nothing is uploaded or modified in Box. The output is
``box-ai-source-analysis.md`` in the current project folder. The local model
uses that evidence packet to create the separate review-only response draft.

Prerequisites:
  1. Install and authenticate the current Box CLI: ``box login``.
  2. Install Poppler for PDF extraction: ``brew install poppler``.

Usage:
  cp demo-config.example.json demo-config.json
  # Edit demo-config.json with IDs from the user's own Box account.
  python3 scripts/build_rfp_response.py

  # Or use a differently named configuration file.
  python3 scripts/build_rfp_response.py --config path/to/demo-config.json
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


OUTPUT_PATH = Path("box-ai-source-analysis.md")
SUPPORTED_SOURCE_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".html", ".htm", ".xlsx"}
LOCALLY_EXTRACTABLE_RFP_EXTENSIONS = {".pdf", ".txt", ".md", ".html", ".htm"}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_config(config_path: Path) -> dict[str, str]:
    """Load account-specific Box locations without storing them in source code."""
    if not config_path.is_file():
        fail(
            f"Configuration file not found: {config_path}. Create it with: "
            "cp demo-config.example.json demo-config.json"
        )
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"Configuration file is not valid JSON: {config_path}\n{exc}")
    if not isinstance(config, dict):
        fail("Configuration must be a JSON object.")

    required_keys = ("received_rfp_folder_id", "approved_sources_folder_id", "rfp_response_hub_id")
    missing = [key for key in required_keys if not isinstance(config.get(key), str) or not config[key].strip()]
    if missing:
        fail(f"Configuration is missing required non-empty value(s): {', '.join(missing)}")
    return {key: config[key].strip() for key in required_keys}


def run_box(*args: str) -> Any:
    """Run a Box CLI read command and return its JSON response."""
    try:
        result = subprocess.run(
            ["box", *args, "--json"],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        fail("Box CLI is not installed. Run: npm install --global @box/cli")
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip()
        fail(f"Box CLI command failed: box {' '.join(args)}\n{detail}")

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        fail(f"Box CLI did not return JSON for: box {' '.join(args)}\n{exc}")


def entries_from(response: Any) -> list[dict[str, Any]]:
    """Handle the collection shapes returned by current and older CLI builds."""
    if isinstance(response, list):
        return [item for item in response if isinstance(item, dict)]
    if not isinstance(response, dict):
        return []
    for key in ("entries", "item_collection"):
        value = response.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict) and isinstance(value.get("entries"), list):
            return value["entries"]
    return []


def list_files(folder_id: str) -> list[dict[str, Any]]:
    response = run_box("folders:items", folder_id)
    files = [item for item in entries_from(response) if item.get("type") == "file"]
    if not files:
        fail(f"No files found in Box folder {folder_id}.")
    return files


def pick_rfp_file(files: list[dict[str, Any]]) -> dict[str, Any]:
    preferred = [item for item in files if "rfp" in item.get("name", "").lower()]
    candidates = preferred or files
    supported = [
        item
        for item in candidates
        if Path(item.get("name", "")).suffix.lower() in LOCALLY_EXTRACTABLE_RFP_EXTENSIONS
    ]
    if not supported:
        fail("The received-RFP folder has no supported document to download.")
    return supported[0]


def download_rfp(file_id: str, destination: Path) -> None:
    """Download with the Box CLI. This is read-only for the Box account."""
    try:
        subprocess.run(
            # The CLI interprets --destination as a directory and preserves the
            # original filename beneath it.
            ["box", "files:download", file_id, "--destination", str(destination.parent)],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip()
        fail(f"Could not download RFP file {file_id}.\n{detail}")
    if not destination.is_file():
        fail(f"Box CLI downloaded RFP file {file_id}, but the expected file was not created: {destination}")


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt", ".html", ".htm"}:
        return path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".pdf":
        if not shutil.which("pdftotext"):
            fail("pdftotext is missing. Install Poppler with: brew install poppler")
        result = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout
    fail(f"RFP type {suffix} is not supported for local extraction in this demo.")


def ask_box_ai(hub_id: str, source_files: list[dict[str, Any]], rfp_text: str) -> dict[str, Any]:
    """Ask Box AI against the RFP workspace Hub through the authenticated CLI."""
    source_list = "\n".join(f"- {item['name']} (Box file ID {item['id']})" for item in source_files)
    prompt = f"""You are a research assistant preparing an evidence packet for a local model that will later draft a customer RFP response.

Use ONLY the approved company-source files named below as evidence. The Hub also
contains the received RFP; use it only to understand the customer's questions,
never as evidence for an answer. Do not use outside knowledge. Do not infer
product commitments, legal terms, certifications, or capabilities that are absent
from the approved sources.

For every customer question below, return exactly this structure:

## [question number or short question title]
**Approved evidence:** [specific facts, limits, and wording found in the sources]
**Source files:** [which approved source(s) support those facts]
**Evidence gap / review flag:** [\"None\" or a short explanation of what the sources do not establish]

Do not write a customer-facing response. Do not make commitments. If a request
is not supported, say so plainly and do not invent evidence.

Approved source files (the only permitted evidence):
{source_list}

Received RFP text:
---
{rfp_text[:45000]}
---
"""
    command = [
        "box",
        "ai:ask",
        "--prompt",
        prompt,
        "--items",
        f"id={hub_id},type=hubs",
    ]
    # --raw-json preserves API field names, including citations.
    command.append("--raw-json")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip()
        fail(
            "Box AI Hub request failed. Confirm that Box AI is enabled on the RFP Response "
            f"Workspace Hub and that your Box CLI login has AI access.\n{detail}"
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        fail(f"Box AI did not return raw JSON.\n{exc}\n{result.stdout}")


def markdown_escape(value: str) -> str:
    return value.replace("\r\n", "\n").strip()


def render_evidence_packet(
    rfp_file: dict[str, Any],
    source_files: list[dict[str, Any]],
    rfp_text: str,
    ai_response: dict[str, Any],
) -> str:
    citations = ai_response.get("citations", [])
    citation_lines = []
    for citation in citations:
        name = citation.get("name", "Unnamed Box source")
        file_id = citation.get("id", "unknown")
        excerpt = re.sub(r"\s+", " ", citation.get("content", "")).strip()
        citation_lines.append(f"- **{name}** (Box file ID `{file_id}`): {excerpt}")
    if not citation_lines:
        citation_lines.append("- Box AI returned no excerpts. Use the named approved source files and evidence notes for review.")

    source_lines = "\n".join(f"- {item['name']} (Box file ID `{item['id']}`)" for item in source_files)
    answer = markdown_escape(ai_response.get("answer", "No answer was returned by Box AI."))
    return f"""# Box AI Source Analysis — Input for Local Drafting

> **Status:** Evidence packet only. A local model may use this packet to draft a response, but a qualified reviewer must approve the final wording.

## Inputs

- **Received RFP:** {rfp_file['name']} (Box file ID `{rfp_file['id']}`)
- **Approved company sources supplied to Box AI:**
{source_lines}
- **Generated:** {ai_response.get('created_at', 'time not returned by Box AI')}

## Received RFP Text

{markdown_escape(rfp_text)}

## Box AI Evidence by RFP Question

{answer}

## Box AI Citation Excerpts (when returned)

{chr(10).join(citation_lines)}

## Local Drafting Rules

- Use only the RFP text and evidence above to draft the customer response.
- Do not turn missing evidence into a product, security, legal, or pricing commitment.
- Carry every evidence gap into the final draft as a review flag.
- The final response remains local and requires human approval before any upload step.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a local Box AI evidence packet for RFP drafting.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("demo-config.json"),
        help="Path to the JSON file containing the user's Box folder and Hub IDs.",
    )
    args = parser.parse_args()
    config = load_config(args.config)

    print("Listing the received RFP folder through Box CLI…")
    rfp_file = pick_rfp_file(list_files(config["received_rfp_folder_id"]))
    print(f"Using received RFP: {rfp_file['name']}")

    print("Listing the approved company-sources folder through Box CLI…")
    all_source_files = list_files(config["approved_sources_folder_id"])
    source_files = [
        item for item in all_source_files
        if Path(item.get("name", "")).suffix.lower() in SUPPORTED_SOURCE_EXTENSIONS
    ]
    if not source_files:
        fail("No supported approved source documents were found.")
    if len(source_files) > 25:
        fail("Box AI supports up to 25 files per multiple-item request. Narrow the approved source folder first.")

    with tempfile.TemporaryDirectory(prefix="box-rfp-") as temporary_directory:
        local_rfp = Path(temporary_directory) / rfp_file["name"]
        print("Downloading the received RFP through Box CLI…")
        download_rfp(str(rfp_file["id"]), local_rfp)
        rfp_text = extract_text(local_rfp).strip()
    if not rfp_text:
        fail("No text could be extracted from the received RFP.")

    print(f"Asking Box AI to analyze the configured RFP Response Hub ({len(source_files)} approved source file(s))…")
    ai_response = ask_box_ai(config["rfp_response_hub_id"], source_files, rfp_text)
    OUTPUT_PATH.write_text(
        render_evidence_packet(rfp_file, source_files, rfp_text, ai_response),
        encoding="utf-8",
    )
    print(f"Created Box AI evidence packet: {OUTPUT_PATH.resolve()}")
    print("No files were uploaded or modified in Box.")


if __name__ == "__main__":
    main()
