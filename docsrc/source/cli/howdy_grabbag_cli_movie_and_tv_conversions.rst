.. include:: ../common.rst

.. _movie_and_tv_conversions_utilities:

MOVIE AND TV CONVERSION UTILITIES
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _convert_mp4movie_to_mkv_label:

convert_mp4movie_to_mkv
++++++++++++++++++++++++++++++
This converts an MP4_ movie file, with optional SRT_ English subtitle file, into an MKV_ movie file with appropriate metadata -- movie title and release year -- with an SRT_ English subtitle as a stream. Optionally, this executable can also transcode the larger MP4_ file into an MKV_ file with much smaller size but with no noticeable loss in video quality; it uses HandBrakeCLI_ for that functionality.

``convert_mp4movie_to_mkv -h`` produces this top level help,

.. code-block:: console

   usage: convert_mp4movie_to_mkv [-h] -M MP4 [-S SRT] -n NAME -y YEAR [-L LANG] [-o OUTDIR] [--keep] [--noinfo] {transform,ssh} ...

   positional arguments:
     {transform,ssh}       Option of transforming (using HandBrakeCLI) to smaller size MKV file.
       transform           Use HandBrakeCLI to transform to different quality MKV movie. Objective is to reduce size.
       ssh                 Use the collection of remote media directory collections to upload final MKV movie to remote SSH server.

   options:
     -h, --help            show this help message and exit
     -M MP4, --mp4 MP4     Name of the MP4 movie file name.
     -S SRT, --srt SRT     Name of the SRT subtitle file associated with the movie.
     -n NAME, --name NAME  Name of the movie.
     -y YEAR, --year YEAR  Year in which the movie was aired.
     -L LANG, --lang LANG  Optional argument, specify the language of the audio track.
     -o OUTDIR, --outdir OUTDIR
			   The directory into which we save the final MKV file. Default is /mnt/software/sources/pythonics/howdy_grabbag/docsrc.
     --keep                If chosen, then KEEP the MP4 and SRT files.
     --noinfo              If chosen, then run with NO INFO logging (less debugging).


In normal operation, this losslessly converts an MP4_ movie file, and where possible includes an SRT_ file, into an MKV_ movie file. It requires these arguments:

* ``-M`` or ``--mp4`` argument (name of the movie file).

* ``-n`` or ``--name`` (name of the released movie) argument.

* ``-y`` or ``--year`` (year in which the movie was released) argument.

Here are what the following optional arguments do,

* ``-S`` or ``--srt`` includes an SRT_ English subtitle file into the final MKV_ movie file.

* ``--keep`` will *NOT* delete the input MP4_ or SRT_ files.

* ``--noinfo`` operates with less debugging info.

* ``--outdir`` can be used to set the *output directory* into which the MKV_ movie file goes. You can give it a ``~`` prefixed path.

* ``-L`` or ``--lang`` specifies the (optional) `ISO 639 <https://en.wikipedia.org/wiki/ISO_639>`_ language code for the audio track, for example ``en`` for English. If you do not specify this argument, then the audio track language is undefined.

The ``transform`` option will transcode the movie, using HandBrakeCLI_, to a specific psychovisual quality. This is the help output in this mode, when running ``convert_mp4movie_to_mkv transform -h``,

.. code-block:: console

   usage: convert_mp4movie_to_mkv transform [-h] [-q QUALITY]

   optional arguments:
     -h, --help            show this help message and exit
     -q QUALITY, --quality QUALITY
			   The quality of the conversion that HandBrakeCLI uses. Default is 26.

The default quality is 26. Higher numbers means smaller files but lower video quality, and lower numbers mean larger files (in some cases, can be larger in size than the input file) but generally higher video quality.
