"""
This goes through *multiple* directories you specify, and tries to *shrink*  *shrink* episodes (using HEVC_ video quality 28) that start off with a bit rate *above* a certain level, by default 2000 kbps.

.. _HEVC: https://en.wikipedia.org/wiki/High_Efficiency_Video_Coding
"""
import os, sys, logging, time, pandas, numpy, json, subprocess, shutil, uuid, glob
from pathos.multiprocessing import Pool, cpu_count
from tabulate import tabulate
from shutil import which
from itertools import chain
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

def _get_bitrate_AVI( filename ):
  try:
    data = _get_ffprobe_json( filename )
    info = { 
      'bit_rate_kbps' : float( data['format']['bit_rate' ] ) / 1_024, }
    return info
  except: return None

def find_files_to_process( directory_names = [ os.getcwd( ), ], do_hevc = True, min_bitrate = 2_000 ):
  fnames = sorted(set(
      chain.from_iterable(map(
          lambda directory_name:
          glob.glob( os.path.join( directory_name, '*.mp4' ) ) +
          glob.glob( os.path.join( directory_name, '*.mkv' ) ) +
          glob.glob( os.path.join( directory_name, '*.webm' ) ), directory_names ) ) ) )
  with Pool( processes = cpu_count( ) ) as pool:
    list_of_files_hevc_br = list(filter(
      lambda tup: tup[1] is not None and tup[1]['bit_rate_kbps'] >= min_bitrate,
      pool.map(lambda fname: ( fname, _get_hevc_bitrate( fname ) ), fnames ) ) )
    if not do_hevc:
      list_of_files_hevc_br = list(filter(lambda tup: tup[1]['is_hevc'] == False,
                                          list_of_files_hevc_br ) )
    return dict( list_of_files_hevc_br )

def find_files_to_process_AVI( directory_names = [ os.getcwd( ), ] ):
  fnames = sorted(set(
      chain.from_iterable(map(
          lambda directory_name:
          glob.glob( os.path.join( directory_name, '*.avi' ) ) +
          glob.glob( os.path.join( directory_name, '*.mpg' ) ), directory_names ) ) ) ) 
  with Pool( processes = cpu_count( ) ) as pool:
    return dict( 
      pool.map(lambda fname: ( fname, _get_bitrate_AVI( fname ) ), fnames ) )

def process_multiple_directories_subtitles(
    directory_names = [ os.getcwd( ), ], output_json_file = 'processed_stuff.json',
    do_add_subtitle = False ):
    assert( os.path.basename( output_json_file ).endswith( '.json' ) )
    #
    ## check whether whisper exists
    _whisper_exec  = which( 'whisper' )
    assert( _whisper_exec is not None )
    #
    ## if adding subtitle check whether mkvmerge exists
    if do_add_subtitle:
      _mkvmerge_exec = which( 'mkvmerge' )
      assert( _mkvmerge_exec is not None )
    fnames_dict = find_files_to_process(
      directory_names = directory_names, do_hevc = True,
      min_bitrate = 100 )
    time00 = time.perf_counter( )
    list_processed = [ 'found %02d files to subtitle in %s.' % (
      len( fnames_dict ), os.path.abspath( directory_name ) ), ]
    if do_add_subtitle: # all files must end in mkv
      assert( all(map(lambda fname: os.path.basename( fname ).endswith('.mkv' ), fnames_dict ) ) )
    json.dump( list_processed, open( output_json_file, 'w' ), indent = 1 )
    for idx, filename in enumerate(sorted( fnames_dict ) ):
      time0 = time.perf_counter( )
      stdout_val = subprocess.check_output(
        [ _nice_exec, '-n', '19', _whisper_exec,
          filename, '--output_format', 'srt', '--language', 'en' ],
        stderr = subprocess.PIPE )
      #
      ## if adding subtitle
      if do_add_subtitle:
        subfile = os.path.basename( filename ).replace( '.mkv', '.srt' )
        assert( os.path.isfile( subfile ) )
        newfile = '%s-%s' % ( str( uuid.uuid4( ) ).split('-')[0].strip( ), os.path.basename( filename ).replace(":", "-" ) )
        stdout_val = subprocess.check_output(
          [ _mkvmerge_exec, '-o', newfile, filename, '--language', '0:eng', '--track-name', '0:English', subfile ],
          stderr = subprocess.PIPE )
        os.chmod( newfile, 0o644 )
        os.rename( newfile, filename )
        os.remove( subfile )
      dt0 = time.perf_counter( ) - time0
      logging.info( 'processed file %02d / %02d in %0.3f seconds' % (
        idx + 1, len( fnames_dict ), dt0 ) )
      list_processed.append( 'processed file %02d / %02d in %0.3f seconds' % (
        idx + 1, len( fnames_dict ), dt0 ) )
      json.dump( list_processed, open( output_json_file, 'w' ), indent = 1 )
    dt00 = time.perf_counter( ) - time00
    logging.info( 'took %0.3f seconds to process %d files' % (
      dt00, len( fnames_dict ) ) )
    list_processed.append( 'took %0.3f seconds to process %d files' % (
      dt00, len( fnames_dict ) ) )
    json.dump( list_processed, open( output_json_file, 'w' ), indent = 1 )

def process_multiple_directories(
    directory_names = [ os.getcwd( ), ], do_hevc = True, min_bitrate = 2_000,
    qual = 28, output_json_file = 'processed_stuff.json' ):
    assert( os.path.basename( output_json_file ).endswith( '.json' ) )
    fnames_dict = find_files_to_process(
        directory_names = directory_names, do_hevc = do_hevc,
        min_bitrate = min_bitrate )
    time00 = time.perf_counter( )
    list_processed = [ 'found %02d files to dehydrate in %s.' % (
        len( fnames_dict ), list(map(os.path.abspath, directory_names ) ) ), ]
    json.dump( list_processed, open( output_json_file, 'w' ), indent = 1 )
    for idx, filename in enumerate(sorted( fnames_dict ) ):
        time0 = time.perf_counter( )
        newfile = '%s-%s' % ( str( uuid.uuid4( ) ).split('-')[0].strip( ), os.path.basename( filename ).replace(":", "-" ) )
        stdout_val = subprocess.check_output([
            _nice_exec, '-n', '19', _hcli_exec,
            '-i', filename, '-e', 'x265', '-q', '%d' % qual, '-E', 'av_aac', '-B', '160',
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
        json.dump( list_processed, open( output_json_file, 'w' ), indent = 1 )
    dt00 = time.perf_counter( ) - time00
    logging.info( 'took %0.3f seconds to process %d files' % (
        dt00, len( fnames_dict ) ) )
    list_processed.append( 'took %0.3f seconds to process %d files' % (
        dt00, len( fnames_dict ) ) )
    json.dump( list_processed, open( output_json_file, 'w' ), indent = 1 )


def process_multiple_directories_AVI(
    directory_names = [ os.getcwd( ), ],
    qual = 22,
    output_json_file = 'processed_stuff.json' ):
    assert( os.path.basename( output_json_file ).endswith( '.json' ) )
    fnames_dict = find_files_to_process_AVI(
        directory_names = directory_names )
    time00 = time.perf_counter( )
    list_processed = [ 'found %02d files to dehydrate in %s.' % (
        len( fnames_dict ), list(map(os.path.abspath, directory_names ) ) ), ]
    json.dump( list_processed, open( output_json_file, 'w' ), indent = 1 )
    for idx, filename in enumerate(sorted( fnames_dict ) ):
        time0 = time.perf_counter( )
        newfile = '.'.join(
            os.path.basename( filename ).replace(":", "-").split('.')[:-1] + [ 'mkv', ] )
        stdout_val = subprocess.check_output([
            _nice_exec, '-n', '19', _hcli_exec,
            '-i', filename, '-e', 'x265', '-q', '%d' % qual, '-E', 'av_aac', '-B', '160',
            '-a', ','.join(map(lambda num: '%d' % num, range(1,35))),
            '-o', newfile ],
            stderr = subprocess.PIPE )
        #
        os.chmod(newfile, 0o644 )
        shutil.move( newfile, directory_name )
        os.remove( filename )
        dt0 = time.perf_counter( ) - time0
        logging.info( 'processed file %02d / %02d in %0.3f seconds' % (
            idx + 1, len( fnames_dict ), dt0 ) )
        list_processed.append( 'processed file %02d / %02d in %0.3f seconds' % (
            idx + 1, len( fnames_dict ), dt0 ) )
        json.dump( list_processed, open( output_json_file, 'w' ), indent = 1 )
    dt00 = time.perf_counter( ) - time00
    logging.info( 'took %0.3f seconds to process %d files' % (
        dt00, len( fnames_dict ) ) )
    list_processed.append( 'took %0.3f seconds to process %d files' % (
        dt00, len( fnames_dict ) ) )
    json.dump( list_processed, open( output_json_file, 'w' ), indent = 1 )
    
def main( ):
    parser = ArgumentParser( )
    parser.add_argument( '-d', '--directories', dest='directories', type=str, action = 'store', nargs = '+', default = [ os.getcwd( ), ],
                        help = 'Name of the directories of MKV and MP4 files to dehydrate. Default is %s.' % [ os.getcwd( ), ] )
    parser.add_argument( '-M', '--minbitrate', dest = 'minbitrate', type = int, action = 'store', default = 2_000,
                        help = ' '.join([
                            'The minimum total bitrate (in kbps) of episodes to dehydrate. Must be >= 2000 kbps.',
                            'Default is 2000 kbps.']))
    parser.add_argument( '--info', dest='do_info', action='store_true', default = False,
                        help = 'If chosen, then turn on INFO logging.' )
    parser.add_argument( '-N', '--nohevc', dest = 'do_hevc', action = 'store_false', default = True,
                        help = 'If chosen, then only process the big episodes that are NOT HEVC. Default is to process everything.' )
    parser.add_argument( '-A', '--doavi', dest = 'do_avi', action = 'store_true', default = False,
                        help = 'If chosen, then process AVI and MPEG files for dehydration at higher qualities.' )
    #
    ## dehydrate arguments
    parser.add_argument( '-Q', '--quality', dest = 'parser_dehydrate_quality', metavar = 'QUALITY', type = int, action = 'store',
                                  default = 28, help = 'Will dehydrate shows using HEVC video codec with this quality. Default is 28. Must be >= 20.' )
    parser.add_argument( '-J', '--jsonfile', dest = 'parser_dehydrate_jsonfile', metavar = 'JSONFILE', type = str, action = 'store', default = 'processed_stuff.json',
                                  help = 'Name of the JSON file to store progress-as-you-go-along on directory dehydration. Default file name = "processed_stuff.json".' )
    #
    ## parsing arguments
    time0 = time.perf_counter( )
    args = parser.parse_args( )
    assert( args.minbitrate >= 500 )
    logger = logging.getLogger( )
    if args.do_info: logger.setLevel( logging.INFO )
    #
    directory_names = sorted(set(filter(os.path.isdir, map(lambda dirname: os.path.realpath( os.path.expanduser( dirname ) ), args.directories ) ) ) )
    #
    ## dehydrate directory
    quality = args.parser_dehydrate_quality
    jsonfile = os.path.expanduser( args.parser_dehydrate_jsonfile )
    assert( os.path.basename( jsonfile ).endswith( '.json' ) )
    assert( quality >= 20 )
    if not args.do_avi:
        process_multiple_directories(
            directory_names = directory_names, do_hevc = args.do_hevc,
            min_bitrate = args.minbitrate, qual = quality,
            output_json_file = jsonfile )
    else:
        process_multiple_directories_AVI(
            directory_names = directory_names,
            qual = quality,
            output_json_file = jsonfile )

def main_list( ):
    parser = ArgumentParser( )
    parser.add_argument( '-d', '--directories', dest='directories', type=str, action = 'store', nargs = '+', default = [ os.getcwd( ), ],
                        help = 'Name of the directories of MKV and MP4 files to dehydrate. Default is %s.' % [ os.getcwd( ), ] )
    parser.add_argument( '-M', '--minbitrate', dest = 'minbitrate', type = int, action = 'store', default = 2_000,
                        help = ' '.join([
                            'The minimum total bitrate (in kbps) of episodes to dehydrate.',
                            'Default is 2000 kbps.']))
    parser.add_argument( '--info', dest='do_info', action='store_true', default = False,
                        help = 'If chosen, then turn on INFO logging.' )
    parser.add_argument( '-N', '--nohevc', dest = 'do_hevc', action = 'store_false', default = True,
                        help = 'If chosen, then only process the big episodes that are NOT HEVC. Default is to process everything.' )
    parser.add_argument( '-A', '--doavi', dest = 'do_avi', action = 'store_true', default = False,
                        help = 'If chosen, then process AVI and MPEG files for dehydration at higher qualities.' )
    #
    ## parsing arguments
    time0 = time.perf_counter( )
    args = parser.parse_args( )
    assert( args.minbitrate >= 0 )
    logger = logging.getLogger( )
    if args.do_info: logger.setLevel( logging.INFO )
    #
    directory_names = sorted(set(filter(os.path.isdir, map(lambda dirname: os.path.realpath( os.path.expanduser( dirname ) ), args.directories ) ) ) )
    #
    ## list filenames
    if not args.do_avi:
        fnames_dict = find_files_to_process(
            directory_names = directory_names,
            do_hevc = args.do_hevc, min_bitrate = args.minbitrate )
        data = list( zip(
            map(os.path.basename, sorted( fnames_dict ) ),
            map(lambda fname: '%0.1f' % fnames_dict[ fname ][ 'bit_rate_kbps' ], sorted( fnames_dict ) ) ) )
        print( 'found %02d valid files in %s with min bitrate >= %d kbps.\n' % (
            len( fnames_dict ), directory_names, args.minbitrate ) )
        print( '%s\n' % tabulate( data, headers = [ 'FILENAME', 'KBPS' ] ) )
        return
    #
    fnames_dict_AVI = find_files_to_process_AVI(
        directory_names = directory_names )
    data_AVI = list( zip(
        map(os.path.basename, sorted( fnames_dict_AVI ) ),
        map(lambda fname: '%0.1f' % fnames_dict_AVI[ fname ][ 'bit_rate_kbps' ], sorted( fnames_dict_AVI ) ) ) )
    print( 'found %02d valid files in %s with min bitrate >= %d kbps.\n' % (
        len( fnames_dict_AVI ), directory_names, args.minbitrate ) )
    print( '%s\n' % tabulate( data_AVI, headers = [ 'FILENAME', 'KBPS' ] ) )
    print( 'took %0.3f seconds to process.' % ( time.perf_counter( ) - time0 ) )

def main_subtitles( ):
  parser = ArgumentParser( )
  parser.add_argument( '-d', '--directories', dest='directories', type=str, action = 'store', nargs = '+', default = [ os.getcwd( ), ],
                       help = 'Name of the directories of MKV and MP4 files to dehydrate. Default is %s.' % [ os.getcwd( ), ] )
  parser.add_argument( '--info', dest='do_info', action='store_true', default = False,
                       help = 'If chosen, then turn on INFO logging.' )
  parser.add_argument( '-J', '--jsonfile', dest = 'parser_dehydrate_jsonfile', metavar = 'JSONFILE', type = str, action = 'store', default =
                       'processed_stuff.json',
                       help = 'Name of the JSON file to store progress-as-you-go-along on directory dehydration. Default file name = "processed_stuff.json".' )
  parser.add_argument( '-S', '--subtitle', dest = 'do_add_subtitle', action = 'store_true', default = False,
                       help = 'If chosen, then AFTER subtitle creation, merge SRT subtitles with original file.' )
  #
  ## parsing arguments
  time0 = time.perf_counter( )
  args = parser.parse_args( )
  logger = logging.getLogger( )
  if args.do_info: logger.setLevel( logging.INFO )
  jsonfile = os.path.expanduser( args.parser_dehydrate_jsonfile )
  assert( os.path.basename( jsonfile ).endswith( '.json' ) )
  #
  directory_names = sorted(set(filter(os.path.isdir, map(lambda dirname: os.path.realpath( os.path.expanduser( dirname ) ), args.directories ) ) ) )
  #
  process_multiple_directories_subtitles(
    directory_names = directory_names,
    output_json_file = jsonfile,
    do_add_subtitle = args.do_add_subtitle )
