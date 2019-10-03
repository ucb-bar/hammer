Introduction to Hammer
===============================

Hammer (Higly Agile Masks Made Efforlessly from RTL) is a framework for building physical design generators for digital VLSI flows. It is an evolving set of APIs that enable reuse in an effort to speed up VLSI flows, which have traditionally been entirely rebuilt for different projects, technologies, and tools.

Hammer is able to generate scripts and collateral for a growing range of CAD tools while remaining technology-agnostic using a well-defined set of common APIs. Tool- and technology-specifi concerns live inside plugins, implement APIs, and provide a set of working default configurations.

The vision of Hammer is to turn it into a key driver of design space exploration, allowing a designer to rapidly explore many parameters such as timing constraints and floorplans with low-level concerns like power strap abutment completely abstracted away. Metrics extracted from each step of the flow are intended to be fed back to the design generator to promote fast convergence towards a high-performance chip. 
