from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from openai import OpenAI
import os
client = OpenAI(base_url="https://openrouter.ai/api/v1",api_key=os.getenv("OPENAI_API_KEY"))
import os
import subprocess
import uuid
from pathlib import Path

app = FastAPI()

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
    script_path = f"./vmd_script_{uuid.uuid4().hex}.tcl"
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
    png_path = img_path.replace(".tga", ".png")
    #subprocess.run(["convert", img_path, png_path])

    return png_path

# POST endpoint
@app.post("/vmd/run")
async def vmd_run(prompt: str =Form(...), pdb_file: UploadFile = File(...)):
    # Save PDB file locally
    pdb_path = f"./{uuid.uuid4().hex}.pdb"
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
