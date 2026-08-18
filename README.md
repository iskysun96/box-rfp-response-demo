# Box RFP Response Demo

A review-first RFP workflow that keeps enterprise content in Box while a
drafting agent writes the response draft.

## What it demonstrates

1. A user stores a received RFP and approved company-source documents in Box.
2. A Python script uses the authenticated Box CLI to retrieve the RFP and ask
   Box AI for source-grounded research from a configured Box Hub.
3. The script writes `box-ai-source-analysis.md` locally.
4. A drafting agent uses that evidence packet to create
   `rfp-response-draft.md` locally.
5. A human reviews the draft before any separate upload or customer-send step.
6. The drafting agent uploads the reviewed draft to Box after explicit approval.

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
      Drafting agent writes the response
                 |
                 v
      rfp-response-draft.md (human review required)
                 |
                 v
      Drafting agent uploads the reviewed draft to Box
```

## Prerequisites

- Python 3
- [Box CLI](https://developer.box.com/guides/cli/), authenticated with `box login`
- [Poppler](https://poppler.freedesktop.org/) for `pdftotext` when the RFP is a PDF
- A Box Hub containing the RFP and approved company sources, with Box AI enabled
- A drafting agent that can follow `AGENTS.md` and edit local Markdown files

Install the two command-line dependencies on macOS:

```bash
npm install --global @box/cli
box login
brew install poppler
```

## Set up the demo workspace in Box

This demo uses three Box folders and one Box Hub. It does not require a
separate Hub for each folder.

### 1. Copy the demo files into Box

In the Box web app, create a top-level folder named **RFP Response Demo
Workspace**. Then copy the three folders inside `demo-files` into that Box
folder. Keep the bundled folder names and structure unchanged:

```text
RFP Response Demo Workspace/
├── 01_Received_RFP/
├── 02_Approved_Company_Sources/
└── 03_Review/
```

Use the folders as follows:

- `01_Received_RFP` contains the customer RFP. The script selects a supported
  RFP file from this folder and downloads it only to a temporary local
  directory.
- `02_Approved_Company_Sources` contains the governed, approved material that
  may be used as evidence for draft responses.
- `03_Review` is the destination for a draft after a person reviews it and
  explicitly approves its upload.

For general folder-creation steps, see Box's
[Create New Files and Folders](https://support.box.com/hc/en-us/articles/360043696394-Create-New-Files-And-Folders)
guide.

### 2. Create the Box Hub

1. In the Box web app, select **Hubs** in the left navigation.
2. Select **New Hub**.
3. Name the Hub **RFP Response Workspace Hub**.
4. Add an optional description such as: `Governed RFP and approved company
   evidence for the review-only response demo.`
5. Add all three folders, `01_Received_RFP`, `02_Approved_Company_Sources`, and `03_Review` to the Hub.
6. Save the Hub and publish it if the Box interface prompts you to do so.

You must be an owner, co-owner, or editor of content to add it to a Hub, and the
content must be owned by your enterprise. Adding collaborators to a Hub can
also grant them Viewer access to its included content, so review permissions
before sharing it. See Box's official guides for
[creating a Hub](https://support.box.com/hc/en-us/articles/25823366568467-Creating-and-Deleting-a-Hub)
and
[adding Hub content](https://support.box.com/hc/en-us/articles/25870093558675-Adding-Content-to-Box-Hubs).

### 3. Record the Box IDs

Open each of the three folders in Box and copy the numeric
ID after the final slash in its URL. For example, the folder ID in
`https://app.box.com/folder/12345` is `12345`.

Open **RFP Response Workspace Hub** and copy its numeric Hub ID from the URL.
For example, the Hub ID in `https://app.box.com/hubs/67890` is `67890`.

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
  "rfp_response_hub_id": "YOUR_RFP_RESPONSE_HUB_ID",
  "review_folder_id": "YOUR_REVIEW_FOLDER_ID"
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

## Use with a drafting agent

Open the repository root in your preferred agent environment. The agent should
load [`AGENTS.md`](AGENTS.md), whose instructions require it to:

- run the script only after explicit confirmation;
- read `box-ai-source-analysis.md` fully;
- write `rfp-response-draft.md` using only the RFP text and Box AI evidence;
- preserve unsupported items as review flags; and
- stop for human review without uploading anything to Box.

## Guardrails

- Box folders and the Hub are read-only for this workflow.
- The drafting agent must not invent product, security, legal, pricing, retention,
  certification, or availability commitments.
- The drafting agent must not use external information as evidence.
- `rfp-response-draft.md` is a draft, not a final customer response.
- Uploading a reviewed draft requires a separate, explicit workflow.

## Notes

The Box CLI describes `box ai:ask` as intended for direct use, rather than AI
agents. In this demo, the human-triggered deterministic script makes that call;
the drafting agent performs the separate drafting step from the resulting local
evidence packet.
