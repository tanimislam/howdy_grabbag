"""
This converts an MP4 TV file, with SRT file, and given TV show and season and epno, into an MKV with subtitles with PLEX convention TV file name.
"""

import mutagen.mp4, time, os, sys, titlecase
import uuid, logging, subprocess
from howdy_grabbag.utils import find_ffmpeg_exec
from howdy.tv import tv_attic
from shutil import which
from argparse import ArgumentParser

ffmpeg_exec = find_ffmpeg_exec( )
mkvmerge_exec = which( 'mkvmerge' )
assert( all(map(lambda exec_f: exec_f is not None,
                ( ffmpeg_exec, mkvmerge_exec,  ) ) ) )

def create_mkv_file(
    mp4tv, tvshow, seasno, epno,
    srtfile = None, firstAiredYear = None,
    delete_files = False, outdir = os.getcwd( ) ):
    #
    time0 = time.perf_counter( )
    assert( os.path.isfile( mp4tv ) )
    assert( os.path.basename( mp4tv ).lower( ).endswith('.mp4' ) )
    if srtfile is not None:
        assert( os.path.isfile( srtfile ) )
        assert( os.path.basename( srtfile ).lower( ).endswith('.srt' ) )
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
    # put_info_mp4tv( mp4tv, name, year )
    logging.debug( 'FFMPEG COMMAND: %s' % ' '.join(
        [ ffmpeg_exec, '-y', '-i', mp4tv,
         '-codec', 'copy', "file:%s" % newfile ] ) )
    stdout_val = subprocess.check_output(
        [ ffmpeg_exec, '-y', '-i', mp4tv,
         '-codec', 'copy', "file:%s" % newfile ],
        stderr = subprocess.STDOUT )
    #
    if srtfile is not None:
        tmpmkv = '%s.mkv' % '-'.join( str( uuid.uuid4( ) ).split('-')[:2] )
        logging.debug( 'MKV COMMAND: %s.' % ' '.join(
             [ mkvmerge_exec, '-o', tmpmkv, newfile,
             '--language', '0:eng',
             '--track-name', '0:English', srtfile ] ) )
        stdout_val = subprocess.check_output(
            [ mkvmerge_exec, '-o', tmpmkv, newfile,
             '--language', '0:eng',
             '--track-name', '0:English', srtfile ],
            stderr = subprocess.STDOUT )
        os.rename( tmpmkv, newfile )
    #
    os.chmod( newfile, 0o644 )
    if delete_files:
        os.remove( mp4tv )
        try: os.remove( srtfile )
        except: pass
    logging.info( 'created %s in %0.3f seconds.' % ( newfile, time.perf_counter( ) - time0 ) )

def main( ):
    parser = ArgumentParser( )
    parser.add_argument( '--mp4', dest='mp4', type=str, action='store',
                       help = 'Name of the MP4 TV file name.', required = True )
    parser.add_argument( '--srt', dest='srt', type=str, action='store',
                       help = 'Name of the SRT subtitle file associated with the TV file.' )
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
        '--keep', dest='do_delete', action='store_false', default = True,
        help = 'If chosen, then KEEP the MP4 and SRT files.' )
    parser.add_argument(
        '--noinfo', dest='do_info', action='store_false', default = True,
        help = 'If chosen, then run with NO INFO logging (less debugging).' )
    #
    args = parser.parse_args( )
    #
    ## error checking
    assert( os.path.isdir( args.outdir ) )
    assert( os.path.isfile( args.mp4 ) )
    assert( os.path.basename( args.mp4 ).lower( ).endswith('.mp4' ) )
    if args.srt is not None:
        assert( os.path.isfile( args.srt ) )
        assert( os.path.basename( args.srt ).lower( ).endswith('.srt' ) )
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
    create_mkv_file(
        args.mp4, args.seriesName, seasno, epno,
        delete_files = args.do_delete,
        srtfile = args.srt,
        outdir = args.outdir )
