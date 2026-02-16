import os, sys, numpy, glob, pandas, time, datetime, logging
from howdy.music import music_spotify
from itertools import chain
from pathos.multiprocessing import Pool, cpu_count
from argparse import ArgumentParser

def main( ):
    parser = ArgumentParser( )
    parser.add_argument( '-i', '--input', dest = 'input', type = str, action = 'store', required = True,
                        help = 'The input HDF5 serialized Pandas DataFrame containing the playlist info.' )
    parser.add_argument( '-o', '--output', dest = 'output', type = str, action = 'store', required = True,
                        help = 'The output HDF5 serialized Pandas DataFrame containing the playlist info containing SPOTIFY IDs.' )
    parser.add_argument( '-N', '--nprocs', dest = 'nprocs', type = int, action = 'store', default = cpu_count( ),
                        help = 'The number of processors over which to split the work of getting SPOTIFY IDs. Must be >= 1. Default = %d.' %
                        cpu_count( ) )
    parser.add_argument( '-I', '--info', dest = 'do_info', action = 'store_true', default = False,
                        help = 'If chosen, turn on INFO logging.' )
    #
    ##
    args = parser.parse_args( )
    logger = logging.getLogger( )
    if args.do_info: logger.setLevel( logging.INFO )
    #
    ## input = must
    df_playlist_file = os.path.realpath( os.path.expanduser( args.input ) )
    assert( os.path.isfile( df_playlist_file ) )
    assert( os.path.basename( df_playlist_file ).endswith( '.h5' ) )
    df_playlist = pandas.read_hdf( df_playlist_file )
    #
    ## this dataframe MUST have these columns
    assert( len( set( ['added date',
                       'album',
                       'album number of tracks',
                       'album year',
                       'artist',
                       'filename',
                       'order in playlist',
                       'song name',
                       'track number'] ) - set( df_playlist.keys( ) ) ) == 0 )
    #
    ## the output file MUST end in h5
    output_file = os.path.expanduser( args.output )
    assert( os.path.basename( output_file ).endswith( '.h5' ) )
    #
    ## numprocs MUST be >= 1
    assert( args.nprocs >= 1 )
    #
    ## now do the calculation after validation stuff
    time0 = time.perf_counter( )
    #
    ## spotify session token
    spotify_access_token = music_spotify.get_spotify_session( )
    #
    df_playlist_spotify = music_spotify.process_dataframe_playlist_spotify_multiproc(
        df_playlist, spotify_access_token, args.nprocs )
    ngoods = df_playlist_spotify[ df_playlist_spotify[ 'SPOTIFY ID' ].str.startswith(
        'spotify:track:' ) ].shape[ 0 ]
    print( 'found %d / %d good SPOTIFY IDs in playlist = %s.' % (
        ngoods, df_playlist.shape[ 0 ], df_playlist_file ) )
    df_playlist_spotify.to_hdf( output_file, key = 'data' )
    logging.info( 'took %0.3f seconds to find and push SPOTIFY IDs.' % (
        time.perf_counter( ) - time0 ) )
    
def main_fix_bad( ):
    parser = ArgumentParser( )
    parser.add_argument( '-i', '--input', dest = 'input', type = str, action = 'store', required = True,
                        help = 'The output HDF5 serialized Pandas DataFrame containing the playlist info containing SPOTIFY IDs.' )
    parser.add_argument( '-N', '--nprocs', dest = 'nprocs', type = int, action = 'store', default = cpu_count( ),
                        help = 'The number of processors over which to split the work of getting SPOTIFY IDs. Must be >= 1. Default = %d.' %
                        cpu_count( ) )
    parser.add_argument( '-I', '--info', dest = 'do_info', action = 'store_true', default = False,
                        help = 'If chosen, turn on INFO logging.' )
    #
    ##
    args = parser.parse_args( )
    logger = logging.getLogger( )
    if args.do_info: logger.setLevel( logging.INFO )
    #
    ## input = must
    df_playlist_file = os.path.realpath( os.path.expanduser( args.input ) )
    assert( os.path.isfile( df_playlist_file ) )
    assert( os.path.basename( df_playlist_file ).endswith( '.h5' ) )
    df_playlist = pandas.read_hdf( df_playlist_file )
    #
    ## this dataframe MUST have these columns
    assert( len( set( ['added date',
                       'album',
                       'album number of tracks',
                       'album year',
                       'artist',
                       'filename',
                       'order in playlist',
                       'song name',
                       'track number', 'SPOTIFY ID', ] ) - set( df_playlist.keys( ) ) ) == 0 )
    #
    ## numprocs MUST be >= 1
    assert( args.nprocs >= 1 )
    #
    ## now do the calculation after validation stuff
    time0 = time.perf_counter( )
    #
    ## spotify session token
    spotify_access_token = music_spotify.get_spotify_session( )
    #
    with Pool( processes = args.nprocs ) as pool: 
        ngoods_rows_tuples = list(
            pool.map(
              lambda idx: music_spotify.process_dataframe_playlist_spotify_bads(
                  df_playlist[idx::args.nprocs], spotify_access_token ),
              range( args.nprocs ) ) )
        ngoods_tots = sum(list(map(lambda tup: tup[0], ngoods_rows_tuples ) ) )
        nrows_tots  = sum(list(map(lambda tup: tup[1], ngoods_rows_tuples ) ) )
        print( 'fixed total of %d / %d bad SPOTIFY IDs in playlist = %s.' % (
            ngoods_tots, nrows_tots, df_playlist_file ) )
        logging.info( 'took %0.3f seconds to find and fix bad SPOTIFY IDs.' % (
            time.perf_counter( ) - time0 ) )
