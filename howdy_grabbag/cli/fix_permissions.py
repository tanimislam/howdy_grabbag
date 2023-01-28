"""
This goes through a directory and ``chmod`` all the directories in it to ``755``, and ``chmod`` all the files in it to ``644``.

28-10-2021: first iteration
27-01-2023: second iteration. Working?
"""

import os, sys, time, logging, pathlib
from pathlib import Path
from pwd import getpwnam
from grp import getgrnam
from argparse import ArgumentParser

def fix_permissions( topdir, username, groupname ):
    time0 = time.perf_counter( )
    assert( os.path.isdir( os.path.abspath( topdir ) ) )
    try:
        uid = getpwnam( username ).pw_uid
        gid = getgrnam( groupname).gr_gid
    except Exception as e:
        print( "ERROR, PROBLEM WITH FINDING USER = %s, GROUP = %s." % (
            username, groupname ) )
        print( "REAL EXCEPTION: %s." % str( e ) )
        return
    #
    def set_perms_dir( dpath ):
        dpath.chmod( 0o755 )
        os.chown( os.path.abspath( dpath ), uid, gid )
    def set_perms_file( fpath ):
        fpath.chmod( 0o644 )
        os.chown( os.path.abspath( fpath ), uid, gid )
    #
    topDirPath = pathlib.Path( topdir )
    fpaths = list(filter(lambda pth: pth.is_file( ), topDirPath.rglob( '*' ) ) )
    dpaths = list(filter(lambda pth: pth.is_dir( ),  topDirPath.rglob( '*' ) ) )
    _ = list(map( set_perms_dir, dpaths ) )
    _ = list(map( set_perms_file, fpaths ) )
    logging.info( 'TOOK %0.3f SECONDS TO CHANGE OWNERSHIP OF %d FILES and %d DIRECTORIES IN %s TOP LEVEL DIRECTORY TO USER = %s AND GROUP = %s.' % (
        time.perf_counter( ), len( fpaths ), len( dpaths ), username, groupname ) )

def main( ):
    parser = ArgumentParser( )
    parser.add_argument( '-d', '--dir', dest='dir', type=str, action='store', default = os.getcwd( ),
                        help = 'Name for the directory under which to fix permissions. Default is %s.' %
                        os.getcwd( ) )
    parser.add_argument( '-u', '--user', dest = 'username', type = str, action = 'store', default = os.getlogin( ),
                        help = "Change the ownership to THIS user. Default is %s." % os.getlogin( ) )
    parser.add_argument( '-g', '--group', dest = 'groupname', type = str, action = 'store', default = os.getlogin( ),
                        help = "Change the ownership to THIS group. Default is %s." % os.getlogin( ) )
    parser.add_argument( '-i', '--info', dest = 'do_info', action = 'store_true', default = False,
                        help = 'If chosen, then run with INFO logging messages.' )
    args = parser.parse_args( )
    #
    logger = logging.getLogger( )
    if args.do_info: logger.setLevel( logging.INFO )
    #
    dirname = os.path.expanduser( args.dir )
    assert( os.path.isdir( os.path.abspath( dirname ) ) )
    fix_permissions( dirname, username = args.username, groupname = args.groupname )
