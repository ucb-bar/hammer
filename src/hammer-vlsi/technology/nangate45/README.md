OpenROAD Nangate45 Technology Library
=====================================
This is the PDK that comes packaged with [OpenROAD-flow](https://github.com/The-OpenROAD-Project/OpenROAD-flow). Right now, it is only validated against the OpenROAD-flow backend of hammer. 

Dummy SRAMs
===========
The Nangate45 plugin comes with fake SRAMs without behavioral models or GDS files. 
They only have timing libs for the TT corner (same as the pdk's stcell lib).

Supported Vendors in the PDK
============================
Only the OpenROAD-flow tools are suported. see a diagram [here](https://github.com/The-OpenROAD-Project/OpenROAD-flow/tree/master/flow). some of the tools supported include:
- yosys (synthesis)
- RePlAce/Resizer (placement)
- TritonCTS (cts)
- TritonRoute (routing)
- magic (finishing/drc)

Known DRC Issues
=================
TODO: there are several. need to document them
