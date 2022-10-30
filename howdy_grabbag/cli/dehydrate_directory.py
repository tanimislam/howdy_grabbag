"""
This goes through a *single* directory you specify, and tries to *shrink*  *shrink* episodes (using HEVC_ video quality 28) that start off with a bit rate *above* a certain level, by default 2000 kbps.

.. _HEVC: https://en.wikipedia.org/wiki/High_Efficiency_Video_Coding
"""
import os, sys, logging, time, pandas, numpy, json, subprocess, shutil, uuid, glob
from pathos.multiprocessing import Pool, cpu_count
from tabulate import tabulate
from shutil import which
from argparse import ArgumentParser

_ffmpeg_exec  = which( 'ffmpeg' )
_ffprobe_exec = which( 'ffprobe' )
_nice_exec    = which( 'nice' )
_hcli_exec = which( 'HandBrakeCLI' )
assert( _ffmpeg_exec is not None )
assert( _ffprobe_exec is not None )
assert( _nice_exec is not None )
assert( _hcli_exec is not None )

#
def _get_ffprobe_json( filename ):
    stdout_val = subprocess.check_output(
        [ _ffprobe_exec, '-v', 'quiet', '-show_streams',
         '-show_format', '-print_format', 'json', filename ],
        stderr = subprocess.STDOUT )
    file_info = json.loads( stdout_val )
    return file_info

def _get_hevc_bitrate( filename ):
    try:
        data = _get_ffprobe_json( filename )
        info = {
            'is_hevc' :  data['streams'][0]['codec_name'].lower( ) == 'hevc',
            'bit_rate_kbps' : float( data['format']['bit_rate' ] ) / 1_024, }
        return info
    except: return None

def find_files_to_process( directory_name = os.getcwd( ), do_hevc = True, min_bitrate = 2_000 ):
    fnames = sorted(
        glob.glob( os.path.join( directory_name, '*.mp4' ) ) +
        glob.glob( os.path.join( directory_name, '*.mkv' ) ) ) 
    with Pool( processes = cpu_count( ) ) as pool:
        list_of_files_hevc_br = list(filter(
            lambda tup: tup[1] is not None and tup[1]['bit_rate_kbps'] >= min_bitrate,
            pool.map(lambda fname: ( fname, _get_hevc_bitrate( fname ) ), fnames ) ) )
        if not do_hevc:
            list_of_files_hevc_br = list(filter(lambda tup: tup[1]['is_hevc'] == False,
                                                list_of_files_hevc_br ) )
        return dict( list_of_files_hevc_br )        

def process_single_directory(
    directory_name = os.getcwd( ), do_hevc = True, min_bitrate = 2_000,
    qual = 28 ):
    fnames_dict = find_files_to_process(
        directory_name = directory_name, do_hevc = do_hevc,
        min_bitrate = min_bitrate )
    time00 = time.perf_counter( )
    list_processed = [ 'found %02d files to dehydrate in %s.' % (
        len( fnames_dict ), os.path.abspath( directory_name ) ), ]
    json.dump( list_processed, open( 'processed_stuff.json', 'w' ), indent = 1 )
    for idx, filename in enumerate(sorted( fnames_dict ) ):
        time0 = time.perf_counter( )
        newfile = '%s-%s' % ( str( uuid.uuid4( ) ).split('-')[0].strip( ), os.path.basename( filename ) )
        stdout_val = subprocess.check_output([
            _nice_exec, '-n', '19', _hcli_exec,
            '-i', filename, '-e', 'x265', '-q', '%d' % qual, '-B', '160',
            '-a', ','.join(map(lambda num: '%d' % num, range(1,35))),
            '-s', ','.join(map(lambda num: '%d' % num, range(1,35))),
            '-o', newfile ],
            stderr = subprocess.PIPE )
        #
        os.chmod(newfile, 0o644 )
        shutil.move( newfile, filename )
        dt0 = time.perf_counter( ) - time0
        logging.info( 'processed file %02d / %02d in %0.3f seconds' % (
            idx + 1, len( fnames_dict ), dt0 ) )
        list_processed.append( 'processed file %02d / %02d in %0.3f seconds' % (
            idx + 1, len( fnames_dict ), dt0 ) )
        json.dump( list_processed, open( 'processed_stuff.json', 'w' ), indent = 1 )
    dt00 = time.perf_counter( ) - time00
    logging.info( 'took %0.3f seconds to process %d files' % (
        dt00, len( fnames_dict ) ) )
    list_processed.append( 'took %0.3f seconds to process %d files' % (
        dt00, len( fnames_dict ) ) )
    json.dump( list_processed, open( 'processed_stuff.json', 'w' ), indent = 1 )

def main( ):
    parser = ArgumentParser( )
    parser.add_argument( '-d', '--directory', dest='directory', type=str, action = 'store', default = os.getcwd( ),
                        help = 'Name of the directory of MKV and MP4 files to dehydrate. Default is %s.' % os.getcwd( ) )
    parser.add_argument( '-M', '--minbitrate', dest = 'minbitrate', type = int, action = 'store', default = 2_000,
                        help = ' '.join([
                            'The minimum total bitrate (in kbps) of episodes to dehydrate. Must be >= 2000 kbps.',
                            'Default is 2000 kbps.']))
    parser.add_argument( '--info', dest='do_info', action='store_true', default = False,
                        help = 'If chosen, then turn on INFO logging.' )
    parser.add_argument( '-N', '--nohevc', dest = 'do_hevc', action = 'store_false', default = True,
                        help = 'If chosen, then only process the big episodes that are NOT HEVC. Default is to process everything.' )
    #
    ## check on which TV shows are candidates for dehydration, or to dehydrate specific TV shows.
    subparsers = parser.add_subparsers( help = ' '.join([
        'Choose on whether to list the filenames in a directory to dehydrate,',
        'or to dehydrate all valid MP4 and MKV files at top level inside a directory.' ]),
                                       dest = 'choose_option' )
    parser_listcandidates = subparsers.add_parser( 'list',      help = 'If chosen, then list the valid filenames to dehydrate.' )
    parser_dehydrate      = subparsers.add_parser( 'dehydrate', help = 'If chosen, then dehydrate all valid filenames.' )
    #
    ## list filenames, do nothing more
    #
    ## dehydrate a single TV show
    parser_dehydrate.add_argument( '-Q', '--quality', dest = 'parser_dehydrate_quality', metavar = 'QUALITY', type = int, action = 'store',
                                  default = 28, help = 'Will dehydrate shows using HEVC video codec with this quality. Default is 28. Must be >= 20.' )
    #
    ## parsing arguments
    time0 = time.perf_counter( )
    args = parser.parse_args( )
    assert( args.minbitrate >= 1000 )
    logger = logging.getLogger( )
    if args.do_info: logger.setLevel( logging.INFO )
    #
    ## list filenames
    if args.choose_option == 'list':
        fnames_dict = find_files_to_process(
            directory_name = args.directory,
            do_hevc = args.do_hevc, min_bitrate = args.minbitrate )
        data = list( zip(
            map(os.path.basename, sorted( fnames_dict ) ),
            map(lambda fname: '%0.1f' % fnames_dict[ fname ][ 'bit_rate_kbps' ], sorted( fnames_dict ) ) ) )
        print( 'found %02d valid files in %s with min bitrate >= %d kbps.\n' % (
            len( fnames_dict ), os.path.abspath( args.directory ), args.minbitrate ) )
        print( '%s\n' % tabulate( data, headers = [ 'FILENAME', 'KBPS' ] ) )
        print( 'took %0.3f seconds to process.' % ( time.perf_counter( ) - time0 ) )
        return
    #
    ## dehydrate directory
    elif args.choose_option == 'dehydrate':
        quality = args.parser_dehydrate_quality
        assert( quality >= 20 )
        process_single_directory(
        directory_name = args.directory, do_hevc = args.do_hevc,
            min_bitrate = args.minbitrate, qual = quality )
