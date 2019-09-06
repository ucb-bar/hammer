Welcome to python-gdsii's documentation!
========================================

`python-gdsii` is a library that can be used to read, create, modify and save
GDSII files. It supports both low-level record I/O and high level interface to
GDSII libraries (databases), structures, and elements.

This package also includes scripts that can be used to convert binary GDS file
to a simple text format (`gds2txt`), YAML (`gds2yaml`), and from text format
back to GDSII (`txt2gds`).

Contents:

.. toctree::
   :maxdepth: 2

   gdsii/index

Download
--------

`python-gdsii` can be downloaded from its Python Package Index `page <http://pypi.python.org/pypi/python-gdsii/>`_.
The source code repository is available on `gitorious.org <http://gitorious.org/python-gdsii>`_.

Usage
-----

For most cases interface provided by Library class from gdsii.library should be
enough. Here is a small example::

    from gdsii.library import Library
    from gdsii.elements import *

    # read a library from a file
    with open('file.gds', 'rb') as stream:
        lib = Library.load(stream)

    # let's move the first structure to a new library
    new_lib = Library(5, b'NEWLIB.DB', 1e-9, 0.001)
    struc = lib.pop(0) # libraries and structures are derived from list class
    new_lib.append(struc)

    # let's also add some elements...
    # Note: first and last points in the boundary should be the same
    #       this is required by GDSII spec.
    struc.append(Boundary(45, 0, [(-100000, -100000), (-100000, 0), (0,0), (0, -100000), (-100000, -100000)]))

    # Save both files with different names...
    with open('newfile1.gds', 'wb') as stream:
        lib.save(stream)

    with open('newfile2.gds', 'wb') as stream:
        new_lib.save(stream)

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
