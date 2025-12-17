"""
This converts an MP4 movie, with SRT file, and name and year into an MKV file with English subtitles.

19-09-2020: rename all dependencies to howdy from plexstuff
12-05-2020: put into howdy_grabbag repo
20-10-2019: now can use HandBrakeCLI to convert the MP4 movie file to an MKV file that is smaller

Requires titlecase, mutagen
Requires executables: ffmpeg, mkvmerge, mkvpropedit, HandBrakeCLI
"""
import signal
from howdy import signal_handler
signal.signal( signal.SIGINT, signal_handler )
#
import mutagen.mp4, time, os, sys, titlecase
import uuid, logging, subprocess, shlex
from howdy.core import core_rsync, SSHUploadPaths
from howdy_grabbag.utils import find_ffmpeg_exec
from shutil import which
from argparse import ArgumentParser

ffmpeg_exec = find_ffmpeg_exec( )
mkvmerge_exec = which( 'mkvmerge' )
mkvpropedit_exec = which( 'mkvpropedit' )
hcli_exec = which( 'HandBrakeCLI' )
assert( all(map(lambda exec_f: exec_f is not None,
                ( ffmpeg_exec, mkvmerge_exec, mkvpropedit_exec, hcli_exec ) ) ) )

def find_valid_movie_aliases( ):
    data_remote_collections = core_rsync.get_remote_connections( )
    valid_movie_aliases = sorted(
        set( filter(lambda alias: data_remote_collections[ alias ][ 'media type' ] == 'movie',
                    data_remote_collections ) ) )
    return valid_movie_aliases

def get_rsync_commands(
    alias, outputfile, subdir = None ):
    #
    valid_aliases = find_valid_movie_aliases( )
    if alias not in valid_aliases:
        print( "ERROR, chosen alias = %s for remote movie media directory collection not one of %s." % (
            alias, valid_aliases ) )
        return None
    remote_collection = core_rsync.get_remote_connections( show_password = True )[ alias ]
    sshpath = remote_collection[ 'ssh path' ]
    maindir = remote_collection[ 'main directory' ]
    if len( remote_collection[ 'sub directories' ] ) == 0:
        finaldir = maindir
    else:
        if subdir is None:
            print( "ERROR, sub directory key must be one of %s." % sorted( remote_collection[ 'sub directories' ] ) )
            return None
        if subdir not in remote_collection[ 'sub directories' ]:
            print( "ERROR, sub directory key = %s must be one of %s." % (
                subdir,
                sorted( remote_collection[ 'sub directories' ] ) ) )
            return None
        finaldir = os.path.join( maindir, remote_collection[ 'sub directories' ][ subdir ] )
    #
    logging.info( 'MOVIE FILE TO UPLOAD: %s.' % outputfile )
    logging.info( 'REMOTE MOVIE MEDIA DIRECTORY COLLECTION SSH PATH: %s.' % sshpath )
    logging.info( 'REMOTE MOVIE MEDIA DIRECTORY COLLECTION UPLOAD DIRECTORY: %s.' % finaldir )
    #
    ## now the command to upload via rsync
    data_rsync = {
        'password'  : remote_collection[ 'password' ],
        'sshpath'   : sshpath,
        'subdir'    : finaldir,
        'local_dir' : '' }
    mycmd, mxcmd = core_rsync.get_rsync_command(
        data_rsync, outputfile, do_download = False,
        use_local_dir_for_upload = False )
    return mycmd, mxcmd

def rsync_upload_mkv( mycmd, mxcmd, numtries = 10 ):
    assert( numtries > 0 )
    mystr_split = [ 'STARTING THIS RSYNC CMD: %s' % mxcmd ]
    logging.info( mystr_split[-1] )
    logging.info( 'TRYING UP TO %d TIMES.' % numtries )
    time0 = time.perf_counter( )
    for idx in range( numtries ):
        time00 = time.perf_counter( )
        stdout_val = subprocess.check_output(
            shlex.split( mycmd ), stderr = subprocess.STDOUT )
        if not any(map(lambda line: 'dispatch_run_fatal' in line, stdout_val.decode('utf-8').split('\n'))):
            mystr_split.append(
                'SUCCESSFUL ATTEMPT %d / %d IN %0.3f SECONDS.' % (
                    idx + 1, numtries, time.perf_counter( ) - time00 ) )
            logging.debug( '%s\n' % stdout_val.decode( 'utf-8' ) )
            logging.info( mystr_split[-1] )
            return 'SUCCESS', '\n'.join( mystr_split )
        mystr_split.append('FAILED ATTEMPT %d / %d IN %0.3f SECONDS.' % (
            idx + 1, numtries, time.perf_counter( ) - time00 ) )
        logging.info( mystr_split[-1] )
        logging.debug( '%s\n' % stdout_val.decode( 'utf-8' ) )
    mystr_split.append( 'ATTEMPTED AND FAILED %d TIMES IN %0.3f SECONDS.' % (
        numtries, time.perf_counter( ) - time0 ) )
    logging.info( mystr_split[-1] )
    return 'FAILURE', '\n'.join( mystr_split )
    

def convert_mp4_movie(
        mp4movie, name, year, quality = 28,
        srtfile = None,
        delete_files = False, outdir = os.getcwd( ) ):
    time0 = time.perf_counter( )
    assert( os.path.isfile( mp4movie ) )
    assert( os.path.basename( mp4movie ).lower( ).endswith( '.mp4' ) )
    assert( (quality >= 20 ) and (quality <= 30) )
    if srtfile is not None:
        assert( os.path.isfile( srtfile ) )
        assert( os.path.basename( srtfile ).lower( ).endswith('.srt' ) )
    #
    ## now create the movie
    newfile = os.path.abspath(
        os.path.join(
            os.path.expanduser( outdir ),
            '%s (%d).mkv' % ( titlecase.titlecase( name ), year ) ) )
    put_info_mp4movie( mp4movie, name, year )
    stdout_val = subprocess.check_output(
        [ hcli_exec, '-i', mp4movie, '-e', 'x264', '-q', '%d' % quality,
          '-B', '160', '-o', newfile ], stderr = subprocess.STDOUT )
    #
    if srtfile is not None:
        tmpmkv = '%s.mkv' % '-'.join( str( uuid.uuid4( ) ).split('-')[:2] )
        try:
          stdout_val = subprocess.check_output(
            [
              mkvmerge_exec, '-o', tmpmkv, newfile,
              '--language', '0:eng',
              '--track-name', '0:English', srtfile ],
            stderr = subprocess.STDOUT )
        except: pass
        os.rename( tmpmkv, newfile )
    #
    os.chmod( newfile, 0o644 )
    if delete_files:
        os.remove( mp4movie )
        try: os.remove( srtfile )
        except: pass
    logging.info( 'created %s in %0.3f seconds.' % (
        newfile, time.perf_counter( ) - time0 ) )
    return os.path.realpath( newfile )

def put_info_mp4movie( mp4movie, name, year, language = None ):
    time0 = time.perf_counter( )
    assert( os.path.isfile( mp4movie ) )
    assert( os.path.basename( mp4movie ).lower( ).endswith('.mp4' ) )
    mp4tags = mutagen.mp4.MP4( mp4movie )
    mp4tags[ '\xa9nam' ] = [ name, ]
    mp4tags[ '\xa9day' ] = [ '%d' % year, ]
    mp4tags.save( )
    logging.info( 'took %0.3f seconds to add metadata to %s.' % (
        time.perf_counter( ) - time0, mp4movie ) )

def create_mkv_file( mp4movie, name, year,
                     srtfile = None,
                     delete_files = False, outdir = os.getcwd( ),
                     language = None ):
    time0 = time.perf_counter( )
    assert( os.path.isfile( mp4movie ) )
    assert( os.path.basename( mp4movie ).lower( ).endswith('.mp4' ) )
    if srtfile is not None:
        assert( os.path.isfile( srtfile ) )
        assert( os.path.basename( srtfile ).lower( ).endswith('.srt' ) )
    newfile = os.path.abspath(
        os.path.join(
            os.path.expanduser( outdir ),
            '%s (%d).mkv' % ( titlecase.titlecase( name ).replace('/','-' ), year ) ) )
    put_info_mp4movie( mp4movie, name, year )
    logging.debug( 'FFMPEG COMMAND: %s' % ' '.join(
        [ ffmpeg_exec, '-y', '-i', mp4movie,
         '-acodec', 'copy',
         '-vcodec', 'copy',
         '-sn', "file:%s" % newfile ] ) )
    stdout_val = subprocess.check_output(
        [ ffmpeg_exec, '-y', '-i', mp4movie,
         '-acodec', 'copy',
         '-vcodec', 'copy',
         '-sn', "file:%s" % newfile ],
        stderr = subprocess.STDOUT )
    #
    if srtfile is not None:
        tmpmkv = '%s.mkv' % '-'.join( str( uuid.uuid4( ) ).split('-')[:2] )
        logging.debug( 'MKV COMMAND: %s.' % ' '.join(
             [ mkvmerge_exec, '-o', tmpmkv, newfile,
             '--language', '0:eng',
             '--track-name', '0:English', srtfile ] ) )
        try:
          stdout_val = subprocess.check_output(
            [ mkvmerge_exec, '-o', tmpmkv, newfile,
              '--language', '0:eng',
              '--track-name', '0:English', srtfile ],
            stderr = subprocess.STDOUT )
        except: pass
        os.rename( tmpmkv, newfile )
    #
    os.chmod( newfile, 0o644 )
    if delete_files:
        os.remove( mp4movie )
        try: os.remove( srtfile )
        except: pass
    if language is not None:
        logging.info( 'setting audio track language to %s.' % language )
        stdout_val = subprocess.check_output(
            [ mkvpropedit_exec, newfile, '--edit', 'track:a1',
             '--set', 'language=%s' % language ], stderr = subprocess.PIPE )
        os.chmod( newfile, 0o644 )
        
    logging.info( 'created %s in %0.3f seconds.' % ( newfile, time.perf_counter( ) - time0 ) )
    return os.path.realpath( newfile )

def main( ):
    parser = ArgumentParser( )
    parser.add_argument( '-M', '--mp4', dest='mp4', type=str, action='store',
                       help = 'Name of the MP4 movie file name.', required = True )
    parser.add_argument( '-S', '--srt', dest='srt', type=str, action='store',
                       help = 'Name of the SRT subtitle file associated with the movie.' )
    parser.add_argument( '-n', '--name', dest='name', type=str, action='store',
                       help = 'Name of the movie.', required = True )
    parser.add_argument( '-y', '--year', type=int, action='store',
                       help = 'Year in which the movie was aired.', required = True )
    parser.add_argument( '-L', '--lang', type=str, action='store', default = None,
                       help = 'Optional argument, specify the language of the audio track.' )
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
    subparser = parser.add_subparsers( help = 'Option of transforming (using HandBrakeCLI) to smaller size MKV file.', dest = 'choose_option' )
    #
    ## transform file ALMOST NEVER DONE
    parser_transform = subparser.add_parser(
        'transform', help = 'Use HandBrakeCLI to transform to different quality MKV movie. Objective is to reduce size.' )
    parser_transform.add_argument(
        '-Q', '--quality', dest='quality', type=int, action='store', default = 26,
        help = 'The quality of the conversion that HandBrakeCLI uses. Default is 26.' )
    #
    ## SSH file to remote directory
    parser_ssh = subparser.add_parser(
        'ssh', help = 'Use the collection of remote media directory collections to upload final MKV movie to remote SSH server.' )
    parser_ssh.add_argument( '-A', '--alias', dest = 'ssh_alias', type = str, action = 'store', required = True,
                             help = 'The alias to identify the remote media directory collection, which contains movies.' )
    parser_ssh.add_argument( '-S', '--subdir', dest = 'ssh_subdir', type = str, action = 'store',
                             help = ' '.join([
                                 'Optional argument.',
                                 'If the movie collection has a list of subdirectories, then must be identified.',
                                 'Otherwise upload to the main directory.' ] ) )
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
    
    
    if args.choose_option == 'transform':
        outputfile = convert_mp4_movie(
            args.mp4, args.name, args.year,
            delete_files = args.do_delete,
            srtfile = args.srt, quality = args.quality,
            outdir = args.outdir )
        return

    outputfile = create_mkv_file(
        args.mp4, args.name, args.year,
        delete_files = args.do_delete,
        srtfile = args.srt,
        outdir = args.outdir,
        language = args.lang )
    #
    ## upload via ssh to the remote server
    if args.choose_option == 'ssh':
        data = get_rsync_commands(
            args.ssh_alias, outputfile, subdir = args.ssh_subdir )
        if data is None:
            return
        mycmd, mxcmd = data
        rsync_upload_mkv( mycmd, mxcmd, numtries = 10 )
