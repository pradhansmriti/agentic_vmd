mol new ./82a1125078f74ee08d14b76db27ef7c7.pdb type pdb
```tcl
# Set representation to hide everything initially
mol modselect 0 top "none"

# Select chain A and color it red
mol modselect 1 top "chain A"
mol modcolor 1 top ColorID 1  ;# Color ID 1 corresponds to red
mol modstyle 1 top NewCartoon ;# Set a style to make it visible
```
render TachyonInternal ./vmd_script_590b9d2ce7114790a53b9ed8fc554e43.tga
quit
