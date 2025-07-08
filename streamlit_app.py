import streamlit as st
import requests

st.set_page_config(page_title="🧬 VMD Visualizer", layout="centered")
st.title("🧠 Natural Language VMD Controller")

# Input fields
prompt = st.text_input(
    "Enter your visualization prompt:",
    placeholder="e.g. Show only chain A and color it red"
)

pdb_file = st.file_uploader("Upload a PDB file", type=["pdb"])

if st.button("Run VMD"):
    if not prompt or not pdb_file:
        st.warning("Please provide both a prompt and a PDB file.")
    else:
        with st.spinner("Sending request to backend..."):
            files = {"pdb_file": (pdb_file.name, pdb_file.getvalue())}
            data = {"prompt": prompt}

            try:
                res = requests.post("http://127.0.0.1:8000/vmd/run", files=files, data=data)

                if res.status_code == 200:
                    result = res.json()
                    st.success("✅ VMD script generated and image rendered!")

                    st.subheader("🧾 VMD Tcl Script")
                    st.code(result["script"], language="tcl")

                    st.subheader("🖼️ Rendered Image")
                    image_url = result["image_path"]
                    image_res = requests.get(image_url)
                    if image_res.status_code == 200:
                        st.image(image_res.content, caption="VMD Rendered Output", use_container_width=True)
                    else:
                        st.warning("Image could not be loaded from backend.")

                else:
                    st.error(f"Backend error {res.status_code}: {res.text}")
            except Exception as e:
                st.error(f"Request failed: {e}")
