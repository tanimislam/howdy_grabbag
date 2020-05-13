###############################################################################
Plexstuff-GRABBAG - A Bunch of Additional Plex and Multimedia Utility Scripts
###############################################################################
This repository consists of a bunch of random utility scripts that use, or are associated with, plexstuff_. plexstuff_ is an SDK used to manage movies, television shows, and music located on a Plex_ server. Its relatively comprehensive documentation (missing documentation on its GUIs) lives in `https://plexstuff.readthedocs.io`. This tool depends explicitly on plexstuff_ and tabulate_ only.

The documentation starts with a description of each command line tool in this README, and grows from there. As this repository evolves, the documentation *may* become more organized. Right now, it is what it is.

plex_config_excludes
======================
This CLI can determine, and change, the set of TV shows to exclude from regular update (using the CLI, `get_plextvdb_batch <gpb_>`_). This can only include TV shows that exist on the Plex_ server. The help output, when running `plex_config_excludes -h`, produces the top level help. It has two operations: ``show`` (which shows the TV shows to be excluded), and ``exclude`` (where the user specifies which shows to exclude).

.. code-block:: bash

   usage: plex_config_excludes [-h] [--remote] [--noverify] [-L LIBRARY] {show,exclude} ...

   positional arguments:
     {show,exclude}        Either show or exclude shows.
       show                Show those TV shows that have been excluded.
       exclude             Exclude a new list of TV shows.

   optional arguments:
     -h, --help            show this help message and exit
     --remote              If chosen, do not check localhost for running plex server.
     --noverify            If chosen, do not verify SSL connections.
     -L LIBRARY, --library LIBRARY
			   If named, then choose this as the TV library through which to look. Otherwise, look for first TV library found on Plex server.

Default flags are the following:

* ``--remote`` says to look for a *remote* Plex server rather than ``localhost``.

* ``--noverify`` means to not verify SSL connections.

* ``-L`` or ``--library`` is used to explicitly specify the TV library. If not chosen, then first available TV library is chosen in the Plex_ server. If a TV library cannot be found, then **exit**.

In ``show`` mode, for example, this is how it looks. Here, we use the default TV library.

.. code-block:: bash

   tanim-desktop: torrents $ plex_config_excludes show
   found 256 TV shows in Plex server.
   found 2 / 256 TV shows that are excluded from update.

   SHOW
   ---------------------
   Lip Sync Battle
   SpongeBob SquarePants

In ``exclude`` mode, for example, this is how it looks when we choose to exclude `Lip Sync Battle`_, `SpongeBob SquarePants`_, and `Reno 911!`_ from update. Here, we use the default TV library.

.. code-block:: bash

   tanim-desktop: torrents $ plex_config_excludes exclude "Lip Sync Battle" "SpongeBob SquarePants" "Reno 911!"
   found 256 TV shows in Plex server.
   Originally 2 shows to exclude. Now 3 shows to exclude.

   ORIGINAL               NEW
   ---------------------  ---------------------
   Lip Sync Battle        Lip Sync Battle
   SpongeBob SquarePants  Reno 911!
			  SpongeBob SquarePants

   PERFORM OPERATION (must choose one) [y/n]:y
   found 3 shows to exclude from TV database.
   had to remove 2 excluded shows from DB that were not in TV library.
   adding 3 extra shows to exclusion database.
   NEW EXCLUDED SHOWS ADDED

Running ``plex_config_excludes show`` will display, in this instance, those three shows instead of the original two.

convert_mp4move_to_mkv
========================

.. note:: IN PROGRESS

.. these are the links
   
.. _plexstuff: https://github.com/tanimislam/plexstuff
.. _Plex: https://plex.tv
.. _tabulate: https://github.com/astanin/python-tabulate
.. _gpb: https://plexstuff.readthedocs.io/plex-tvdb/cli_tools/plex_tvdb_cli.html?highlight=get_plextvdb_batch#get-plextvdb-batch
.. _`Lip Sync Battle`: https://www.imdb.com/title/tt4335742
.. _`SpongeBob SquarePants`: https://www.imdb.com/title/tt0206512
.. _`Reno 911!`: https://www.imdb.com/title/tt0370194
