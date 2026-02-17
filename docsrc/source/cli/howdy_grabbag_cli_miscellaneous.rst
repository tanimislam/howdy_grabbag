.. include:: ../common.rst

.. _miscellaneous_utilities:

MISCELLANEOUS UTILITIES
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _fix_permissions_label:

fix_permissions
+++++++++++++++++
I constantly run these commands to ``chmod 755` the subdirectories and ``chmod 644`` the files within a root directory.

* Here is the command to ``chmod 755` all the subdirectories at ``<root_directory>`` and underneath it.

  .. code-block:: console

     find <root_directory> -type d -exec chmod 755 '{}' +

* Here is the command to ``chmod 644`` all the files at ``<root_directory>`` and underneath it.

  .. code-block:: console

     find <root_directory> -type f -exec chmod 644 '{}' +

To make my life easier, I wrote up this executable. The help output, when running ``fix_permissions -h``, produces the following.

.. code-block:: console

   usage: fix_permissions [-h] [-d DIR]

   optional arguments:
     -h, --help         show this help message and exit
     -d DIR, --dir DIR  Name for the directory under which to fix permissions. Default is <default_directory>.

And that's it.
