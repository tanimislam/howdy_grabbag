"""
This converts an MP4 movie, with SRT file, and name and year into an MKV file with English subtitles.

12-05-2020: put into plexstuff_grabbag repo
20-10-2019: now can use HandBrakeCLI to convert the MP4 movie file to an MKV file that is smaller

Requires titlecase, mutagen
Requires executables: ffmpeg, mkvmerge, HandBrakeCLI
"""

import mutagen.mp4, time, os, sys, titlecase
import uuid, logging, subprocess
from distutils.spawn import find_executable
from argparse import ArgumentParser

ffmpeg_exec = find_executable( 'ffmpeg' )
mkvmerge_exec = find_executable( 'mkvmerge' )
hcli_exec = find_executable( 'HandBrakeCLI' )
assert( all(map(lambda exec_f: exec_f is not None,
                ( ffmpeg_exec, mkvmerge_exec, hcli_exec ) ) ) )

def convert_mp4_movie(
        mp4movie, name, year, quality = 28,
        srtfile = None,
        delete_files = False ):
    time0 = time.time( )
    assert( os.path.isfile( mp4movie ) )
    assert( os.path.basename( mp4movie ).lower( ).endswith( '.mp4' ) )
    assert( (quality >= 20 ) and (quality <= 30) )
    if srtfile is not None:
        assert( os.path.isfile( srtfile ) )
        assert( os.path.basename( srtfile ).lower( ).endswith('.srt' ) )
    #
    ## now create the movie
    newfile = '%s (%d).mkv' % ( titlecase.titlecase( name ), year )
    put_info_mp4movie( mp4movie, name, year )
    proc = subprocess.Popen(
        [ hcli_exec, '-i', mp4movie, '-e', 'x264', '-q', '%d' % quality,
          '-B', '160', '-o', newfile ], stdout = subprocess.PIPE,
        stderr = subprocess.STDOUT )
    stdout_val, stderr_val = proc.communicate( )
    #
    if srtfile is not None:
        tmpmkv = '%s.mkv' % '-'.join( str( uuid.uuid4( ) ).split('-')[:2] )
        proc = subprocess.Popen(
            [
                mkvmerge_exec, '-o', tmpmkv, newfile,
                '--language', '0:eng',
                '--track-name', '0:English', srtfile ],
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT )
        stdout_val, stderr_val = proc.communicate( )
        os.rename( tmpmkv, newfile )
    #
    os.chmod( newfile, 0o644 )
    if delete_files:
        os.remove( mp4movie )
        try: os.remove( srtfile )
        except: pass
    logging.info( 'created %s in %0.3f seconds.' % (
        newfile, time.time( ) - time0 ) )


def put_info_mp4movie( mp4movie, name, year ):
    time0 = time.time( )
    assert( os.path.isfile( mp4movie ) )
    assert( os.path.basename( mp4movie ).lower( ).endswith('.mp4' ) )
    mp4tags = mutagen.mp4.MP4( mp4movie )
    mp4tags[ '\xa9nam' ] = [ name, ]
    mp4tags[ '\xa9day' ] = [ '%d' % year, ]
    mp4tags.save( )
    logging.info( 'took %0.3f seconds to add metadata to %s.' % (
        time.time( ) - time0, mp4movie ) )

def create_mkv_file( mp4movie, name, year,
                     srtfile = None,
                     delete_files = False ):
    time0 = time.time( )
    assert( os.path.isfile( mp4movie ) )
    assert( os.path.basename( mp4movie ).lower( ).endswith('.mp4' ) )
    if srtfile is not None:
        assert( os.path.isfile( srtfile ) )
        assert( os.path.basename( srtfile ).lower( ).endswith('.srt' ) )
    newfile = '%s (%d).mkv' % ( titlecase.titlecase( name ), year )
    put_info_mp4movie( mp4movie, name, year )
    proc = subprocess.Popen(
        [
            ffmpeg_exec, '-y', '-i', mp4movie,
            '-codec', 'copy', "file:%s" % newfile ],
        stdout = subprocess.PIPE,
        stderr = subprocess.STDOUT )
    stdout_val, stderr_val = proc.communicate( )
    #
    if srtfile is not None:
        tmpmkv = '%s.mkv' % '-'.join( str( uuid.uuid4( ) ).split('-')[:2] )
        proc = subprocess.Popen(
            [
                mkvmerge_exec, '-o', tmpmkv, newfile,
                '--language', '0:eng',
                '--track-name', '0:English', srtfile ],
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT )
        stdout_val, stderr_val = proc.communicate( )
        os.rename( tmpmkv, newfile )
    #
    os.chmod( newfile, 0o644 )
    if delete_files:
        os.remove( mp4movie )
        try: os.remove( srtfile )
        except: pass
    logging.info( 'created %s in %0.3f seconds.' % ( newfile, time.time( ) - time0 ) )

def main( ):
    parser = ArgumentParser( )
    parser.add_argument( '--mp4', dest='mp4', type=str, action='store',
                       help = 'Name of the MP4 movie file name.', required = True )
    parser.add_argument( '--srt', dest='srt', type=str, action='store',
                       help = 'Name of the SRT subtitle file associated with the movie.' )
    parser.add_argument( '-n', '--name', dest='name', type=str, action='store',
                       help = 'Name of the movie.', required = True )
    parser.add_argument( '-y', '--year', type=int, action='store',
                       help = 'Year in which the movie was aired.', required = True )
    parser.add_argument( '--keep', dest='do_delete', action='store_false', default = True,
                       help = 'If chosen, then KEEP the MP4 and SRT files.' )
    parser.add_argument( '--noinfo', dest='do_info', action='store_false', default = True,
                       help = 'If chosen, then run with NO INFO logging (less debugging).' )
    #
    subparser = parser.add_subparsers( help = 'Option of transforming (using HandBrakeCLI) to smaller size MKV file.', dest = 'choose_option' )
    parser_transform = subparser.add_parser( 'transform', help = 'Use HandBrakeCLI to transform to different quality MKV movie. Objective is to reduce size.' )
    parser_transform.add_argument( '-q', '--quality', dest='quality', type=int, action='store', default = 26,
                       help = 'The quality of the conversion that HandBrakeCLI uses. Default is 26.' )
    #
    args = parser.parse_args( )
    #
    ## error checking
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
        convert_mp4_movie(
            args.mp4, args.name, args.year,
            delete_files = args.do_delete,
            srtfile = args.srt, quality = args.quality )
        return
    #
    create_mkv_file(
        args.mp4, args.name, args.year,
        delete_files = args.do_delete,
        srtfile = args.srt )
