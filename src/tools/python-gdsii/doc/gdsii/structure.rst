.. automodule:: gdsii.structure
    :synopsis: module containing GDSII structure class.

.. autoclass:: Structure
    :show-inheritance:

    .. automethod:: __init__

    Instance attributes:
        .. attribute:: name

            Structure name (:class:`bytes`).

        .. attribute:: mod_time

            Last modification time (:class:`datetime`).

        .. attribute:: acc_time

            Last access time (:class:`datetime`).

        .. attribute:: strclass

            Structure class (:class:`int`, optional).
