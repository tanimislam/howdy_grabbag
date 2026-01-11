from setuptools import setup, find_packages
from shutil import which
#
## requirements are in "requirements.txt"
#
## fail hard if cannot find ffmpeg, ffprobe, mkvmerge, HandBrakeCLI
if which( 'ffmpeg' ) is None:
    raise ValueError("Error, cannot find necessary executable: ffmpeg" )
if which( 'ffprobe' ) is None:
    raise ValueError("Error, cannot find necessary executable: ffprobe" )
if which( 'mkvmerge' ) is None:
    raise ValueError("Error, cannot find necessary executable: mkvmerge" )
if which( 'HandBrakeCLI' ) is None:
    print( "Although would be nice to have, cannot find HandBrakeCLI. Cannot do transcoding of movies here." )

setup(
    name = 'howdy_grabbag',
    version = '1.0',
    #
    ## following advice on find_packages excluding tests from https://setuptools.readthedocs.io/en/latest/setuptools.html#using-find-packages
    packages = find_packages( exclude = ["*.tests", "*.tests.*", "tests" ] ),
    url = 'https://github.com/tanimislam/howdy_grabbag',
    license = 'BSD-2-Clause',
    author = 'Tanim Islam',
    author_email = 'tanim.islam@gmail.com',
    description = 'A Bunch of Additional Plex and Multimedia Utility Scripts',
    #
    ## classification: where in package space does "howdy live"?
    ## follow (poorly) advice I infer from https://blog.ionelmc.ro/2014/05/25/python-packaging/#the-setup-script
    classifiers=[
    # complete classifier list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Environment :: Console',
        'Programming Language :: Python :: 3',
    # uncomment if you test on these interpreters:
    # 'Programming Language :: Python :: Implementation :: IronPython',
    # 'Programming Language :: Python :: Implementation :: Jython',
    # 'Programming Language :: Python :: Implementation :: Stackless',
        'Topic :: Utilities',
        'Topic :: Multimedia',
    ],
    #
    ## requirements
    install_requires = [
        'tabulate',
        'mutagen',
        'howdy',
        'redis',
        'validators',
        'python-magic', ],
    python_requires = '>=3.8',
    #
    ## the executables I am creating
    entry_points = {
        'console_scripts' : [
            'convert_mp4movie_to_mkv  = howdy_grabbag.cli.convert_mp4movie_to_mkv:main',
            'convert_mp4tv_to_mkv     = howdy_grabbag.cli.convert_mp4tv_to_mkv:main',
            'dvd_to_mkv               = howdy_grabbag.cli.dvd_to_mkv:main',
            'rename_mkv_tv            = howdy_grabbag.cli.rename_mkv_tv:main',
            'howdy_music_compilation  = howdy_grabbag.cli.howdy_music:main_compilation',
            'howdy_music_individual   = howdy_grabbag.cli.howdy_music:main_individual',
            'howdy_music_add_spotify  = howdy_grabbag.cli.howdy_music_add_spotify:main',
            'fix_permissions          = howdy_grabbag.cli.fix_permissions:main',
            'dehydrate_tv_shows       = howdy_grabbag.cli.dehydrate_tv_shows:main',
            'deavify_tv_shows         = howdy_grabbag.cli.dehydrate_tv_shows:main_avis',
            'dehydrate_directory      = howdy_grabbag.cli.dehydrate_directory:main',
            'dehydrate_files          = howdy_grabbag.cli.dehydrate_directory:main_dehydrate_files',
            'lower_audio_directory    = howdy_grabbag.cli.dehydrate_directory:main_lower_audio',
            'list_directory           = howdy_grabbag.cli.dehydrate_directory:main_list',
            'subtitle_directory       = howdy_grabbag.cli.dehydrate_directory:main_subtitles',
            'spotify_add_and_fix      = howdy_grabbag.cli.spotify_add_and_fix:main',
            'spotify_fix_bad          = howdy_grabbag.cli.spotify_add_and_fix:main_fix_bad',
            'spotify_push_from_plex   = howdy_grabbag.cli.spotify_push_from_plex:main',
            ]
    },
)
