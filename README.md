# Agentic VMD Visualizer

A natural language interface for [VMD (Visual Molecular Dynamics)](https://www.ks.uiuc.edu/Research/vmd/). Upload a PDB file, describe a visualization in plain English, and get a rendered image — no Tcl scripting required.

## How it works

1. User uploads a PDB file and enters a natural language prompt
2. An LLM (GPT-4o via OpenRouter) converts the prompt into a VMD Tcl script
3. VMD runs headlessly to render the scene using TachyonInternal
4. A PNG is returned and displayed in the UI

The Streamlit frontend also exposes the generated Tcl script in an editable text area, so users can tweak and re-render without re-prompting.

## Example

**Prompt:** `Color chain A red in ribbon representation, hide everything else`

**Generated Tcl:**
```tcl
delrep 0 top
color Display Background white
axes location Off
display depthcue off
mol addrep top
mol modstyle 0 top NewRibbons
mol modcolor 0 top ColorID 1
mol modselect 0 top "chain A"
```

## Setup

**Requirements:**
- [VMD](https://www.ks.uiuc.edu/Research/vmd/) installed at `/Applications/VMD.app/` (macOS ARM64)
- Python 3.9+
- An [Anthropic](https://console.anthropic.com) API key

**Install dependencies:**
```bash
pip install fastapi uvicorn anthropic pillow streamlit requests python-multipart
```

**Set environment variable:**
```bash
cp .env.example .env
# edit .env and add your Anthropic key
export ANTHROPIC_API_KEY=sk-ant-...
```

## Running

**Start the FastAPI backend:**
```bash
uvicorn main:app --reload
```

**Start the Streamlit frontend** (separate terminal):
```bash
streamlit run streamlit_app.py
```

Then open `http://localhost:8501` and upload a PDB file.

**Test the backend directly:**
```bash
curl -X POST "http://127.0.0.1:8000/vmd/run" \
  -F "prompt=Color chain A red in ribbon representation and hide everything else" \
  -F "pdb_file=@A1B1.pdb"
```

## API endpoints

| Endpoint | Description |
|---|---|
| `POST /vmd/run` | Natural language prompt + PDB → rendered PNG URL |
| `POST /vmd/run-tcl` | Raw Tcl script + PDB → rendered PNG URL |
| `GET /static/<filename>` | Serve rendered images |
