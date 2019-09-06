.. automodule:: gdsii.library
    :synopsis: module containing GDSII library class.

.. autoclass:: Library
   :show-inheritance:

    .. automethod:: __init__

    Instance attributes:
        .. attribute:: version

            GDSII file verion (:class:`int`).
            Number as found in a GDSII file.
            For example value is 5 for GDSII v5 and 0x600 for GDSII v6.

        .. attribute:: name

            Library name (:class:`bytes`).

        .. attribute:: physical_unit

            Size of database unit in meters (:class:`float`).

        .. attribute:: logical_unit

            Size of user unit in database units (:class:`float`).

        .. attribute:: mod_time

            Last modification time (:class:`datetime`).

        .. attribute:: acc_time

            Last access time (:class:`datetime`).

        .. attribute:: libdirsize

            Number of pages in the library directory (:class:`int`, optional).

        .. attribute:: srfname

            Name of spacing rules file (:class:`bytes`, optional).

        .. attribute:: acls
            
            ACL data (:class:`list` of tuples ``(GID, UID, ACCESS)``, optional).

        .. attribute:: reflibs

            Names of reference libraries (:class:`bytes`, optional).
            See GDSII stream format documentation for format.

        .. attribute:: fonts

            Names of font definition files (:class:`bytes`, optional).
            The content is not parsed, see GDSII stream format documentation
            for format.

        .. attribute:: attrtable
            
            Name of attribute definition file (:class:`bytes`, optional).

        .. attribute:: generations

            Number of copies for deleted structures (:class:`int`, optional)

        .. attribute:: format

            Library format (:class:`int`, optional). Possible values:
                * 0 -- GDSII archive format
                * 1 -- GDSII filtered format
                * 2 -- EDSIII archive format
                * 3 -- EDSIII filtered format

        .. attribute:: masks

            Masks for filtered format (:class:`list` of :class:`bytes`, optional).

    .. automethod:: load

    .. automethod:: save
