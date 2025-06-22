mol new ./806ad2cf940e4428b2f26ce229a3a5ad.pdb type pdb
```tcl
# Hide everything initially
display resetview
# Hide all atoms
mol representation Lines
mol selection all
mol material Transparent
mol color Name
mol addrep 0

# Show and color chain A in red
mol representation Licorice
mol selection "chain A"
mol material Opaque
mol color ColorID 1
mol addrep 0
```
render TachyonInternal ./vmd_script_7aa1baa1352c45bf8849a65388d846c2.tga
quit
