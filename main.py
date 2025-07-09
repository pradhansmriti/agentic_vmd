from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
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



app = FastAPI()


#serve images from static
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Allow local dev requests (optional for Streamlit)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set your OpenAI key (or use environment variable)

# Request model
class PromptRequest(BaseModel):
    prompt: str

# Function: prompt to VMD Tcl script
def prompt_to_vmd_script(prompt: str) -> str:
    system_message = (
        "You are an expert in VMD Tcl scripting. Given a natural language prompt, "
        "convert it into a VMD Tcl script that assumes the structure has been loaded. "
        "Start with no representation (delrep)"
        "add new representation of selection from prompt."
        "Make the background display color always white with: color Display Background white"
        "Turn off axes and depth cueing"
        "when using coloring method use color codes in vmd by default."
        " Default color codes are 0:blue, 1:red, 2:gray 3:orange 4:yellow 5:tan 6:silver,"
        "7:Green 8:white 9:pink 10:cyan."
        "Make the default drwaing method VDW unless stated otherwise."
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
    png_path=img_path.replace(".tga",".png")
    final_path=f"static/vmd_{uuid.uuid4().hex}.png"

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
    shutil.move(png_path,final_path)
    #subprocess.run(["convert", img_path, png_path])

    return f"http://localhost:8000/{final_path}"

# POST endpoint
@app.post("/vmd/run")
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
"""""
import streamlit as st

st.title("LLM-Driven Molecular Viewer")

user_input = st.text_input("Describe your visualization task:")
if st.button("Run"):
    vmd_code = prompt_to_vmd_code(user_input, model="gpt-4")
    st.code(vmd_code, language="tcl")
    run_vmd_script(vmd_code)
"""
