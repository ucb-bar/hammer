.. automodule:: gdsii.types

Defined members::

    NODATA = 0
    BITARRAY = 1
    INT2 = 2
    INT4 = 3
    REAL4 = 4
    REAL8 = 5
    ASCII = 6

Type :const:`REAL4` is not used in GDSII and not handled by `python-gdsii`.

Additionaly this module contains the following members:

    .. data:: DICT

        A dictionary that maps type names to type IDs.

    .. data:: REV_DICT
    
        A dictionary that maps type IDs to type names.
