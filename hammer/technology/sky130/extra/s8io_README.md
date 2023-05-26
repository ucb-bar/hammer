# s8io Library

The IO ring can be created in Innovus using the NDA s8iom0s8 IO cell library. Here are the steps to use it:

1. `efabless_template.io` is a template IO file. You should modify this by replacing the `<inst_path>` with the path to the IO cell instances in your netlist. **DO NOT MODIFY THE POSITIONS OF THE CELLS OR REPLACE CLAMP CELLS WITH IO CELLS**

2. Then, in your design yml file, specify your IO file with:

    technology.sky130.io_file: <path/to/ring.io>
    technology.sky130.io_file_meta: prependlocal

3. The size of your toplevel should be exactly the following:

    path: Top
    type: toplevel
    x: 0
    y: 0
    width: 3588
    height: 5188
    margins:
      left: 200.1
      right: 200.1
      top: 201.28
      bottom: 201.28

4. In your CLIDriver, you must import the following hook from the tech plugin and insert is as a `post_insertion_hook` after `floorplan_design`.

    from hammer.technology.sky130 import efabless_ring_io

5. Refer [this documentation](https://skywater-pdk.readthedocs.io/en/main/contents/libraries/sky130_fd_io/docs/user_guide.html) for how to configure the pins of the GPIOs (not exhaustive).
