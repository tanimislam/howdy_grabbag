import os, sys, numpy, glob, pandas, time, datetime, logging, tabulate
from pathos.multiprocessing import Pool, cpu_count
from plexapi.server import PlexServer
from howdy.core import core
from howdy.music import music_spotify
from argparse import ArgumentParser

#
## prints out the AUDIO playlists on the local Plex server
def get_plex_audio_playlists( ):
    fullURL, token = core.checkServerCredentials( doLocal=True )
    plex = PlexServer( fullURL, token )
    playlists = list(filter(lambda playlist: playlist.playlistType == 'audio', plex.playlists( ) ) )
    if len( playlists ) == 0:
        print( 'FOUND ZERO AUDIO PLAYLISTS' )
        return
    def _get_playlist_info( playlist ):
        name = playlist.title
        num_items = len( playlist.items( ) )
        added_at = playlist.addedAt.date( )
        updated_at = playlist.updatedAt.date( )
        return {
            'name' : name,
            'number of items' : num_items,
            'added at' : added_at,
            'updated at' : updated_at }
    with Pool( processes = min( len( playlists ), cpu_count( ) ) ) as pool:
        list_of_playlists = sorted(
            pool.map( _get_playlist_info, playlists ),
            key = lambda entry: -entry[ 'number of items' ] )
        df_plex_playlists_summary = pandas.DataFrame({
            'name' : list(map(lambda entry: entry['name'], list_of_playlists ) ),
            'number of items' : numpy.array( list(map(lambda entry: entry['number of items'], list_of_playlists ) ), dtype=int ),
            'created' : list(map(lambda entry: entry['added at'], list_of_playlists ) ),
            'updated' : list(map(lambda entry: entry['updated at'], list_of_playlists ) ) } )
        return df_plex_playlists_summary

def print_plex_audio_playlists( df_plex_playlists_summary ):
    headers = [ 'name', 'number of items', 'created', 'updated' ]
    def _get_data( rowno ):
        df_sub = df_plex_playlists_summary[
            df_plex_playlists_summary.index == rowno ]
        return (
            max( df_sub.name ),
            max( df_sub['number of items' ] ),
            max( df_sub['created'] ).strftime( '%d %B %Y' ),
            max( df_sub['updated'] ).strftime( '%d %B %Y' ) )
    print( 'summary info for %d plex audio playlists.\n' % df_plex_playlists_summary.shape[ 0 ] )
    print( '%s\n' % tabulate.tabulate(
        list(map(_get_data, range( df_plex_playlists_summary.shape[ 0 ] ) ) ),
        headers = headers ) )

def print_spotify_public_playlists( ):
    oauth2_access_token = music_spotify.get_or_push_spotify_oauth2_token( )
    assert( oauth2_access_token is not None )
    spotify_data_playlists = music_spotify.get_public_playlists( oauth2_access_token )
    headers = [ 'name', 'number of items', 'description' ]
    data = list(map(lambda entry: ( entry['name'], entry['number of tracks'], entry['description' ] ),
                    spotify_data_playlists ) )
    print( 'summary info for %d public Spotify audio playlists.\n' % len( spotify_data_playlists ) )
    print( '%s\n' % tabulate.tabulate( data, headers = headers ) )

def main( ):
    time0 = time.perf_counter( )
    #
    parser = ArgumentParser( )
    parser.add_argument(
        '-I', '--info', dest='do_info', action='store_true', default = False,
        help = 'If chosen, then print out INFO level logging statements.' )
    #
    subparsers = parser.add_subparsers(
        #help = '\n'.join([
        #    'Choose one of four options:',
        #    '(plex): list all the PLEX AUDIO playlists on this Plex server',
        #    '(spotify_list): list the public SPOTIFY playlists on your SPOTIFY account',
        #    '(spotify_create): create a public SPOTIFY playlist on your SPOTIFY account',
        #    '(push): make the collection of songs on a specific SPOTIFY playlist match the SPOTIFY-identified songs on the specific PLEX AUDIO playlist.' ] ),
        dest = 'choose_option', required = True )
    #
    ## the plex option
    subparsers_plex = subparsers.add_parser(
        'plex',
        help = 'list all the PLEX audio playlists on the local Plex server.' )
    #
    ## now the spotify list one
    subparsers_spotify_list = subparsers.add_parser(
        'spotify_list',
        help = 'List the public SPOTIFY playlists on your SPOTIFY account.' )
    #
    ## now the spotify create one
    subparsers_spotify_create = subparsers.add_parser(
        'spotify_create',
        help = 'Create a public SPOTIFY playlist on your SPOTIFY account.' )
    subparsers_spotify_create.add_argument(
        '-n', '--name', dest = 'name', type = str, action = 'store',
        help = 'Name of the public SPOTIFY playlist.' )
    subparsers_spotify_create.add_argument(
        '-d', '--description', dest = 'description', type = str, action = 'store',
        help = 'Description of the public SPOTIFY playlist.' )
    #
    ## now the push one
    subparsers_push = subparsers.add_parser(
        'push',
        help = 'make the collection of songs on a specific SPOTIFY playlist match the SPOTIFY-identified songs on the specific PLEX AUDIO playlist.' )
    subparsers_push.add_argument(
        '-i', '--input', dest = 'plex_input', type = str, action = 'store',
        help = 'The input PLEX AUDIO playlist to push into a public SPOTIFY playlist.' )
    subparsers_push.add_argument(
        '-o', '--output', dest = 'spotify_output', type = str, action = 'store',
        help = "The output public SPOTIFY playlist. Intent = the public SPOTIFY playlist's songs will MATCH the PLEX AUDIO playlist's collection of SPOTIFY identified songs." )
    #
    ## now do the needful
    args = parser.parse_args( )
    #
    ## turn on debug logging
    logger = logging.getLogger( )
    if args.do_info: logger.setLevel( logging.INFO )
    #
    ##
    if args.choose_option not in ( 'plex', 'spotify_create', 'spotify_list', 'push' ):
        print( "ERROR, MUST CHOOSE ONE OF 'plex', 'spotify_list', 'spotify_create', or 'push'. Instead chosen %s." %
              args.choose_option )
        return
    #
    ## the plex option
    if args.choose_option == 'plex':
        print_plex_audio_playlists( get_plex_audio_playlists( ) )
    elif args.choose_option == 'spotify_list':
        print_spotify_public_playlists( )
    elif args.choose_option == 'spotify_create':
        pass
    elif args.choose_option == 'push':
        pass
    #
    ## how long did this take?
    print( 'took %0.3f seconds to process.' % ( time.perf_counter( ) - time0 ) )
    
