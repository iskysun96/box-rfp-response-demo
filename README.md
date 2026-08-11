# Box RFP Response Demo

A review-first RFP workflow that keeps enterprise content in Box while a local
model writes the response draft.

## What it demonstrates

1. A user stores a received RFP and approved company-source documents in Box.
2. A Python script uses the authenticated Box CLI to retrieve the RFP and ask
   Box AI for source-grounded research from a configured Box Hub.
3. The script writes `box-ai-source-analysis.md` locally.
4. A local model—such as Qwen3-14B in Pi—uses that evidence packet to create
   `rfp-response-draft.md` locally.
5. A human reviews the draft before any separate upload or customer-send step.

The script never uploads, edits, moves, shares, or deletes Box content.

## Architecture

```text
Received RFP + approved sources in Box
                 |
                 v
        Box CLI + Box AI Hub research
                 |
                 v
    box-ai-source-analysis.md (local evidence packet)
                 |
                 v
      Local Qwen model in Pi drafts the response
                 |
                 v
      rfp-response-draft.md (human review required)
```

## Prerequisites

- Python 3
- [Box CLI](https://developer.box.com/guides/cli/), authenticated with `box login`
- [Poppler](https://poppler.freedesktop.org/) for `pdftotext` when the RFP is a PDF
- A Box Hub containing the RFP and approved company sources, with Box AI enabled
- Pi (or another local coding-agent harness) and a local model

Install the two command-line dependencies on macOS:

```bash
npm install --global @box/cli
box login
brew install poppler
```

## Configure your Box content

Copy the example configuration:

```bash
cp demo-config.example.json demo-config.json
```

Update `demo-config.json` with IDs from **your** Box account:

```json
{
  "received_rfp_folder_id": "YOUR_RECEIVED_RFP_FOLDER_ID",
  "approved_sources_folder_id": "YOUR_APPROVED_SOURCES_FOLDER_ID",
  "rfp_response_hub_id": "YOUR_RFP_RESPONSE_HUB_ID"
}
```

`demo-config.json` is ignored by Git. Do not commit account-specific IDs.

## Run the evidence-gathering step

```bash
python3 scripts/build_rfp_response.py
```

The script creates `box-ai-source-analysis.md`. It contains:

- the selected RFP text;
- Box AI research organized by RFP question;
- names of the approved source files;
- any citation excerpts returned by Box AI; and
- evidence gaps that must remain review flags.

To use a differently named configuration file:

```bash
python3 scripts/build_rfp_response.py --config path/to/demo-config.json
```

## Use with Pi and a local model

Start Pi from the repository root:

```bash
pi
```

Pi loads [`AGENTS.md`](AGENTS.md). Those instructions constrain the local model
to:

- run the script only after explicit confirmation;
- read `box-ai-source-analysis.md` fully;
- write `rfp-response-draft.md` using only the RFP text and Box AI evidence;
- preserve unsupported items as review flags; and
- stop for human review without uploading anything to Box.

## Guardrails

- Box folders and the Hub are read-only for this workflow.
- The local model must not invent product, security, legal, pricing, retention,
  certification, or availability commitments.
- The local model must not use external information as evidence.
- `rfp-response-draft.md` is a draft, not a final customer response.
- Uploading a reviewed draft requires a separate, explicit workflow.

## Notes

The Box CLI describes `box ai:ask` as intended for direct use, rather than AI
agents. In this demo, the human-triggered deterministic script makes that call;
the local model performs the separate drafting step from the resulting local
evidence packet.
