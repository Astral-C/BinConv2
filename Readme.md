# BinConvert
A basic wavefront obj to bin converter for Luigi's Mansion.

## Usage
`python binconv.py -i in.obj -o out.bin`

## Quick FAQ

### Where is the precompiled exe?
On the releases page.

### I converted a model and there is only one texture?
Make sure that the model you are converting is split by material.

## Modified Bindings
This converter requires slightly modified versions of python bindings for libsquish and tinyobjloader, as such the needed modifications are included under the bindings directory. Simply clone tinyobjloader and [this version of libsquish](https://github.com/tito/libsquish), replace the proper files, and build as normal.
