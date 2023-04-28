"""
This renames an MKV TV file, given TV show and season and epno, into an MKV with PLEX convention TV file name.

19-09-2020: rename all dependencies to howdy from plexstuff
12-05-2020: put into plexstuff_grabbag repo
20-10-2019: now can use HandBrakeCLI to convert the MP4 movie file to an MKV file that is smaller

Requires titlecase, mutagen
Requires executables: ffmpeg, mkvmerge, HandBrakeCLI
"""

import time, os, sys, titlecase, logging, subprocess
from howdy_grabbag.utils import find_ffmpeg_exec
from howdy.tv import tv_attic
from argparse import ArgumentParser

def rename_mkv_file(
    mkvtv, tvshow, seasno, epno,
    firstAiredYear = None, outdir = os.getcwd( ) ):
    #
    time0 = time.perf_counter( )
    assert( os.path.isfile( mkvtv ) )
    assert( os.path.basename( mkvtv ).lower( ).endswith('.mkv' ) )
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
            '%s - s%02de%02d - %s.mkv' % ( tvshow, seasno, epno, epname ) ) )
    os.rename( mkvtv, newfile )
    os.chmod( newfile, 0o644 )
    logging.info( 'created %s in %0.3f seconds.' % ( newfile, time.perf_counter( ) - time0 ) )

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
    args = parser.parse_args( )
    #
    ## error checking
    assert( os.path.isdir( args.outdir ) )
    assert( os.path.isfile( args.inputmkv ) )
    assert( os.path.basename( args.inputmkv ).lower( ).endswith('.mkv' ) )
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
    #
    rename_mkv_file(
        args.inputmkv, args.seriesName, seasno, epno,
        outdir = args.outdir )

