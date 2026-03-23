# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

Agentic VMD Visualizer: a natural language interface for [VMD (Visual Molecular Dynamics)](https://www.ks.uiuc.edu/Research/vmd/). A user uploads a PDB file and describes a visualization in plain English; an LLM converts that to a VMD Tcl script, VMD runs headlessly to render a snapshot, and the PNG is returned.

## Architecture

**Two-process design:**

1. **FastAPI backend** (`main.py`) — exposes two endpoints:
   - `POST /vmd/run` — accepts a natural language `prompt` + `pdb_file`, calls the LLM to generate a Tcl script, runs VMD, returns an image URL.
   - `POST /vmd/run-tcl` — accepts a raw `tcl_script` + `pdb_file`, skips the LLM, runs VMD directly.
   - Serves rendered PNGs from `./static/` at `/static`.

2. **Streamlit frontend** (`streamlit_app.py`) — sends multipart form requests to the FastAPI server at `http://127.0.0.1:8000`. Shows the generated Tcl script in an editable text area so users can tweak and re-run without re-prompting.

**LLM integration:** Uses the Anthropic Python client with model `claude-sonnet-4-6`. API key is read from the `ANTHROPIC_API_KEY` environment variable.

**VMD rendering pipeline:**
1. Write a `.tcl` file to `/tmp/` that loads the PDB, appends the generated script, calls `render TachyonInternal <path>.tga`, then `quit`.
2. Execute `/Applications/VMD.app/Contents/vmd/vmd_MACOSXARM64 -dispdev text -e <script.tcl>`.
3. Convert the `.tga` output to `.png` via Pillow (`convert_tga_to_png`).
4. Move the PNG to `./static/` with a UUID filename.

**Tcl script conventions** (baked into the LLM system prompt):
- Always start with `delrep 0 top` to remove the default representation.
- Set `color Display Background white`.
- Turn off axes and depth cueing.
- Default drawing method is VDW; default coloring uses VMD numeric color codes (0=blue, 1=red, 2=gray, 3=orange, 4=yellow, 5=tan, 6=silver, 7=green, 8=white, 9=pink, 10=cyan).

## Running the App

**Start the FastAPI backend:**
```bash
uvicorn main:app --reload
```

**Start the Streamlit frontend** (in a separate terminal):
```bash
streamlit run streamlit_app.py
```

**Test the backend directly:**
```bash
# Natural language prompt endpoint
curl -X POST "http://127.0.0.1:8000/vmd/run" \
  -F "prompt=Color chain A red in new ribbon representation and hide everything else" \
  -F "pdb_file=@A1B1.pdb"
```

## Environment

- `ANTHROPIC_API_KEY` — Anthropic API key (required)
- VMD must be installed at `/Applications/VMD.app/` (macOS ARM64 path hardcoded in `main.py:78`)

## Other Files

- `main_app.py` / `app.py` — older drafts; `main.py` is the canonical backend
- `test_agent.ipynb` — scratch notebook for exploring the OpenRouter API
- `A1B1.pdb` — sample PDB file for manual testing
