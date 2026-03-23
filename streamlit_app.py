import streamlit as st
import requests

st.set_page_config(page_title="🧬 VMD Visualizer", layout="centered")
st.title("🧠 Natural Language VMD Controller")

backend_url = "http://127.0.0.1:8000"

# Input fields
prompt = st.text_input(
    "Enter your visualization prompt:",
    placeholder="e.g. Show only chain A and color it red"
)

# PDB source toggle
source = st.radio("PDB source", ["Upload file", "Fetch from RCSB"])

pdb_bytes = None
pdb_name = None

if source == "Upload file":
    pdb_file = st.file_uploader("Upload a PDB file", type=["pdb"])
    if pdb_file:
        pdb_bytes = pdb_file.getvalue()
        pdb_name = pdb_file.name
else:
    pdb_id = st.text_input("PDB ID", placeholder="e.g. 1TIM")
    if pdb_id:
        pdb_id = pdb_id.strip().upper()
        pdb_name = f"{pdb_id}.pdb"

if st.button("Generate Script from Prompt"):
    if not prompt:
        st.warning("Please enter a visualization prompt.")
    elif source == "Fetch from RCSB" and pdb_id:
        rcsb_url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
        with st.spinner(f"Fetching {pdb_id} from RCSB..."):
            r = requests.get(rcsb_url)
        if r.status_code == 404:
            st.error(f"PDB ID '{pdb_id}' not found on RCSB.")
        elif r.status_code != 200:
            st.error(f"Failed to fetch PDB (status {r.status_code}).")
        else:
            pdb_bytes = r.content
            st.session_state.pdb_bytes = pdb_bytes
            st.session_state.pdb_name = pdb_name
            files = {"pdb_file": (pdb_name, pdb_bytes)}
            data = {"prompt": prompt}
            with st.spinner("Generating script and rendering..."):
                res = requests.post(f"{backend_url}/vmd/run", files=files, data=data)
            if res.status_code == 200:
                result = res.json()
                st.session_state.tcl_script = result["script"]
                st.image(result["image_path"], use_container_width=True)
            else:
                st.error(f"Backend error: {res.text}")
    elif source == "Upload file" and pdb_bytes:
        st.session_state.pdb_bytes = pdb_bytes
        st.session_state.pdb_name = pdb_name
        files = {"pdb_file": (pdb_name, pdb_bytes)}
        data = {"prompt": prompt}
        with st.spinner("Generating script and rendering..."):
            res = requests.post(f"{backend_url}/vmd/run", files=files, data=data)
        if res.status_code == 200:
            result = res.json()
            st.session_state.tcl_script = result["script"]
            st.image(result["image_path"], use_container_width=True)
        else:
            st.error(f"Backend error: {res.text}")
    else:
        st.warning("Please provide a PDB file or ID.")

# Edit Tcl Script and Re-run
if "tcl_script" in st.session_state:
    st.subheader("Edit Tcl Script")
    tcl_script = st.text_area("Modify your Tcl script", value=st.session_state.tcl_script, height=300)

    if st.button("Run Edited Script"):
        saved_bytes = st.session_state.get("pdb_bytes")
        saved_name = st.session_state.get("pdb_name", "structure.pdb")
        if saved_bytes and tcl_script:
            files = {"pdb_file": (saved_name, saved_bytes)}
            data = {"tcl_script": tcl_script}
            with st.spinner("Running edited script..."):
                res = requests.post(f"{backend_url}/vmd/run-tcl", files=files, data=data)
            if res.status_code == 200:
                result = res.json()
                st.image(result["image_path"], use_container_width=True)
            else:
                st.error(f"Backend error: {res.text}")
        else:
            st.warning("No PDB loaded. Generate a script first.")
