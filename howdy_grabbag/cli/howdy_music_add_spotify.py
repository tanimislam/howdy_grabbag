import os, sys, logging, tabulate
from argparse import ArgumentParser
#
from howdy.music import music, get_m4a_metadata

def main( ):
    parser = ArgumentParser( )
    parser.add_argument( '-f', '--filename', dest = 'filename', type = str, action = 'store', required = True,
                        help = 'Name of the M4A filename that we want to add SPOTIFY ID. NOTE THAT THIS FILE MUST BE M4A AND HAVE METADATA.' )
    parser.add_argument( '-g', '--get', dest = 'do_get', action = 'store_true', default = False,
                        help = 'If chosen, then JUST GET the SPOTIFY ID from file METADATA.' )
    parser.add_argument( '-p', '--push', dest = 'do_push', action = 'store_true', default = False,
                        help = "If chosen, then JUST PUSH the SPOTIFY ID into the file's METADATA." )
    parser.add_argument( '-F', '--force', dest = 'do_force', action = 'store_true', default = False,
                        help = "If chosen, then FORCE SPOTIFY ID metadata even though file may have SPOTIFY metadata already identified." )
    parser.add_argument( '-i', '--info', dest = 'do_info', action = 'store_true', default = False,
                        help = 'If chosen, then turn on INFO logging.' )
    #
    args = parser.parse_args( )
    logger = logging.getLogger( )
    if args.do_info: logger.setLevel( logging.INFO )
    #
    if len(list(filter(lambda entry: entry is True, ( args.do_push, args.do_get ) ) ) ) != 1:
        print( "ERROR, only one of -p or -g must be chosen. Not BOTH or NEITHER. Exiting..." )
        return
    #
    music_filename = os.path.realpath( os.path.expanduser( args.filename ) )
    assert( os.path.basename( music_filename ).endswith( '.m4a' ) )
    assert( os.path.isfile( music_filename ) )
    data = [ ( 'NAME OF FILE', music_filename ) ]
    song_metadata_dict = get_m4a_metadata( music_filename )
    data.append( ( 'SONG NAME', song_metadata_dict[ 'song' ] ) )
    data.append( ( 'SONG ARTIST', song_metadata_dict[ 'artist' ] ) )
    if 'album' in song_metadata_dict:
        data.append( ( 'SONG ALBUM', song_metadata_dict[ 'album' ] ) )
    if 'date' in song_metadata_dict:
        data.append( ( 'SONG YEAR', song_metadata_dict[ 'date' ].year ) )
    #
    ## get SPOTIFY ACCESS TOKEN
    access_token = music.MusicInfo.get_spotify_session( )
    #
    ## now spotify_id
    spotify_id_in_file = music.get_spotify_song_id_filename( music_filename )
    if spotify_id_in_file is not None:
        data.append( ( 'SPOTIFY ID IN FILE', spotify_id_in_file ) )
    spotify_id = music.get_spotify_song_id( access_token, song_metadata_dict )
    data.append( ( 'SPOTIFY ID', spotify_id ) )
    print( '%s' % tabulate.tabulate( data ) )
    if args.do_get: return
    #
    ## if pushing
    if spotify_id_in_file is None:
        print( 'PUSHING SPOTIFY ID INTO FILE = %s.' % music_filename )
        music.push_spotify_song_id_to_file( spotify_id, music_filename )
        return
    if args.do_force:
        print( 'PUSHING SPOTIFY ID INTO FILE = %s.' % music_filename )
        music.push_spotify_song_id_to_file( spotify_id, music_filename )
        return
    print( 'SPOTIFY ID ALREADY IN FILE = %s. DOING NOTHING.' % music_filename )
    
