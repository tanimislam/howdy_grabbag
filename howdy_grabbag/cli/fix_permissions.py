"""
This goes through a directory and ``chmod`` all the directories in it to ``755``, and ``chmod`` all the files in it to ``644``.

28-10-2021: first iteration
"""

import os, sys, numpy, pathlib
from argparse import ArgumentParser

def fix_permissions( dirname ):
    assert( os.path.isdir( dirname ) )
    path = pathlib.Path( dirname )
    for fpath in filter(lambda pth: pth.is_file( ), path.rglob('*')):
        fpath.chmod( 0o644 )
    for dpath in filter(lambda pth: pth.is_dir( ), path.rglob('*')):
        fpath.chmod( 0o755 )

def main( ):
    parser = ArgumentParser( )
    parser.add_argument('-d', '--dir', dest='dir', type=str, action='store', default = os.getcwd( ),
                        help = 'Name fo the directory under which to fix permissions. Default is %s.' %
                        os.getcwd( ) )
    args = parser.parse_args( )
    dirname = os.path.expanduser( args.dir )
    assert( os.path.isdir( dirname ) )
    fix_permissions( dirname )
