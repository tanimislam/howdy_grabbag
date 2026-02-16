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
import uuid, logging, subprocess
from howdy.core import core_rsync, SSHUploadPaths
from howdy_grabbag.utils import get_rsync_commands, rsync_upload_mkv
from shutil import which
from argparse import ArgumentParser
#
from howdy_grabbag import (
    ffmpeg_exec, mkvmerge_exec,
    mkvpropedit_exec, hcli_exec )

def convert_mp4_movie(
    mp4movie, name, year, quality = 28,
    srtfile = None,
    delete_files = False, outdir = os.getcwd( ) ):
    #
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
            stdout_val = subprocess.check_output([
                mkvmerge_exec, '-o', tmpmkv, newfile,
                '--language', '0:eng',
                '--track-name', '0:English', srtfile ], stderr = subprocess.STDOUT )                                                 
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

def create_mkv_file(
    mp4movie, name, year,
    srtfile = None,
    delete_files = False, outdir = os.getcwd( ),
    language = None ):
    #
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
    ##
    logger = logging.getLogger( )
    if args.do_info: logger.setLevel( logging.INFO )
    #
    ## error checking
    assert( os.path.isdir( args.outdir ) )
    assert( os.path.isfile( args.mp4 ) )
    assert( os.path.basename( args.mp4 ).lower( ).endswith('.mp4' ) )
    if args.srt is not None:
        assert( os.path.isfile( args.srt ) )
        assert( os.path.basename( args.srt ).lower( ).endswith('.srt' ) )
    joblib_dict = {
        'outdir'       : args.outdir,
        'mp4'          : args.mp4,
        'name'         : args.name,
        'srt'          : args.srt,
        'year'         : args.year,
        'lang'         : args.lang,
        'do_delete'    : args.do_delete,
        'do_transform' : False,
        'do_ssh'       : False }
    if args.choose_option == 'transform':
        joblib_dict[ 'do_transform' ] = True
        joblib_dict[ 'quality'      ] = args.quality
    #
    ## upload via ssh to the remote server
    if args.choose_option == 'ssh':
        joblib_dict[ 'do_ssh' ] = True
        joblib_dict[ 'alias'  ] = args.ssh_alias
        joblib_dict[ 'subdir' ] = args.ssh_subdir
        data_init = get_rsync_commands(
            joblib_dict[ 'alias' ], "", subdir = joblib_dict[ 'subdir' ] )
        if data_init is None:
            return
    
    
    if joblib_dict[ 'do_transform' ]:
        outputfile = convert_mp4_movie(
            joblib_dict[ 'mp4' ],
            joblib_dict[ 'name' ],
            joblib_dict[ 'year' ],
            delete_files = joblib_dict[ 'do_delete' ],
            srtfile = joblib_dict[ 'srt' ],
            quality = joblib_dict[ 'quality' ],
            outdir  = joblib_dict[ 'outdir' ] )
        return

    outputfile = create_mkv_file(
        joblib_dict[ 'mp4' ],
        joblib_dict[ 'name' ],
        joblib_dict[ 'year' ],
        delete_files = joblib_dict[ 'do_delete' ],
        srtfile  = joblib_dict[ 'srt' ],
        outdir   = joblib_dict[ 'outdir' ],
        language = joblib_dict[ 'lang' ] )
    
    ## upload via ssh to the remote server
    if joblib_dict[ 'do_ssh' ]:
        mycmd, mxcmd = get_rsync_commands(
            joblib_dict[ 'alias' ],
            outputfile,
            subdir = joblib_dict[ 'subdir' ] )
        rsync_upload_mkv( mycmd, mxcmd, numtries = 10 )
