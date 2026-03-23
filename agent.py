import streamlit as st
import anthropic
import requests
import os
import sys
from pathlib import Path

# Import run_vmd_script directly from main.py (no HTTP overhead)
sys.path.insert(0, str(Path(__file__).parent))
from main import run_vmd_script

# ---------------------------------------------------------------------------
# Anthropic client
# ---------------------------------------------------------------------------
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

MODEL = "claude-sonnet-4-6"

# ---------------------------------------------------------------------------
# Tool definition (Anthropic format)
# ---------------------------------------------------------------------------
tools = [
    {
        "name": "execute_vmd",
        "description": (
            "Execute a VMD Tcl script on the loaded protein structure and return a rendered image."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tcl_script": {
                    "type": "string",
                    "description": (
                        "Complete VMD Tcl script. Assume the structure is already loaded as "
                        "molecule 0 (top). Always start by removing all existing representations."
                    ),
                }
            },
            "required": ["tcl_script"],
        },
    }
]

SYSTEM_PROMPT = """You are an expert in VMD (Visual Molecular Dynamics) Tcl scripting and protein structure visualization.
A protein structure has been loaded. When the user asks you to visualize something, use the execute_vmd tool to render it.

VMD Tcl conventions:
- Always start scripts with a loop to remove all existing representations:
    set nreps [molinfo top get numreps]
    for {set i 0} {$i < $nreps} {incr i} { mol delrep 0 top }
- Background: color Display Background white
- Turn off axes: axes location off
- Turn off depth cueing: display depthcue off
- Color codes: 0=blue, 1=red, 2=gray, 3=orange, 4=yellow, 5=tan, 6=silver, 7=green, 8=white, 9=pink, 10=cyan
- Default drawing method: VDW (unless user asks for ribbon, cartoon, surface, licorice, etc.)
- To add a representation:
    mol addrep top
    mol modstyle 0 top <DrawMethod>
    mol modcolor 0 top ColorID <n>
    mol modselect 0 top "<selection>"
- if representation is said Ribbon it means NewRibbons representation with thickness 3.0 showing alpha helices and beta sheets; not vdw or cpk
- Multiple representations: increment the rep index (0, 1, 2, ...) for each mol modstyle/modcolor/modselect call

After each render, briefly describe what is shown. Remember context from previous messages to maintain continuity."""

# ---------------------------------------------------------------------------
# Helper: serialize Anthropic content blocks to plain dicts for session state
# ---------------------------------------------------------------------------
def serialize_content(content):
    result = []
    for block in content:
        if block.type == "text":
            result.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            result.append({"type": "tool_use", "id": block.id, "name": block.name, "input": block.input})
    return result

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="VMD Agent", layout="centered")
st.title("VMD Visualization Agent")

# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_display" not in st.session_state:
    st.session_state.chat_display = []

# ---------------------------------------------------------------------------
# Sidebar: PDB loading
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Load Protein Structure")

    pdb_id_input = st.text_input("PDB ID (e.g. 1CRN)")
    if st.button("Fetch from RCSB") and pdb_id_input:
        pdb_id = pdb_id_input.strip().upper()
        url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
        with st.spinner(f"Fetching {pdb_id}..."):
            resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            pdb_path = f"/tmp/{pdb_id}.pdb"
            with open(pdb_path, "wb") as f:
                f.write(resp.content)
            st.session_state.pdb_path = pdb_path
            st.session_state.messages = []
            st.session_state.chat_display = []
            st.success(f"Loaded {pdb_id}")
        else:
            st.error(f"Could not fetch {pdb_id} (HTTP {resp.status_code})")

    st.markdown("---")

    uploaded = st.file_uploader("Or upload a .pdb file", type=["pdb"])
    if uploaded is not None:
        pdb_path = f"/tmp/{uploaded.name}"
        with open(pdb_path, "wb") as f:
            f.write(uploaded.getbuffer())
        if st.session_state.get("pdb_path") != pdb_path:
            st.session_state.pdb_path = pdb_path
            st.session_state.messages = []
            st.session_state.chat_display = []
            st.success(f"Loaded {uploaded.name}")

    if "pdb_path" in st.session_state:
        st.info(f"Active structure: **{Path(st.session_state.pdb_path).name}**")
    else:
        st.warning("No structure loaded. Fetch a PDB ID or upload a file.")

# ---------------------------------------------------------------------------
# Render existing chat history
# ---------------------------------------------------------------------------
for entry in st.session_state.chat_display:
    with st.chat_message(entry["role"]):
        if entry.get("text"):
            st.markdown(entry["text"])
        if entry.get("image"):
            st.image(entry["image"], use_container_width=True)
            with open(entry["image"], "rb") as f:
                st.download_button("Download image", f, file_name=Path(entry["image"]).name, mime="image/png", key=entry["image"])

# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------
user_input = st.chat_input(
    "Describe the visualization...",
    disabled="pdb_path" not in st.session_state,
)

if user_input:
    if "pdb_path" not in st.session_state:
        st.warning("Please load a PDB structure first.")
        st.stop()

    # Show user message immediately
    st.session_state.chat_display.append({"role": "user", "text": user_input, "image": None})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Append to message history
    st.session_state.messages.append({"role": "user", "content": user_input})

    # ------------------------------------------------------------------
    # Agent loop
    # ------------------------------------------------------------------
    image_path = None
    final_text = ""

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=tools,
                messages=st.session_state.messages,
            )

            # Keep going while Claude wants to call tools
            while response.stop_reason == "tool_use":
                tool_results = []

                for block in response.content:
                    if block.type == "tool_use" and block.name == "execute_vmd":
                        tcl_script = block.input["tcl_script"]

                        # Run VMD; returns "http://localhost:8000/static/vmd_<uuid>.png"
                        result_url = run_vmd_script(tcl_script, st.session_state.pdb_path)
                        local_path = result_url.replace("http://localhost:8000/", "")
                        image_path = local_path

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": "Image rendered successfully.",
                        })

                # Append assistant turn and tool results (serialize to plain dicts)
                st.session_state.messages.append(
                    {"role": "assistant", "content": serialize_content(response.content)}
                )
                st.session_state.messages.append(
                    {"role": "user", "content": tool_results}
                )

                response = client.messages.create(
                    model=MODEL,
                    max_tokens=4096,
                    system=SYSTEM_PROMPT,
                    tools=tools,
                    messages=st.session_state.messages,
                )

            # Extract final text
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text

            # Persist final assistant message
            st.session_state.messages.append(
                {"role": "assistant", "content": serialize_content(response.content)}
            )

        if final_text:
            st.markdown(final_text)
        if image_path:
            st.image(image_path, use_container_width=True)
            with open(image_path, "rb") as f:
                st.download_button("Download image", f, file_name=Path(image_path).name, mime="image/png")

    st.session_state.chat_display.append(
        {"role": "assistant", "text": final_text, "image": image_path}
    )
