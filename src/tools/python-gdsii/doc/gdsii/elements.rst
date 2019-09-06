.. automodule:: gdsii.elements
    :synopsis: module containing classes for GDSII elements.

Possible instance attributes:

    :attr:`elflags`
        Element flags (:class:`int`, optional).
        Bit 15 specifies template data.
        Bit 14 specifies external data.
    :attr:`plex`
        Plex number (:class:`int`, optional).
    :attr:`layer`
        Element layer (:class:`int`)
    :attr:`data_type`
        Element data type (:class:`int`)
    :attr:`path_type`
        Type of path endpoints (:class:`int`, optional).
        The values have the following meaning:

        * 0 -- square ends, flush with endpoints
        * 1 -- round ends, centered on endpoints
        * 2 -- square ends, centered on endpoints
        * 4 -- custom square ends
    :attr:`width`
        Width of the path (:class:`int`, optional). If the value is negative,
        then the width is absolute and not affected by magnification factor.
    :attr:`bgn_extn`, :attr:`end_extn`
        Start end end extensions for :attr:`path_type` 4 (:class:`int`, optional).
    :attr:`xy`
        List of points (:class:`list` of tuples ``(x, y)``).
    :attr:`struct_name`
        Name of the referenced structure (:class:`bytes`).
    :attr:`strans`
        Transformation flags (:class:`int`, optional). Bits have the following meaning:

        * 0 -- reclection about X axis
        * 13 -- absolute magnification
        * 14 -- absolute angle
    :attr:`mag`
        Magnification factor (:class:`float`, optional).
    :attr:`angle`
        Rotation factor in degrees (:class:`float`, optional). Rotation is counterclockwise.
    :attr:`cols`
        Number of columns (:class:`int`).
    :attr:`rows`
        Number of rows (:class:`int`).
    :attr:`text_type`
        Text type (:class:`int`).
    :attr:`presentation`
        Bit array that specifies how the text is presented (:class:`int`, optional).
        Meaning of bits:

        * Bits 10 and 11 specify font number (0-3).
        * Bits 12 and 13 specify vertical justification (0 -- top, 1 -- middle, 2 -- bottom).
        * Bits 14 and 15 specify horizontal justification (0 -- left, 1 -- center, 2 -- rigth).
    :attr:`string`
        String for :const:`TEXT` element (:class:`bytes`).
    :attr:`node_type`
        Node type (:class:`int`).
    :attr:`box_type`
        Box type (:class:`int`).
    :attr:`properties`
        Element properties, represented as a list of tupes (`propattr`, `propvalue`).
        `propattr` is an :class:`int`, `propvalue` is :class:`bytes`.
        This attribute is optional.

.. autoclass:: ARef
    
    Required attributes: :attr:`struct_name`, :attr:`cols`, :attr:`rows`, :attr:`xy`.

    Optional attributes: :attr:`elflags`, :attr:`plex`, :attr:`strans`, :attr:`mag`,
    :attr:`angle`, :attr:`properties`.

.. autoclass:: Boundary

    Required attributes: :attr:`layer`, :attr:`data_type`, :attr:`xy`.

    Optional attributes: :attr:`elflags`, :attr:`plex`, :attr:`properties`.

.. autoclass:: Box
    
    Required attributes: :attr:`layer`, :attr:`box_type`, :attr:`xy`.

    Optional attributes: :attr:`elflags`, :attr:`plex`, :attr:`properties`.

.. autoclass:: Node

    Required attributes: :attr:`layer`, :attr:`node_type`, :attr:`xy`

    Optional attributes: :attr:`elflags`, :attr:`plex`, :attr:`properties`

.. autoclass:: Path

    Required attributes: :attr:`layer`, :attr:`data_type`, :attr:`xy`

    Optional attributes: :attr:`elflags`, :attr:`plex`, :attr:`path_type`,
    :attr:`width`, :attr:`bgn_extn`, :attr:`end_extn`, :attr:`properties`

.. autoclass:: SRef

    Required attributes: :attr:`struct_name`, :attr:`xy`

    Optional attributes: :attr:`elflags`, :attr:`strans`, :attr:`mag`,
    :attr:`angle`, :attr:`properties`

.. autoclass:: Text

    Required attributes: :attr:`layer`, :attr:`text_type`, :attr:`xy`, :attr:`string`

    Optional attributes: :attr:`elflags`, :attr:`plex`, :attr:`presentation`,
    :attr:`path_type`, :attr:`width`, :attr:`strans`, :attr:`mag`, :attr:`angle`, :attr:`properties`
