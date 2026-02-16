"""
This renames an MKV TV file, given TV show and season and epno, into an MKV with PLEX convention TV file name.

19-09-2020: rename all dependencies to howdy from plexstuff
12-05-2020: put into plexstuff_grabbag repo
20-10-2019: now can use HandBrakeCLI to convert the MP4 movie file to an MKV file that is smaller

Requires titlecase, mutagen
Requires executables: ffmpeg, mkvmerge, HandBrakeCLI
"""

import time, os, sys, titlecase, logging
from howdy.core import SSHUploadPaths
from howdy_grabbag.utils import get_rsync_commands_lowlevel, rsync_upload_mkv
from howdy.tv import tv_attic
from argparse import ArgumentParser

def rename_mkv_file(
    mkvtv, tvshow, seasno, epno,
    firstAiredYear = None, outdir = os.getcwd( ) ):
    #
    time0 = time.perf_counter( )
    assert( os.path.isfile( mkvtv ) )
    assert( any(map(lambda suffix: os.path.basename( mkvtv ).lower( ).endswith('.%s' %suffix ),
                    ( 'avi', 'mp4', 'mpg', 'mkv', 'webm' ) ) ) )
    actual_suffix = os.path.basename( mkvtv ).lower( ).split('.')[-1].strip( )
    #
    ## get the episode info first find the series
    epdicts = tv_attic.get_tot_epdict_tmdb(
        tvshow, showFuture = True, minmatch = 10.0, firstAiredYear = firstAiredYear )
    assert( epdicts is not None )
    assert( seasno in epdicts )
    assert( epno in epdicts[ seasno ] )
    epname = '; '.join(map(lambda tok: tok.strip(), epdicts[seasno][epno][0].split('/') ) )
    newfile = os.path.abspath(
        os.path.join(
            os.path.expanduser( outdir ),
            '%s - s%02de%02d - %s.%s' % ( tvshow, seasno, epno, epname, actual_suffix ) ) )
    os.rename( mkvtv, newfile )
    os.chmod( newfile, 0o644 )
    logging.info( 'created %s in %0.3f seconds.' % (
        os.path.realpath( newfile ), time.perf_counter( ) - time0 ) )
    return os.path.realpath( newfile )

def main( ):
    parser = ArgumentParser( )
    parser.add_argument( '-i', dest='inputmkv', type=str, action='store',
                       help = 'Name of the MKV TV file name.', required = True )
    parser.add_argument( '-S', '--series', dest='seriesName', type=str, action='store',
                       help = 'Name of the TV show.', required = True )
    parser.add_argument( '-e', '--epstring', dest='epstring', type=str, action='store',
                        help = 'The episode string, in the form S%%02dE%%02d.' )
    parser.add_argument( '-F', '--firstAiredYear', type=int, action='store',
                       help = 'Year in which the first episode of the TV show aired.' )
    #
    parser.add_argument(
        '-o', '--outdir', dest='outdir', action='store', type=str, default = os.getcwd( ),
        help = 'The directory into which we save the final MKV file. Default is %s.' % os.getcwd( ) )
    parser.add_argument(
        '--noinfo', dest='do_info', action='store_false', default = True,
        help = 'If chosen, then run with NO INFO logging (less debugging).' )
    #
    subparser = parser.add_subparsers(
        help = 'Option of transforming (using HandBrakeCLI) to smaller size MKV file.',
        dest = 'choose_option' )
    #
    ## SSH file to remote directory
    parser_ssh = subparser.add_parser(
        'ssh', help = 'Use the collection of remote media directory collections to upload final MKV movie to remote SSH server.' )
    parser_ssh.add_argument( '-A', '--alias', dest = 'ssh_alias', type = str, action = 'store', required = True,
                             help = 'The alias to identify the remote tv media directory collection, which contains movies.' )
    parser_ssh.add_argument( '-T', '--tvshow', dest = 'tvshow', type = str, action = 'store', default = None,
                             help = 'Optional name of the TV show directory into which to put the TV media file.' )
    #
    args = parser.parse_args( )
    #
    ## error checking
    assert( os.path.isdir( args.outdir ) )
    assert( os.path.isfile( args.inputmkv ) )
    assert( any(map(lambda suffix: os.path.basename( args.inputmkv ).lower( ).endswith('.%s' %suffix ),
                    ( 'avi', 'mp4', 'mpg', 'mkv', 'webm' ) ) ) )
    #
    ##
    logger = logging.getLogger( )
    if args.do_info: logger.setLevel( logging.INFO )
    #
    seasepstring = args.epstring.strip( ).upper( )
    if not seasepstring[0] == 'S':
        print( 'Error, first string must be an s or S.' )
        return
    seasepstring = seasepstring[1:]
    splitseaseps = seasepstring.split('E')[:2]
    if len( splitseaseps ) != 2:
        print( 'Error, string must have a SEASON and EPISODE part.' )
        return
    try:
        seasno = int( splitseaseps[0] )
    except:
        print( 'Error, invalid season number.' )
        return
    try:
        epno = int( splitseaseps[1] )
    except:
        print( 'Error, invalid episode number.' )
        return
    joblib_dict = {
        'mkvtv'  : args.inputmkv,
        'tvshow' : args.seriesName,
        'seasno' : seasno,
        'epno'   : epno,
        'outdir' : args.outdir,
        'do_ssh' : False }
    if args.choose_option == 'ssh':
        joblib_dict[ 'do_ssh' ] = True
        joblib_dict[ 'alias'  ] = args.ssh_alias
        tvshow = joblib_dict[ 'tvshow' ]
        if args.tvshow is not None: tvshow = args.tvshow
        #
        ## try this out first, check find alias
        data_init = get_rsync_commands_lowlevel(
            joblib_dict[ 'alias' ], tvshow, "", mediatype = SSHUploadPaths.MediaType.tv )
        print( data_init )
        if data_init is None:
            return
        valid_subdirs = sorted(filter(lambda subdir: get_rsync_commands_lowlevel(
            joblib_dict[ 'alias' ], subdir, "", mediatype = SSHUploadPaths.MediaType.tv ) is not None,
                                    set([ os.path.join( tvshow, 'Season %d' % seasno ),
                                          os.path.join( tvshow, 'Season %02d' % seasno ) ] ) ) )
        if len( valid_subdirs ) == 0:
            return
        joblib_dict[ 'subdir' ] = valid_subdirs[ 0 ]
    #
    #outputfile = rename_mkv_file(
    #    args.inputmkv, args.seriesName, seasno, epno,
    #    outdir = args.outdir )
    outputfile = rename_mkv_file(
        joblib_dict[ 'mkvtv'  ],
        joblib_dict[ 'tvshow' ],
        joblib_dict[ 'seasno' ],
        joblib_dict[ 'epno'   ],
        outdir = joblib_dict[ 'outdir' ] )
    if joblib_dict[ 'do_ssh' ]:
        mycmd, mxcmd = get_rsync_commands_lowlevel(
            joblib_dict[ 'alias' ],
            joblib_dict[ 'subdir' ],
            outputfile,
            mediatype = SSHUploadPaths.MediaType.tv )
        rsync_upload_mkv( mycmd, mxcmd, numtries = 10 )
