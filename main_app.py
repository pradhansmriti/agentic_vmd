from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from openai import OpenAI
import os
client = OpenAI(base_url="https://openrouter.ai/api/v1",api_key="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")
import os
import subprocess
import uuid
from pathlib import Path
from PIL import Image
import shutil

def convert_tga_to_png(tga_path, png_path):
    with Image.open(tga_path) as img:
        img.save(png_path)




# Set your OpenAI key (or use environment variable)

# Request model
class PromptRequest(BaseModel):
    prompt: str

# Function: prompt to VMD Tcl script
def prompt_to_vmd_script(prompt: str) -> str:
    system_message = (
        "You are an expert in VMD Tcl scripting. Given a natural language prompt, "
        "convert it into a VMD Tcl script that assumes the structure has been loaded. "
        "Do not include loading commands unless asked."
    )
    completion = client.chat.completions.create(model="openai/gpt-4o",
    messages=[
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt}
    ])
    return completion.choices[0].message.content

# Function: run VMD script
def run_vmd_script(script: str, pdb_path: str) -> str:
    script_path = f"/tmp/vmd_script_{uuid.uuid4().hex}.tcl"
    img_path = script_path.replace(".tcl", ".tga")

    # Prepare script
    with open(script_path, "w") as f:
        f.write(f"mol new {pdb_path} type pdb\n")
        f.write(script + "\n")
        f.write(f'render TachyonInternal {img_path}\n')
        f.write("quit\n")

    # Run VMD in text mode
    subprocess.run(["/Applications/VMD.app/Contents/vmd/vmd_MACOSXARM64", "-dispdev", "text", "-e", script_path])

    # Convert image to PNG (optional, needs imagemagick)
    convert_tga_to_png(img_path,png_path)
    png_path = img_path.replace(".tga", ".png")
    #shutil.move(png_path,f'./vmd_agent.png')
    #subprocess.run(["convert", img_path, png_path])

    return png_path

# POST endpoint
async def vmd_run(prompt: str =Form(...), pdb_file: UploadFile = File(...)):
    # Save PDB file locally
    pdb_path = f"/tmp/{uuid.uuid4().hex}.pdb"
    with open(pdb_path, "wb") as f:
        f.write(await pdb_file.read())

    # Convert prompt to VMD script
    tcl_script = prompt_to_vmd_script(prompt)

    # Run VMD script and render
    image_path = run_vmd_script(tcl_script, pdb_path)

    return {
        "script": tcl_script,
        "image_path": image_path,
        "message": "VMD script executed and image generated."
    }

import streamlit as st
import requests
import os

st.set_page_config(page_title="VMD Visualizer", layout="centered")
st.title("🧬 Natural Language VMD Interface")

# Prompt input
prompt = st.text_input("Enter your visualization prompt:", placeholder="e.g. Show only chain A and color it red")

# File uploader
pdb_file = st.file_uploader("Upload a PDB file", type=["pdb"])

if st.button("Run VMD"):
    if prompt and pdb_file:
        
        files = {"pdb_file": (pdb_file.name, pdb_file.getvalue())}
        data = {"prompt": prompt}
        with st.spinner("Generating visualization..."):
            res = requests.post("http://localhost:8501/vmd/run", files=files, data=data)
        if res.status_code == 200:
            result = res.json()
            st.success("✅ VMD script executed!")
            # Download the image from FastAPI (if it's served as a static file)
            image_url = result["image_path"]
            print(image_url)
            img_response = requests.get(image_url)

            if img_response.status_code == 200:
                st.image(img_response.content, caption="Rendered Snapshot", use_column_width=True)
            else:
                st.warning("Image could not be loaded.")

    else:
        st.warning("Please provide both a prompt and a PDB file.")
