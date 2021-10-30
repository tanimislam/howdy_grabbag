===============================================================================
 Howdy-GRABBAG - A Bunch of Additional Plex_ and Multimedia Utility Scripts
===============================================================================
This repository consists of a bunch of random utility scripts that use, or are associated with, Howdy_. Howdy_ is an SDK used to manage movies, television shows, and music located on a Plex_ server. Its relatively comprehensive documentation (missing documentation on two of its GUIs) lives in `howdy.readthedocs.io`_.

This module depends explicitly on howdy_ and mutagen_. This module will not install and run without ffmpeg_, ffprobe_, and mkvmerge_. This module will install without HandBrakeCLI_, but with reduced functionality -- no transcoding in convert_mp4movie_to_mkv_.

Installing this software is unusual but straightforward. Just run this command, using ``pip3`` (pip_ for Python 3),

.. code-block:: console

   pip3 install --user --upgrade git+https://github.com/tanimislam/howdy_grabbag#egg=howdy_grabbag

And then these executables (`convert_mp4movie_to_mkv <convert_mp4movie_to_mkv_label_>`_ for now), will live in ``~/.local/bin``.

The documentation starts with a description of each command line tool in this README, and grows from there. As this repository evolves, the documentation *may* become more organized. Right now, it is what it is.

.. _convert_mp4movie_to_mkv_label:

convert_mp4movie_to_mkv
^^^^^^^^^^^^^^^^^^^^^^^^
This converts an MP4_ movie file, with optional SRT_ English subtitle file, into an MKV_ movie file with appropriate metadata -- movie title and release year -- with an SRT_ English subtitle as a stream. Optionally, this executable can also transcode the larger MP4_ file into an MKV_ file with much smaller size but with no noticeable loss in video quality; it uses HandBrakeCLI_ for that functionality.  The help output, when running ``convert_mp4movie_to_mkv -h``, produces the top level help,

.. code-block:: console

   usage: convert_mp4movie_to_mkv [-h] --mp4 MP4 [--srt SRT] -n NAME -y YEAR
				  [--outdir OUTDIR] [--keep] [--noinfo]
				  {transform} ...

   positional arguments:
     {transform}           Option of transforming (using HandBrakeCLI) to smaller
			   size MKV file.
       transform           Use HandBrakeCLI to transform to different quality MKV
			   movie. Objective is to reduce size.

   optional arguments:
     -h, --help            show this help message and exit
     --mp4 MP4             Name of the MP4 movie file name.
     --srt SRT             Name of the SRT subtitle file associated with the
			   movie.
     -n NAME, --name NAME  Name of the movie.
     -y YEAR, --year YEAR  Year in which the movie was aired.
     --outdir OUTDIR       The directory into which we save the final MKV file.
			   Default is /home1/tanimislam/.local/src/howdy_grabbag.
     --keep                If chosen, then KEEP the MP4 and SRT files.
     --noinfo              If chosen, then run with NO INFO logging (less
			   debugging).

In normal operation, |convert_mp4movie_to_mkv| losslessly converts an MP4_ movie file, and where possible includes an SRT_ file, into an MKV_ movie file. It requires the ``--mp4`` argument (name of the movie file); the ``-n`` or ``--name`` (name of the released movie) argument; and the ``-y`` or ``--year`` (year in which the movie was released) argument. Here are what the following optional arguments do,

* ``--srt`` includes an SRT_ English subtitle file into the final MKV_ movie file.

* ``--keep`` will *NOT* delete the input MP4_ or SRT_ files.

* ``--noinfo`` operates with less debugging info.

* ``--outdir`` can be used to set the *output directory* into which the MKV_ movie file goes. You can give it a ``~`` prefixed path.

Finally, the |transform| option will transcode the movie, using HandBrakeCLI_, to a specific psychovisual quality. This is the help output in this mode, when running ``convert_mp4movie_to_mkv transform -h``,

.. code-block:: console

   usage: convert_mp4movie_to_mkv transform [-h] [-q QUALITY]

   optional arguments:
     -h, --help            show this help message and exit
     -q QUALITY, --quality QUALITY
			   The quality of the conversion that HandBrakeCLI uses. Default is 26.

The default quality is 26. Higher numbers means smaller files but lower video quality, and lower numbers mean larger files (in some cases, can be larger in size than the input file) but generally higher video quality.

fix_permissions
^^^^^^^^^^^^^^^^^^^^^^^^
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
  
.. these are the links

.. _ffmpeg: https://ffmpeg.org/ffmpeg.html
.. _ffprobe: https://ffmpeg.org/ffprobe.html
.. _HandBrakeCLI: https://handbrake.fr/docs/en/latest/cli/cli-options.html
.. _mkvmerge: https://mkvtoolnix.download/doc/mkvmerge.html
.. _MP4: https://en.wikipedia.org/wiki/MPEG-4_Part_14
.. _MKV: https://en.wikipedia.org/wiki/Matroska
.. _mutagen: https://mutagen.readthedocs.io
.. _pip: https://pip.pypa.io
.. _Howdy: https://github.com/tanimislam/howdy
.. _Plex: https://plex.tv
.. _SRT: https://en.wikipedia.org/wiki/SubRip
.. _`howdy.readthedocs.io`: https://howdy.readthedocs.io

.. |transform| replace:: ``transform``
.. |convert_mp4movie_to_mkv| replace:: ``convert_mp4movie_to_mkv``
