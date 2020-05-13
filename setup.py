from setuptools import setup, find_packages
#
## requirements are in "requirements.txt"

setup(
    name = 'plexstuff_grabbag',
    version = '1.0',
    #
    ## following advice on find_packages excluding tests from https://setuptools.readthedocs.io/en/latest/setuptools.html#using-find-packages
    packages = find_packages( exclude = ["*.tests", "*.tests.*", "tests" ] ),
    # package_dir = { "": "nprstuff" },
    url = 'https://github.com/tanimislam/plexstuff_grabbag',
    license = 'BSD-2-Clause',
    author = 'Tanim Islam',
    author_email = 'tanim.islam@gmail.com',
    description = 'A Bunch of Additional Plex and Multimedia Utility Scripts',
    #
    ## classification: where in package space does "plexstuff live"?
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
    install_requires = [ 'tabulate' ],
    dependency_links = [ 'git+https://github.org/tanimislam/plexstuff.git#egg=plexstuff' ],
    python_requires = '>=3',
    #
    ## the executables I am creating
    entry_points = {
        'console_scripts' : [
            'plex_config_excludes = plexstuff_grabbag.cli.plex_config_excludes:main',
            'convert_mp4movie_to_mkv = plexstuff_grabbag.cli.convert_mp4movie_to_mkv:main',
            ]
    },
)
