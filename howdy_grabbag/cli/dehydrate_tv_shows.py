"""
This goes through your Plex_ TV library, on your *local* server, and tries to *shrink* episodes (using HEVC_ video quality 28) that start off with a bit rate *above* a certain level, by default 2000 kbps.

Lots of words, huh?

This can *either* tell a table of TV show data on your locally running Plex_ server, on your selected library. Each row is information about a TV show on the Plex_ library; columns are TV show name, and number of episodes above the default bit rate. Rows are organized from *most* number of episodes to fewest, and only includes those TV shows that have :math:`\ge 1` high bitrate episodes.

.. _Plex: https://plex.tv
.. _HEVC: https://en.wikipedia.org/wiki/High_Efficiency_Video_Coding
"""
import os, sys, logging, time, pandas, numpy, json, subprocess
from howdy.core import core, session
from howdy.tv import tv, get_token, tv_attic, get_tvdb_api, TMDBShowIds
from howdy.music import music
from howdy.movie import tmdb_apiKey
from pathos.multiprocessing import Pool, cpu_count
from tabulate import tabulate
from distutils.spawn import find_executable
from argparse import ArgumentParser

_ffmpeg_exec  = find_executable( 'ffmpeg' )
_ffprobe_exec = find_executable( 'ffprobe' )
assert( _ffmpeg_exec is not None )
assert( _ffprobe_exec is not None )

def get_tv_library_local( library_name = 'TV Shows' ):
    fullURL, token = core.checkServerCredentials( doLocal=True )
    library_names = list( core.get_libraries( token = token ).values( ) )
    assert( library_name in library_names )
    #
    tvdata = core.get_library_data(
        library_name, token = token, num_threads = cpu_count( ) )
    return tvdata

def get_all_durations_dataframe( tvdata, min_bitrate = 2000 ):
    assert( min_bitrate >= 2000 )
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
                durations.append( tvdata[show]['seasons'][seasno]['episodes'][epno]['duration'])
                sizes.append( tvdata[show]['seasons'][seasno]['episodes'][epno]['size'] )
                shows.append( show )
                seasons.append( seasno )
                epnos.append( epno )
                names.append( tvdata[show]['seasons'][seasno]['episodes'][epno]['title'] )
                paths.append( tvdata[show]['seasons'][seasno]['episodes'][epno]['path'] )
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

def single_show_summary_dataframe( df_sub, showname ):
    df_show = df_sub[ df_sub.shows == showname ].copy( )
    assert( len( df_show ) != 0 )
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

def summarize_single_show( df_sub, showname, minbitrate ):
    df_show = single_show_summary_dataframe( df_sub, showname )
    #
    ## now report it out
    print( 'information for %s, which has %d episodes >= %d kbps.\n' % ( showname, len( df_show ), minbitrate ) )
    data = [ [ 'NUM EPISODES', len( df_show ) ], ]
    data.append( [ 'MIN KBPS', df_show[ 'bitrate (kbps)' ].min( ) ] )
    data.append( [ 'MED KBPS', numpy.median( df_show[ 'bitrate (kbps)' ] ) ] )
    data.append( [ 'MAX KBPS', df_show[ 'bitrate (kbps)' ].max( ) ] )
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

def process_single_show( df_sub, showname, do_hevc = True, qual = 28 ):
    #
    ## check we have nice and HandBrakeCLI
    nice_exec = find_executable( 'nice' )
    hcli_exec = find_executable( 'HandBrakeCLI' )
    assert( nice_exec is not None )
    assert( hcli_exec is not None )
    #
    df_show = single_show_summary_dataframe( df_sub, showname )
    df_show_sub = df_show.copy( )
    if not do_hevc:
        df_show_sub = df_show[ df_show[ 'is hevc' ] == False ].copy( )
    #
    ## now process those shows SLOWLY
    time00 = time.perf_counter( )
    df_show_sorted = df_show_sub.sort_values(by=['seasons', 'epnos']).reset_index( )
    episodes_sorted = list( df_show_sorted.paths )
    list_processed = []
    for idx, filename in enumerate(episodes_sorted):
        time0 = time.perf_counter( )
        newfile = os.path.basename( filename )
        stdout_val = subprocess.check_output([
            nice_exec, '-n', '19', hcli_exec,
            '-i', filename, '-e', 'x265', '-q', '%d' % qual, '-B', '160',
            '-s', ','.join(map(lambda num: '%d' % num, range(1,35))), '-o', newfile ],
            stderr = subprocess.PIPE )
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
    

def main( ):
    parser = ArgumentParser( )
    #
    ## top level arguments
    parser.add_argument( '-t', '--tvlibrary', dest='tvlibrary', type=str, action = 'store', default = 'TV Shows',
                        help = 'Name of the TV library on the local PLEX server. Default is "TV Shows".' )
    parser.add_argument( '-M', '--minbitrate', dest = 'minbitrate', type = int, action = 'store', default = 2000,
                        help = ' '.join([
                            'The minimum total bitrate (in kbps) of episodes to dehydrate. Must be >= 2000 kbps.',
                            'Default is 2000 kbps.']))
    parser.add_argument( '--info', dest='do_info', action='store_true', default = False,
                        help = 'If chosen, then turn on INFO logging.' )
    #
    ## check on which TV shows are candidates for dehydration, or to dehydrate specific TV shows.
    subparsers = parser.add_subparsers( help = 'Choose on whether to list the TV shows to dehydrate, or to dehydrate a TV show.',
                                       dest = 'choose_option' )
    parser_listcandidates = subparsers.add_parser( 'list',      help = 'If chosen, then list the TV shows to dehydrate.' )
    parser_dehydrate      = subparsers.add_parser( 'dehydrate', help = 'If chosen, then dehydrate a single TV show.' )
    #
    ## list TV shows, do nothing more
    #
    ## dehydrate a single TV show
    parser_dehydrate.add_argument( '-s', '--show', metavar = 'SHOW', dest = 'parser_dehydrate_show', type = str, action = 'store',
                                  required = True, help = 'Name of a TV show (with episodes to dehydrate).' )
    parser_dehydrate.add_argument( '-I', dest = 'parser_dehydrate_do_info', action = 'store_true', default = False,
                                  help = 'If chosen, then only print out info on the selected TV show.' )
    parser_dehydrate.add_argument( '-Q', '--quality', dest = 'parser_dehydrate_quality', metavar = 'QUALITY', type = int, action = 'store',
                                  default = 28, help = 'Will dehydrate shows using HEVC video codec with this quality. Default is 28. Must be >= 20.' )
    parser_dehydrate.add_argument( '-N', '--nohevc', dest = 'parser_dehydrate_do_hevc', action = 'store_false', default = True,
                                  help = 'If chosen, then only process the big episodes that are NOT HEVC. Default is to process everything.' )
    #
    ## parsing arguments
    time0 = time.perf_counter( )
    args = parser.parse_args( )
    assert( args.minbitrate >= 2000 )
    logger = logging.getLogger( )
    if args.do_info: logger.setLevel( logging.INFO )
    df_sub = get_all_durations_dataframe(
        get_tv_library_local( library_name = args.tvlibrary ),
        min_bitrate = args.minbitrate )
    shownames = set( df_sub.shows )
    #
    ## list TV shows
    if args.choose_option == 'list':
        df_shows = summarize_shows_dataframe( df_sub )
        print( 'found %d shows and %d episodes with episodes >= %d k2bps.' % (
            len( df_shows ), df_shows['num episodes'].sum( ), args.minbitrate ) )
        data = list(zip( list(df_shows.shows), list( df_shows['num episodes'] ),
                        list( df_shows[ 'min kbps' ] ), list( df_shows[ 'med kbps' ] ),
                        list( df_shows[ 'max kbps' ] ) ) )
        print( '%s\n' % tabulate( data, headers = [ 'SHOW', 'NUM EPISODES', 'MIN KBPS', 'MED KBPS', 'MAX KPBS' ] ) )
        print( 'took %0.3f seconds to process.' % ( time.perf_counter( ) - time0 ) )
        return
    #
    ## dehydrate single show
    elif args.choose_option == 'dehydrate':
        showname = args.parser_dehydrate_show
        assert( showname in shownames )
        #
        ## just do info then return
        if args.parser_dehydrate_do_info:
            summarize_single_show( df_sub, showname, args.minbitrate )
            print( 'took %0.3f seconds to process.' % ( time.perf_counter( ) - time0 ) )
            return
        #
        ## now do the big thing
        quality = args.parser_dehydrate_quality
        assert( quality >= 20 )
        process_single_show( df_sub, showname, do_hevc = args.parser_dehydrate_do_hevc,
                            qual = quality )
