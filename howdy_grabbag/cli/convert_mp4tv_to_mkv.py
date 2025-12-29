"""
This converts an MP4 TV file, with SRT file, and given TV show and season and epno, into an MKV with subtitles with PLEX convention TV file name.
"""

import mutagen.mp4, time, os, sys, titlecase
import uuid, logging, subprocess
from howdy_grabbag.utils import find_ffmpeg_exec, get_rsync_commands_lowlevel, rsync_upload_mkv
from howdy.core import SSHUploadPaths
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
    return newfile

def main( ):
    parser = ArgumentParser( )
    parser.add_argument( '-M', '--mp4', dest='mp4', type=str, action='store',
                       help = 'Name of the MP4 TV file name.', required = True )
    parser.add_argument( '-S', '--srt', dest='srt', type=str, action='store',
                       help = 'Name of the SRT subtitle file associated with the TV file.' )
    parser.add_argument( '-s', '--series', dest='seriesName', type=str, action='store',
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
    joblib_dict = {
        'mp4tv'     : args.mp4,
        'tvshow'    : args.seriesName,
        'seasno'    : seasno,
        'epno'      : epno,
        'srtfile'   : args.srt,
        'do_delete' : args.do_delete,
        'outdir'    : args.outdir,
        'do_ssh'    : False }
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
    outputfile = create_mkv_file(
        joblib_dict[ 'mp4tv'  ], #args.mp4,
        joblib_dict[ 'tvshow' ], #args.seriesName,
        joblib_dict[ 'seasno' ],
        joblib_dict[ 'epno'   ],
        delete_files = joblib_dict[ 'do_delete' ], #args.do_delete,
        srtfile = joblib_dict[ 'srtfile' ], # args.srt,
        outdir = joblib_dict[ 'outdir' ] ) #args.outdir )
    if joblib_dict[ 'do_ssh' ]:
        mycmd, mxcmd = get_rsync_commands_lowlevel(
            joblib_dict[ 'alias' ],
            joblib_dict[ 'subdir' ],
            outputfile,
            mediatype = SSHUploadPaths.MediaType.tv )
        rsync_upload_mkv( mycmd, mxcmd, numtries = 10 )
