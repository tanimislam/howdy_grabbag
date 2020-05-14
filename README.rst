###############################################################################
Plexstuff-GRABBAG - A Bunch of Additional Plex and Multimedia Utility Scripts
###############################################################################
This repository consists of a bunch of random utility scripts that use, or are associated with, plexstuff_. plexstuff_ is an SDK used to manage movies, television shows, and music located on a Plex_ server. Its relatively comprehensive documentation (missing documentation on its GUIs) lives in `https://plexstuff.readthedocs.io`.

This module depends explicitly on plexstuff_, tabulate_, and mutagen_. This module will not install and run without ffmpeg_, ffprobe_, and mkvmerge_. This module will install without HandBrakeCLI_, but with reduced functionality -- no transcoding in convert_mp4movie_to_mkv_.

Installing this software is unusual but straightforward. Just run this command, using ``pip3`` (pip_ for Python 3),

.. code-block:: bash

   pip3 install --user --upgrade git+https://github.com/tanimislam/plexstuff_grabbag#egg=plexstuff_grabbag

And then these executables, plex_config_excludes_ and convert_mp4move_to_mkv, will live in ``~/.local/bin``.

The documentation starts with a description of each command line tool in this README, and grows from there. As this repository evolves, the documentation *may* become more organized. Right now, it is what it is.

.. _plex_config_excludes:

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

.._convert_mp4movie_to_mkv:

convert_mp4movie_to_mkv
========================

This converts an MP4_ movie file, with optional SRT_ English subtitle file, into an MKV_ movie file with appropriate metadata -- movie title and release year -- with an SRT_ English subtitle as a stream. Optionally, this executable can also transcode the larger MP4_ file into an MKV_ file with much smaller size but with no noticeable loss in video quality; it uses HandBrakeCLI_ for that functionality.  The help output, when running `convert_mp4movie_to_mkv -h`, produces the top level help,

.. code-block:: bash

   usage: convert_mp4movie_to_mkv [-h] --mp4 MP4 [--srt SRT] -n NAME -y YEAR [--keep] [--noinfo] {transform} ...

   positional arguments:
     {transform}           Option of transforming (using HandBrakeCLI) to smaller size MKV file.
       transform           Use HandBrakeCLI to transform to different quality MKV movie. Objective is to reduce size.

   optional arguments:
     -h, --help            show this help message and exit
     --mp4 MP4             Name of the MP4 movie file name.
     --srt SRT             Name of the SRT subtitle file associated with the movie.
     -n NAME, --name NAME  Name of the movie.
     -y YEAR, --year YEAR  Year in which the movie was aired.
     --keep                If chosen, then KEEP the MP4 and SRT files.
     --noinfo              If chosen, then run with NO INFO logging (less debugging).

In normal operation, ``convert_mp4movie_to_mkv`` losslessly converts an MP4_ movie file, and where possible includes an SRT_ file, into an MKV_ movie file. It requires the ``--mp4`` argument (name of the movie file); the `-n`` or ``--name`` (name of the released movie) argument; and the ``-y`` or ``--year`` (year in which the movie was released) argument. Here are what the following optional arguments do,

* ``--srt`` includes an SRT_ English subtitle file into the final MKV_ movie file.

* ``--keep`` will *NOT* delete the input MP4_ or SRT_ files.

* ``--noinfo`` operates with less debugging info.

Finally, the ``transform`` option will transcode the movie, using HandBrakeCLI_, to a specific psychovisual quality. The help output in this mode, when running ``convert_mp4movie_to_mkv transform -h``, produces this help,

.. code-block:: bash

   usage: convert_mp4movie_to_mkv transform [-h] [-q QUALITY]

   optional arguments:
     -h, --help            show this help message and exit
     -q QUALITY, --quality QUALITY
			   The quality of the conversion that HandBrakeCLI uses. Default is 26.

The default quality is 26. Higher numbers means smaller files but lower video quality, and lower numbers mean larger files (in some cases, can be larger in size than the input file) but generally higher video quality.
			   
.. these are the links

.. _ffmpeg: https://ffmpeg.org/ffmpeg.html
.. _ffprobe: https://ffmpeg.org/ffprobe.html
.. _HandBrakeCLI: https://handbrake.fr/docs/en/latest/cli/cli-options.html
.. _mkvmerge: https://mkvtoolnix.download/doc/mkvmerge.html
.. _MP4: https://en.wikipedia.org/wiki/MPEG-4_Part_14
.. _MKV: https://en.wikipedia.org/wiki/Matroska
.. _mutagen: https://mutagen.readthedocs.io
.. _pip: https://pip.pypa.io
.. _plexstuff: https://github.com/tanimislam/plexstuff
.. _Plex: https://plex.tv
.. _SRT: https://en.wikipedia.org/wiki/SubRip
.. _tabulate: https://github.com/astanin/python-tabulate
.. _gpb: https://plexstuff.readthedocs.io/plex-tvdb/cli_tools/plex_tvdb_cli.html?highlight=get_plextvdb_batch#get-plextvdb-batch
.. _`Lip Sync Battle`: https://www.imdb.com/title/tt4335742
.. _`SpongeBob SquarePants`: https://www.imdb.com/title/tt0206512
.. _`Reno 911!`: https://www.imdb.com/title/tt0370194
