r"""
This goes through your Plex_ TV library, on your *local* server, and tries to *shrink* episodes (using HEVC_ video quality 28) that start off with a bit rate *above* a certain level, by default 2000 kbps.

Lots of words, huh?

This can *either* tell a table of TV show data on your locally running Plex_ server, on your selected library. Each row is information about a TV show on the Plex_ library; columns are TV show name, and number of episodes above the default bit rate. Rows are organized from *most* number of episodes to fewest, and only includes those TV shows that have :math:`\ge 1` high bitrate episodes.

.. _Plex: https://plex.tv
.. _HEVC: https://en.wikipedia.org/wiki/High_Efficiency_Video_Coding
"""
import os, sys, time, pandas, numpy, json, subprocess, shutil, re, redis, glob, uuid, logging
from enum import Enum
from howdy.core import core, session
from howdy.tv import tv, get_token, tv_attic, get_tvdb_api, TMDBShowIds
from howdy.music import music
from howdy.movie import tmdb_apiKey
from pathos.multiprocessing import Pool, cpu_count
from tabulate import tabulate
from itertools import chain
from shutil import which

_ffmpeg_exec      = which( 'ffmpeg' )
_ffprobe_exec     = which( 'ffprobe' )
_nice_exec        = which( 'nice' )
_hcli_exec        = which( 'HandBrakeCLI' )
_mkvpropedit_exec = which( 'mkvpropedit' )
assert( _ffmpeg_exec is not None )
assert( _ffprobe_exec is not None )
assert( _nice_exec is not None )
assert( _hcli_exec is not None )
assert( _mkvpropedit_exec is not None )

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
        audio_streams = list(filter(lambda entry: entry['codec_type'] == 'audio', data['streams'] ) )
        try:
            bit_rate_audio_1 = sum(map(lambda entry: float( entry[ 'bit_rate' ] ) / 1_024, audio_streams ) )
        except Exception as e:
            bit_rate_audio_1 = 0
        try:
            bit_rate_audio_2 = sum(map(lambda entry: float( entry[ 'tags']['BPS'] ) / 1_024, audio_streams ) )
        except Exception as e:
            bit_rate_audio_2 = 0
        info[ 'audio_bit_rate_kbps' ] = max( bit_rate_audio_1, bit_rate_audio_2 )
        return info
    except Exception as e:
        logging.debug( 'PROBLEM WITH %s. ERROR MESSAGE = %s.' % (
            os.path.realpath( filename ), str( e ) ) )
        return None

def _get_bitrate_AVI( filename ):
    try:
        data = _get_ffprobe_json( filename )
        info = { 
            'bit_rate_kbps' : float( data['format']['bit_rate' ] ) / 1_024, }
        audio_streams = list(filter(lambda entry: entry['codec_type'] == 'audio', data['streams'] ) )
        try:
            bit_rate_audio_1 = sum(map(lambda entry: float( entry[ 'bit_rate' ] ) / 1_024, audio_streams ) )
        except: bit_rate_audio_1 = 0
        try:
            bit_rate_audio_2 = sum(map(lambda entry: float( entry[ 'tags']['BPS'] ) / 1_024, audio_streams ) )
        except: bit_rate_audio_2 = 0
        info[ 'audio_bit_rate_kbps' ] = max( bit_rate_audio_1, bit_rate_audio_2 )
        return info
    except: return None

def get_tv_library_local( library_name = 'TV Shows' ):
    fullURL, token = core.checkServerCredentials( doLocal=True )
    library_names = list( core.get_libraries( token = token ).values( ) )
    assert( library_name in library_names )
    #
    tvdata = core.get_library_data(
        library_name, token = token, num_threads = cpu_count( ) )
    return tvdata

class DATAFORMAT( Enum ):
    IS_AVI_OR_MPEG = 1
    IS_LATER = 2

    @classmethod
    def check_format( cls, fullpath ):
        basename = os.path.basename( fullpath ).lower( )
        if any( map(lambda suffix: basename.endswith( '.%s' % suffix ), ( 'avi', 'mpg', 'mpeg' ) ) ):
            return DATAFORMAT.IS_AVI_OR_MPEG
        return DATAFORMAT.IS_LATER

#
## process_single_filename_hcli
def process_single_filename_hcli( filename, newfile, qual = 28, audio_bit_string = '160' ):
    def _get_audio_entry_hcli( bit_string ):
        if bit_string.strip( ).isdigit( ):
            num_kbps = int( bit_string )
            assert( num_kbps > 0 )
            return [ '-B', '%d' % num_kbps ]
        if bit_string.strip( ).lower( ) == 'copy':
            return [ '-E', 'copy' ]
        return None
    #
    ##
    audio_entry_hcli = _get_audio_entry_hcli( audio_bit_string )
    if audio_entry_hcli is None:
        raise ValueError("Error, invalid audio bit string = %s." % audio_bit_string )
    logging.debug( 'FILENAME = %s, NEWFILE = %s, AUDIO ENTRY HCLI = %s.' % (
        filename, newfile, audio_entry_hcli ) )
    stdout_val = subprocess.check_output([
        _nice_exec, '-n', '19', _hcli_exec,
        '-i', filename, '-e', 'x265', '-q', '%d' % qual,
        audio_entry_hcli[0], audio_entry_hcli[1],
        '-a', ','.join(map(lambda num: '%d' % num, range(1,35))),
        '-s', ','.join(map(lambda num: '%d' % num, range(1,35))),
        '-o', newfile ], stderr = subprocess.PIPE )
    logging.error( stdout_val.decode( 'utf8' ) )
    if newfile.endswith( '.mkv' ):
        stdout_val = subprocess.check_output([
            _nice_exec, '-n', '19', _mkvpropedit_exec,
            newfile, '--add-track-statistics-tags' ], stderr = subprocess.PIPE )
        logging.error( stdout_val.decode( 'utf8' ) )
            
        
        
def get_all_durations_dataframe( tvdata, min_bitrate = 2000, mode_dataformat = DATAFORMAT.IS_LATER ):
    if mode_dataformat == DATAFORMAT.IS_LATER: assert( min_bitrate >= 1000 )
    sizes = [ ]
    durations = [ ]
    shows = [ ]
    seasons = [ ]
    epnos = [ ]
    names = [ ]
    paths = [ ]
    
    for show in tvdata:
        for seasno in tvdata[show]['seasons']:
            for epno in tvdata[show]['seasons'][seasno]['episodes']:
                mypath = tvdata[show]['seasons'][seasno]['episodes'][epno]['path']
                if mode_dataformat != DATAFORMAT.check_format( mypath ):
                    continue
                durations.append( tvdata[show]['seasons'][seasno]['episodes'][epno]['duration'])
                sizes.append( tvdata[show]['seasons'][seasno]['episodes'][epno]['size'] )
                shows.append( show )
                seasons.append( seasno )
                epnos.append( epno )
                names.append( tvdata[show]['seasons'][seasno]['episodes'][epno]['title'] )
                paths.append( mypath )
    df = pandas.DataFrame({'sizes (MB)' : numpy.array(sizes)/1024**2, 'durations (s)' : durations,
                           'shows' : shows, 'seasons' : seasons, 'epnos' : epnos, 'names' : names,
                          'paths' : paths })
    df['bitrate (kbps)'] = numpy.array( df['sizes (MB)'] ) / numpy.array( df['durations (s)']) * 1024 * 8
    df_sub = df[ (df['bitrate (kbps)'] > min_bitrate ) ].sort_values('bitrate (kbps)', ascending = True).copy( )
    return df_sub


def summarize_shows_dataframe( df_sub ):
    def _get_num_shows( showname ):
        return {
            'num shows' : len( df_sub[ df_sub.shows == showname ] ),
            'min kbps' : df_sub[ df_sub.shows == showname ]['bitrate (kbps)'].min( ),
            'med kbps' : numpy.median( df_sub[ df_sub.shows == showname ]['bitrate (kbps)'] ),
            'max kbps' : df_sub[ df_sub.shows == showname ]['bitrate (kbps)'].max( ),
            }
    dict_of_shows = dict(map(lambda showname: ( showname, _get_num_shows( showname ) ),
                             set( df_sub.shows ) ) )
    df = pandas.DataFrame( {
        'shows' : sorted( dict_of_shows ),
        'num episodes' : list(map(lambda showname: dict_of_shows[ showname ][ 'num shows' ], sorted( dict_of_shows ) ) ),
        'min kbps'     : list(map(lambda showname: dict_of_shows[ showname ][ 'min kbps'  ], sorted( dict_of_shows ) ) ),
        'med kbps'     : list(map(lambda showname: dict_of_shows[ showname ][ 'med kbps'  ], sorted( dict_of_shows ) ) ),
        'max kbps'     : list(map(lambda showname: dict_of_shows[ showname ][ 'max kbps'  ], sorted( dict_of_shows ) ) ),
        } )
    df = df.sort_values( 'num episodes', ascending = False ).copy( )
    return df

def single_show_summary_dataframe( df_sub, showname, mode_dataformat = DATAFORMAT.IS_LATER ):
    df_show = df_sub[ df_sub.shows == showname ].copy( )
    assert( len( df_show ) != 0 )
    if mode_dataformat == DATAFORMAT.IS_AVI_OR_MPEG:
        return df_show
    #
    def get_ffprobe_json( filename ):
        stdout_val = subprocess.check_output(
            [ _ffprobe_exec, '-v', 'quiet', '-show_streams',
             '-show_format', '-print_format', 'json', filename ],
            stderr = subprocess.STDOUT )
        file_info = json.loads( stdout_val )
        return file_info

    def is_hevc( filename ):
        data = get_ffprobe_json( filename )
        return data['streams'][0]['codec_name'].lower( ) == 'hevc'

    with Pool( processes = min( cpu_count( ), len( df_show ) ) ) as pool:
        dict_of_episodes_hevc = dict( pool.map(
            lambda filename: ( filename, is_hevc( filename ) ),
            list( df_show.paths ) ) )
        df_show[ 'is hevc' ] = list(map(lambda filename: dict_of_episodes_hevc[ filename ],
                                        list( df_show.paths ) ) )
        return df_show

def summarize_single_show( df_sub, showname, minbitrate, mode_dataformat = DATAFORMAT.IS_LATER ):
    df_show = single_show_summary_dataframe( df_sub, showname, mode_dataformat = mode_dataformat )
    #
    ## now report it out
    print( 'information for %s, which has %d episodes >= %d kbps.\n' % ( showname, len( df_show ), minbitrate ) )
    data = [ [ 'NUM EPISODES', len( df_show ) ], ]
    data.append( [ 'MIN KBPS', df_show[ 'bitrate (kbps)' ].min( ) ] )
    data.append( [ 'MED KBPS', numpy.median( df_show[ 'bitrate (kbps)' ] ) ] )
    data.append( [ 'MAX KBPS', df_show[ 'bitrate (kbps)' ].max( ) ] )
    if mode_dataformat == DATAFORMAT.IS_AVI_OR_MPEG:
        print( '%s\n' % tabulate( data, headers = [ 'PARAMETER', 'INFO' ] ) )
        return
    #
    if len( df_show[ df_show[ 'is hevc' ] == True ] ) == 0:
        print( '%s\n' % tabulate( data, headers = [ 'PARAMETER', 'INFO' ] ) )
        return
    #
    ## now HEVC episodes
    df_show_ishevc = df_show[ df_show[ 'is hevc' ] == True ].copy( )
    data.append( [ 'NUM HEVC EPISODES', len( df_show_ishevc ) ] )
    data.append( [ 'MIN KBPS HEVC', df_show_ishevc[ 'bitrate (kbps)' ].min( ) ] )
    data.append( [ 'MED KBPS HEVC', numpy.median( df_show_ishevc[ 'bitrate (kbps)' ] ) ] )
    data.append( [ 'MAX KBPS HEVC', df_show_ishevc[ 'bitrate (kbps)' ].max( ) ] )
    print( '%s\n' % tabulate( data, headers = [ 'PARAMETER', 'INFO' ] ) )

def process_single_show( df_sub, showname, do_hevc = True, qual = 28, audio_bit_string = '160' ):
    #
    df_show = single_show_summary_dataframe( df_sub, showname )
    df_show_sub = df_show.copy( )
    if not do_hevc:
        df_show_sub = df_show[ df_show[ 'is hevc' ] == False ].copy( )
    #
    ## now process those shows SLOWLY
    time00 = time.perf_counter( )
    df_show_sorted = df_show_sub.sort_values(by=['seasons', 'epnos']).reset_index( )
    episodes_sorted = sorted( set( df_show_sorted.paths ) )
    list_processed = [ ]
    for idx, filename in enumerate(episodes_sorted):
        time0 = time.perf_counter( )
        newfile = os.path.basename( filename )
        #
        process_single_filename_hcli(
            filename, newfile, qual = qual,
            audio_bit_string = audio_bit_string )
        #
        os.chmod(newfile, 0o644 )   
        shutil.move( newfile, filename )
        dt0 = time.perf_counter( ) - time0
        print('processed episode %02d / %02d in %0.3f seconds' % (
            idx + 1, len( episodes_sorted ), dt0 ) )
        list_processed.append( 'processed episode %02d / %02d in %0.3f seconds' % (
            idx + 1, len( episodes_sorted ), dt0 ) )
        json.dump( list_processed, open( 'processed_stuff.json', 'w' ), indent = 1 )
    dt00 = time.perf_counter( ) - time00
    print( 'took %0.3f seconds to process %d episodes' % (
        dt00, len( episodes_sorted ) ) )
    list_processed.append( 'took %0.3f seconds to process %d episodes' % (
        dt00, len( episodes_sorted ) ) )
    json.dump( list_processed, open( 'processed_stuff.json', 'w' ), indent = 1 )

def process_single_show_avi( df_sub, showname, qual = 20, audio_bit_string = '160' ):
    #
    df_show_sub = single_show_summary_dataframe(
        df_sub, showname, mode_dataformat = DATAFORMAT.IS_AVI_OR_MPEG )
    #
    ## now process those shows SLOWLY
    time00 = time.perf_counter( )
    df_show_sorted = df_show_sub.sort_values(by=['seasons', 'epnos']).reset_index( )
    episodes_sorted = sorted( set( df_show_sorted.paths ) )
    list_processed = [ ]
    #
    ## first go through redis database to see if shows are running
    for idx, filename in enumerate(episodes_sorted):
        time0 = time.perf_counter( )
        dirname = os.path.dirname( filename )
        newfile = re.sub( r'\.avi$', '.mkv', os.path.basename( filename ) )
        try:
            process_single_filename_hcli(
                filename, newfile, qual = qual,
                audio_bit_string = audio_bit_string )
            os.chmod(newfile, 0o644 )
            shutil.move( newfile, dirname )
            os.remove( filename )
            dt0 = time.perf_counter( ) - time0
            print('processed episode %02d / %02d in %0.3f seconds' % (
                idx + 1, len( episodes_sorted ), dt0 ) )
            list_processed.append( 'processed episode %02d / %02d in %0.3f seconds' % (
                idx + 1, len( episodes_sorted ), dt0 ) )
        except:
            try: os.remove( newfile )
            except: pass
            dt0 = time.perf_counter( ) - time0
            print('failed episode %02d / %02d in %0.3f seconds' % (
                idx + 1, len( episodes_sorted ), dt0 ) )
            list_processed.append( 'failed episode %02d / %02d in %0.3f seconds' % (
                idx + 1, len( episodes_sorted ), dt0 ) )
        json.dump( list_processed, open( 'processed_stuff_avi.json', 'w' ), indent = 1 )
    dt00 = time.perf_counter( ) - time00
    print( 'took %0.3f seconds to process %d episodes' % (
        dt00, len( episodes_sorted ) ) )
    list_processed.append( 'took %0.3f seconds to process %d episodes' % (
        dt00, len( episodes_sorted ) ) )
    json.dump( list_processed, open( 'processed_stuff_avi.json', 'w' ), indent = 1 )

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
        qual = 28, output_json_file = 'processed_stuff.json', audio_bit_string = '160' ):
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
        #
        process_single_filename_hcli(
            filename, newfile, qual = qual,
            audio_bit_string = audio_bit_string )
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
    output_json_file = 'processed_stuff.json',
    audio_bit_string = '160',
):
    assert( os.path.basename( output_json_file ).endswith( '.json' ) )
    fnames_dict = find_files_to_process_AVI(
        directory_names = directory_names )
    time00 = time.perf_counter( )
    list_processed = [ 'found %02d files to dehydrate in %s.' % (
        len( fnames_dict ), list(map(os.path.abspath, directory_names ) ) ), ]
    json.dump( list_processed, open( output_json_file, 'w' ), indent = 1 )
    for idx, filename in enumerate(sorted( fnames_dict ) ):
        time0 = time.perf_counter( )
        directory_name = os.path.dirname( filename )
        replacfile = os.path.join(
            directory_name, os.path.basename( filename ).replace('.avi', '.mkv' ) )
        newfile = '.'.join(
            os.path.basename( filename ).replace(":", "-").split('.')[:-1] + [ 'mkv', ] )
        newfile = '%s-%s' % ( str( uuid.uuid4( ) ).split('-')[0].strip( ), newfile )
        #
        process_single_filename_hcli(
            filename, newfile, qual = qual, audio_bit_string = audio_bit_string )
        #
        os.chmod(newfile, 0o644 )
        os.rename( newfile, replacfile )
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

def process_multiple_files(
    file_names, qual = 28, output_json_file = 'processed_stuff.json',
    audio_bit_string = '160',
):
    #
    assert( os.path.basename( output_json_file ).endswith( '.json' ) )
    act_file_names = sorted(filter(os.path.isfile,
                                   set(map(os.path.realpath, file_names))))
    time00 = time.perf_counter( )
    list_processed = [ 'found %02d files to dehydrate.' % ( len( act_file_names ) ), ]
    json.dump( list_processed, open( output_json_file, 'w' ), indent = 1 )
    for idx, filename in enumerate( act_file_names ):
        time0 = time.perf_counter( )
        newfile = '%s-%s' % ( str( uuid.uuid4( ) ).split('-')[0].strip( ), os.path.basename( filename ).replace(":", "-" ) )
        #
        process_single_filename_hcli(
            filename, newfile, qual = qual,
            audio_bit_string = audio_bit_string )
        #
        os.chmod(newfile, 0o644 )
        shutil.move( newfile, filename )
        dt0 = time.perf_counter( ) - time0
        logging.info( 'processed file %02d / %02d in %0.3f seconds' % (
            idx + 1, len( act_file_names ), dt0 ) )
        list_processed.append( 'processed file %02d / %02d in %0.3f seconds' % (
            idx + 1, len( act_file_names ), dt0 ) )
        json.dump( list_processed, open( output_json_file, 'w' ), indent = 1 )
    dt00 = time.perf_counter( ) - time00
    logging.info( 'took %0.3f seconds to process %d files' % (
        dt00, len( act_file_names ) ) )
    list_processed.append( 'took %0.3f seconds to process %d files' % (
        dt00, len( act_file_names ) ) )
    json.dump( list_processed, open( output_json_file, 'w' ), indent = 1 )


def process_multiple_files_AVI(
        file_names, qual = 28, output_json_file = 'processed_stuff.json', audio_bit_string = '160' ):
    #
    assert( os.path.basename( output_json_file ).endswith( '.json' ) )
    act_file_names = sorted(filter(os.path.isfile,
                                   set(map(os.path.realpath, file_names))))
    time00 = time.perf_counter( )
    list_processed = [ 'found %02d files to dehydrate.' % ( len( act_file_names ) ), ]
    json.dump( list_processed, open( output_json_file, 'w' ), indent = 1 )
    for idx, filename in enumerate( act_file_names ):
        time0 = time.perf_counter( )
        replacfile = os.path.join(
            directory_name, os.path.basename( filename ).replace('.avi', '.mkv' ).replace( ".mpg", ".mkv" ) )
        newfile = '.'.join(
            os.path.basename( filename ).replace(":", "-").split('.')[:-1] + [ 'mkv', ] )
        newfile = '%s-%s' % ( str( uuid.uuid4( ) ).split('-')[0].strip( ), newfile )
        #
        process_single_filename_hcli(
            filename, newfile, qual = qual,
            audio_bit_string = audio_bit_string )
        #
        os.chmod(newfile, 0o644 )
        os.rename( newfile, replacfile )
        os.remove( filename )
        dt0 = time.perf_counter( ) - time0
        logging.info( 'processed file %02d / %02d in %0.3f seconds' % (
            idx + 1, len( fnames_dict ), dt0 ) )
        list_processed.append( 'processed file %02d / %02d in %0.3f seconds' % (
            idx + 1, len( fnames_dict ), dt0 ) )
        json.dump( list_processed, open( output_json_file, 'w' ), indent = 1 )
    dt00 = time.perf_counter( ) - time00
    logging.info( 'took %0.3f seconds to process %d files' % (
        dt00, len( act_file_names ) ) )
    list_processed.append( 'took %0.3f seconds to process %d files' % (
        dt00, len( act_file_names ) ) )
    json.dump( list_processed, open( output_json_file, 'w' ), indent = 1 )
