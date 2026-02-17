===============================================================================
 Howdy-GRABBAG - A Bunch of Additional Plex_ and Multimedia Utility Scripts
===============================================================================
This repository consists of a bunch of random utility scripts that use, or are associated with, Howdy_. Howdy_ is an SDK used to manage movies, television shows, and music located on a Plex_ server. Its relatively comprehensive documentation (missing documentation on two of its GUIs) lives in the `Howdy documentation page <https://tanimislam.github.io/howdy>`_.

This module depends explicitly on howdy_ and mutagen_. This module will not run without nice_, ffmpeg_, ffprobe_, mkvmerge_, mkvpropedit_, and HandBrakeCLI_.

Installing this software is unusual but straightforward. Just run this command using pip_ for Python 3,

.. code-block:: console

   python3 -m pip install --user --upgrade git+https://github.com/tanimislam/howdy_grabbag#egg=howdy_grabbag

You can also install them by downloading the repository from Github directly, then installing,

.. code-block:: console

   python3 -m pip install --user -e .

Currently, there are *nineteen* executables as part of ``howdy_grabbag``. The Sphinx documentation now documents each of the command line tools in this repository. We invite users to look in the Sphinx documentation for this project to understand how all these tools work.
   
.. And then these executables (`convert_mp4movie_to_mkv <convert_mp4movie_to_mkv_label_>`_ and `fix_permissions <fix_permissions_label_>`_ for now), will live in ``~/.local/bin``.

.. The documentation starts with a description of each command line tool in this README, and grows from there. As this repository evolves, the documentation *may* become more organized. Right now, it is what it is.
  
.. these are the links

.. _ffmpeg: https://ffmpeg.org/ffmpeg.html
.. _ffprobe: https://ffmpeg.org/ffprobe.html
.. _HandBrakeCLI: https://handbrake.fr/docs/en/latest/cli/cli-options.html
.. _mkvmerge: https://mkvtoolnix.download/doc/mkvmerge.html
.. _mkvpropedit: https://mkvtoolnix.download/doc/mkvpropedit.html
.. _nice: https://www.man7.org/linux/man-pages/man1/nice.1.html
.. _MP4: https://en.wikipedia.org/wiki/MPEG-4_Part_14
.. _MKV: https://en.wikipedia.org/wiki/Matroska
.. _mutagen: https://mutagen.readthedocs.io
.. _pip: https://pip.pypa.io
.. _Howdy: https://github.com/tanimislam/howdy
.. _Plex: https://plex.tv
.. _SRT: https://en.wikipedia.org/wiki/SubRip

.. |transform| replace:: ``transform``
