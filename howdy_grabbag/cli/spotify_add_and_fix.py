import os, sys, numpy, glob, pandas, time, datetime, logging
# from plexapi.server import PlexServer
from itertools import chain
from pathos.multiprocessing import Pool, cpu_count
from argparse import ArgumentParser
#
# from howdy.core import core, get_maximum_matchval
from howdy.music import music

def process_dataframe_playlist_spotify( df_playlist, spotify_access_token ):
    time0 = time.perf_counter( )
    df_dict = df_playlist.to_dict( orient = 'list' )
    #
    ## df_list_proc is the list of dictionaries to process in order with SPOTIFY API
    ## SPOTIFY API process: 1) if SPOTIFY ID in music file, return that; 2) if SPOTIFY ID not in music file, find it out and push into file then return that.
    df_list_proc = list(map(lambda tup: {
        'order' : tup[0], 'filename' : tup[1], 'song' : tup[2], 'artist' : tup[3], 'album' : tup[4], 'year' : tup[5] },
                            zip(
                                df_dict['order in playlist'], df_dict['filename'],
                                df_dict['song name'], df_dict[ 'artist' ], df_dict[ 'album' ],
                                df_dict['album year'] ) ) )

    def _get_process_spotify_id_entry( df_list_entry, access_token ):
        filename = df_list_entry['filename']
        order = df_list_entry['order']
        spotify_id_fname = music.get_spotify_song_id_filename( filename )
        if spotify_id_fname is not None:
            return ( order, spotify_id_fname )
        #
        ## otherwise get spotify ID and push into file
        song_metadata_dict = {
            'song'   : df_list_entry[ 'song'   ],
            'artist' : df_list_entry[ 'artist' ],
            'date'   : datetime.datetime.strptime( '%04d' % df_list_entry[ 'year' ], '%Y' ).date( ),
            'album'  : df_list_entry[ 'album' ]
        }
        spotify_id = music.get_spotify_song_id( access_token, song_metadata_dict )
        music.push_spotify_song_id_to_file( spotify_id, filename )
        #
        ## if is bad
        #if spotify_id.startswith( 'spotify:track:'):
        #    return ( order, spotify_id )
        return ( order, spotify_id )

    spotify_ids_list = sorted(
        map(lambda df_list_entry: _get_process_spotify_id_entry( df_list_entry, spotify_access_token), df_list_proc ),
        key = lambda tup: tup[0] )
    #
    ## number of good SPOTIFY IDs
    ngoods = len(list(filter(lambda tup: tup[1].startswith('spotify:track:'), spotify_ids_list ) ) )
    #
    df_playlist_out = df_playlist.copy( ).sort_values( 'order in playlist' )
    nrows = df_playlist_out.shape[ 0 ]
    ncols = df_playlist_out.shape[ 1 ]
    df_playlist_out.insert( ncols, "SPOTIFY ID", list(zip(*spotify_ids_list ))[1] )
    #
    ##
    logging.info( 'found %02d / %02d good SPOTIFY IDs in playlist dataframe in %0.3f seconds.' % (
        ngoods, nrows, time.perf_counter( ) - time0 ) )
    return df_playlist_out    

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
    spotify_access_token = music.MusicInfo.get_spotify_session( )
    #
    with Pool( processes = args.nprocs ) as pool: 
        df_playlist_spotify = pandas.concat( list(
            pool.map(
              lambda idx: process_dataframe_playlist_spotify( df_playlist[idx::args.nprocs], spotify_access_token ),
              range( args.nprocs ) ) ) ).sort_values( 'order in playlist' )
        ngoods = df_playlist_spotify[ df_playlist_spotify[ 'SPOTIFY ID' ].str.startswith(
            'spotify:track:' ) ].shape[ 0 ]
        print( 'found %d / %d good SPOTIFY IDs in playlist = %s.' % (
            ngoods, df_playlist.shape[ 0 ], df_playlist_file ) )
        df_playlist_spotify.to_hdf( output_file, key = 'data' )
        logging.info( 'took %0.3f seconds to find and push SPOTIFY IDs.' % (
            time.perf_counter( ) - time0 ) )
    
