from setuptools import setup, find_packages
from distutils.spawn import find_executable
#
## requirements are in "requirements.txt"
#
## fail hard if cannot find ffmpeg, ffprobe
if find_executable( 'ffmpeg' ) is None:
    raise ValueError("Error, cannot find necessary executable: ffmpeg" )
if find_executable( 'ffprobe' ) is None:
    raise ValueError("Error, cannot find necessary executable: ffprobe" )
if find_executable( 'mkvmerge' ) is None:
    raise ValueError("Error, cannot find necessary executable: mkvmerge" )
if find_executable( 'HandBrakeCLI' ) is None:
    print( "Although would be nice to have, cannot find HandBrakeCLI. Cannot do transcoding of movies here." )

setup(
    name = 'howdy_grabbag',
    version = '1.0',
    #
    ## following advice on find_packages excluding tests from https://setuptools.readthedocs.io/en/latest/setuptools.html#using-find-packages
    packages = find_packages( exclude = ["*.tests", "*.tests.*", "tests" ] ),
    # package_dir = { "": "nprstuff" },
    url = 'https://github.com/tanimislam/howdy_grabbag',
    license = 'BSD-2-Clause',
    author = 'Tanim Islam',
    author_email = 'tanim.islam@gmail.com',
    description = 'A Bunch of Additional Plex and Multimedia Utility Scripts',
    #
    ## classification: where in package space does "howdy live"?
    ## follow (poorly) advice I infer from https://blog.ionelmc.ro/2014/05/25/python-packaging/#the-setup-script
    classifiers=[
    # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
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
        'howdy @ git+https://github.com/tanimislam/howdy.git@master' ],
    python_requires = '>=3.5',
    #
    ## the executables I am creating
    entry_points = {
        'console_scripts' : [
            'convert_mp4movie_to_mkv = howdy_grabbag.cli.convert_mp4movie_to_mkv:main',
            ]
    },
)
