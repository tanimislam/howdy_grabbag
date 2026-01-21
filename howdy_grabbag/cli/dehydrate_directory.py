"""
This goes through *multiple* directories you specify, and tries to *shrink*  *shrink* episodes (using HEVC_ video quality 28) that start off with a bit rate *above* a certain level, by default 2000 kbps.

.. _HEVC: https://en.wikipedia.org/wiki/High_Efficiency_Video_Coding
"""
import os, sys, logging, time, pandas, numpy, json, subprocess, shutil, uuid, glob
from tabulate import tabulate
from itertools import chain
from howdy_grabbag.utils.dehydrate import (
    find_files_to_process,
    find_files_to_process_AVI,
    process_multiple_directories,
    process_multiple_directories_AVI,
    process_multiple_directories_subtitles,
    process_multiple_directories_lower_audio,
    process_multiple_files,
    process_multiple_files_AVI,
    process_multiple_files_lower_audio )
    
from argparse import ArgumentParser

def _get_directory_names( all_directories ):
    directories_not_globs = set(filter(lambda dirname: '*' not in dirname, all_directories ) )
    directories_globs     = set(filter(lambda dirname: '*' in dirname, all_directories ) )
    directory_names_1 = set(filter(os.path.isdir, map(lambda dirname: os.path.realpath( os.path.expanduser( dirname ) ), directories_not_globs ) ) )
    directory_names_2 = set(filter(os.path.isdir, map(lambda dirname: os.path.realpath( os.path.expanduser( dirname ) ),
                                                      chain.from_iterable(map(lambda globdir: glob.glob( globdir ), directories_globs ) ) ) ) )
    directory_names   = sorted( directory_names_1 | directory_names_2 )
    return directory_names


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
    parser.add_argument( '-B', '--bitrate', dest = 'parser_audio_bitstring', metavar = 'BITRATE', type = str, action = 'store', default = '160',
                         help = 'Will dehydrate shows using this audio bitrate in KBPS, or using value = "copy". Default is 160.' )
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
    directory_names = _get_directory_names( args.directories )
    #
    ## dehydrate directory
    quality = args.parser_dehydrate_quality
    jsonfile = os.path.expanduser( args.parser_dehydrate_jsonfile )
    assert( os.path.basename( jsonfile ).endswith( '.json' ) )
    assert( quality >= 20 )
    #
    ##
    audio_bit_string = args.parser_audio_bitstring.strip( ).lower( )
    if audio_bit_string != 'copy':
        assert( audio_bit_string.isdigit( ) )
    if not args.do_avi:
        process_multiple_directories(
            directory_names = directory_names, do_hevc = args.do_hevc,
            min_bitrate = args.minbitrate, qual = quality,
            audio_bit_string = audio_bit_string,
            output_json_file = jsonfile )
    else:
        process_multiple_directories_AVI(
            directory_names = directory_names,
            qual = quality,
            output_json_file = jsonfile )

def main_lower_audio( ):
    parser = ArgumentParser( )
    parser.add_argument( '-d', '--directories', dest='directories', type=str, action = 'store', nargs = '+', default = [ os.getcwd( ), ],
                        help = 'Name of the directories of MKV and MP4 files to dehydrate. Default is %s.' % [ os.getcwd( ), ] )
    parser.add_argument( '-M', '--minaudiobitrate', dest = 'minaudiobitrate', type = int, action = 'store', default = 256,
                        help = ' '.join([
                            'The minimum audio bitrate (in kbps) of episodes to lower the audio bitrate. Must be >= 10 kbps.',
                            'Default is 256 kbps.']))
    parser.add_argument( '--info', dest='do_info', action='store_true', default = False,
                        help = 'If chosen, then turn on INFO logging.' )
    #
    ## lower_audio arguments
    parser.add_argument( '-B', '--bitrate', dest = 'parser_new_audio_bit_rate', metavar = 'BITRATE', type = int, action = 'store', default = 160,
                         help = 'Will lower the audio bitrate down to these many kbps. Must be >= 10 kbps. Default is 160 kbps.' )
    parser.add_argument( '-J', '--jsonfile', dest = 'parser_lower_audio_jsonfile', metavar = 'JSONFILE', type = str, action = 'store',
                         default = 'processed_stuff_audio.json',
                         help = 'Name of the JSON file to store progress-as-you-go-along on directory dehydration. Default file name = "processed_stuff_audio.json".' )
    #
    ## parsing arguments
    time0 = time.perf_counter( )
    args = parser.parse_args( )
    assert( args.minaudiobitrate >= 10 )
    logger = logging.getLogger( )
    if args.do_info: logger.setLevel( logging.INFO )
    #
    directory_names = _get_directory_names( args.directories )
    #
    ## dehydrate directory
    jsonfile = os.path.expanduser( args.parser_lower_audio_jsonfile )
    assert( os.path.basename( jsonfile ).endswith( '.json' ) )
    assert( args.parser_new_audio_bit_rate >= 10 )
    #
    process_multiple_directories_lower_audio(
        directory_names = directory_names,
        min_audio_bit_rate = args.minaudiobitrate,
        new_audio_bit_rate = args.parser_new_audio_bit_rate,
        output_json_file = jsonfile )

def main_lower_audio_files( ):
    parser = ArgumentParser( )
    parser.add_argument( '-i', '--input', dest='inputfiles', type=str, action = 'store', required = True, nargs = '+',
                         help = 'Name of the single olr multiple MKV or MP4 file to dehydrate.' )
    parser.add_argument( '-M', '--minaudiobitrate', dest = 'minaudiobitrate', type = int, action = 'store', default = 256,
                        help = ' '.join([
                            'The minimum audio bitrate (in kbps) of episodes to lower the audio bitrate. Must be >= 10 kbps.',
                            'Default is 256 kbps.']))
    parser.add_argument( '--info', dest='do_info', action='store_true', default = False,
                         help = 'If chosen, then turn on INFO logging.' )
    #
    ## lower_audio arguments
    parser.add_argument( '-B', '--bitrate', dest = 'parser_new_audio_bit_rate', metavar = 'BITRATE', type = int, action = 'store', default = 160,
                         help = 'Will lower the audio bitrate down to these many kbps. Must be >= 10 kbps. Default is 160 kbps.' )
    parser.add_argument( '-J', '--jsonfile', dest = 'parser_lower_audio_jsonfile', metavar = 'JSONFILE', type = str, action = 'store',
                         default = 'processed_stuff_audio.json',
                         help = 'Name of the JSON file to store progress-as-you-go-along on directory dehydration. Default file name = "processed_stuff_audio.json".' )
    #
    ## parsing arguments
    time0 = time.perf_counter( )
    args = parser.parse_args( )
    assert( args.minaudiobitrate >= 10 )
    logger = logging.getLogger( )
    if args.do_info: logger.setLevel( logging.INFO )
    #
    directory_names = _get_directory_names( args.directories )
    #
    ## dehydrate directory
    jsonfile = os.path.expanduser( args.parser_lower_audio_jsonfile )
    assert( os.path.basename( jsonfile ).endswith( '.json' ) )
    assert( args.parser_new_audio_bit_rate >= 10 )
    #
    process_multiple_files_lower_audio(
        args.inputfiles,
        min_audio_bit_rate = args.minaudiobitrate,
        new_audio_bit_rate = args.parser_new_audio_bit_rate,
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
    directory_names = _get_directory_names( args.directories )
    #directory_names = sorted(set(filter(os.path.isdir, map(lambda dirname: os.path.realpath( os.path.expanduser( dirname ) ), args.directories ) ) ) )
    #
    ## list filenames
    if not args.do_avi:
        fnames_dict = find_files_to_process(
            directory_names = directory_names,
            do_hevc = args.do_hevc, min_bitrate = args.minbitrate )
        data = list( zip(
            map(os.path.basename, sorted( fnames_dict ) ),
            map(lambda fname: '%0.1f' % fnames_dict[ fname ][ 'bit_rate_kbps' ], sorted( fnames_dict ) ),
            map(lambda fname: '%0.1f' % fnames_dict[ fname ][ 'audio_bit_rate_kbps' ], sorted( fnames_dict ) ) ) )
        print( 'found %02d valid files in %s with min bitrate >= %d kbps.\n' % (
            len( fnames_dict ), directory_names, args.minbitrate ) )
        print( '%s\n' % tabulate( data, headers = [ 'FILENAME', 'KBPS', 'AUDIO KBPS' ] ) )
        return
    #
    fnames_dict_AVI = find_files_to_process_AVI(
        directory_names = directory_names )
    data_AVI = list( zip(
        map(os.path.basename, sorted( fnames_dict_AVI ) ),
        map(lambda fname: '%0.1f' % fnames_dict_AVI[ fname ][ 'bit_rate_kbps' ], sorted( fnames_dict_AVI ) ),
        map(lambda fname: '%0.1f' % fnames_dict_AVI[ fname ][ 'audio_bit_rate_kbps' ], sorted( fnames_dict_AVI ) ) ) )
    print( 'found %02d valid files in %s with min bitrate >= %d kbps.\n' % (
        len( fnames_dict_AVI ), directory_names, args.minbitrate ) )
    print( '%s\n' % tabulate( data_AVI, headers = [ 'FILENAME', 'KBPS', 'AUDIO KBPS' ] ) )
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
    directory_names = sorted(set(filter(os.path.isdir, map(lambda dirname: os.path.realpath(
        os.path.expanduser( dirname ) ), args.directories ) ) ) )
    #
    process_multiple_directories_subtitles(
        directory_names = directory_names,
        output_json_file = jsonfile,
        do_add_subtitle = args.do_add_subtitle )

def main_dehydrate_files( ):
    parser = ArgumentParser( )
    parser.add_argument( '-i', '--input', dest='inputfiles', type=str, action = 'store', required = True, nargs = '+',
                         help = 'Name of the single olr multiple MKV or MP4 file to dehydrate.' )
    parser.add_argument( '--info', dest='do_info', action='store_true', default = False,
                         help = 'If chosen, then turn on INFO logging.' )
    parser.add_argument( '-A', '--doavi', dest = 'do_avi', action = 'store_true', default = False,
                         help = 'If chosen, then process AVI and MPEG files for dehydration at higher qualities.' )
    #
    ##
    parser.add_argument( '-Q', '--quality', dest = 'parser_dehydrate_quality', metavar = 'QUALITY', type = int, action = 'store',
                         default = 28, help = 'Will dehydrate shows using HEVC video codec with this quality. Default is 28. Must be >= 20.' )
    parser.add_argument( '-B', '--bitrate', dest = 'parser_audio_bitstring', metavar = 'BITRATE', type = str, action = 'store', default = '160',
                         help = 'Will dehydrate shows using this audio bitrate in KBPS, or using value = "copy". Default is 160.' )
    parser.add_argument( '-J', '--jsonfile', dest = 'parser_dehydrate_jsonfile', metavar = 'JSONFILE', type = str, action = 'store', default = 'processed_stuff.json',
                         help = 'Name of the JSON file to store progress-as-you-go-along on directory dehydration. Default file name = "processed_stuff.json".' )
    #
    ## parsing arguments
    time0 = time.perf_counter( )
    args = parser.parse_args( )
    logger = logging.getLogger( )
    if args.do_info: logger.setLevel( logging.INFO )
    #
    ## dehydrate files
    quality = args.parser_dehydrate_quality
    jsonfile = os.path.realpath( os.path.expanduser( args.parser_dehydrate_jsonfile ) )
    assert( os.path.basename( jsonfile ).endswith( '.json' ) )
    assert( quality >= 20 )
    #
    ##
    #
    ##
    audio_bit_string = args.parser_audio_bitstring.strip( ).lower( )
    if audio_bit_string != 'copy':
        assert( audio_bit_string.isdigit( ) )
    #
    if not args.do_avi:
        process_multiple_files(
            args.inputfiles, qual = quality,
            audio_bit_string = audio_bit_string,
            output_json_file = jsonfile )
        return
    #
    process_multiple_files_AVI(
        args.inputfiles, qual = quality,
        output_json_file = jsonfile )
