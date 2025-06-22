mol new ./345417e6a1b347c78941ceb4b6d1d82e.pdb type pdb
```tcl
# Hide all representations
display update off
mol modselect 0 top all
mol modstyle 0 top lines
mol modcolor 0 top ColorID 0
mol modselect 0 top none

# Create a new representation for chain A and color it red
mol addrep top
mol modselect 1 top "chain A"
mol modstyle 1 top lines
mol modcolor 1 top ColorID 1
display update on
```
render TachyonInternal ./vmd_script_b793c0f0bf5245928b690ceed01c6e75.tga
quit
