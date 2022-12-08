import os, sys, numpy, mutagen.mp4, requests, yt_dlp, time, datetime, magic, io, logging, validators
from enum import Enum
from io import BytesIO
from PIL import Image
from argparse import ArgumentParser
#
from howdy.music.music import get_youtube_file
from howdy.music import fill_m4a_metadata

class IMAGETYPE( Enum ):
    IS_JPEG = 1
    IS_PNG  = 2
    IS_INVALID = -1
    
    @classmethod
    def check_format( cls, fullpath ):
        val = magic.from_file( os.path.abspath( fullpath ) )
        if 'jpeg' in val.lower( ): return IMAGETYPE.IS_JPEG
        if 'png' in val.lower( ): return IMAGETYPE.IS_PNG
        return IMAGETYPE.IS_INVALID

def download_indiv_song(
        input_data, album_cover_filename_or_URL, youtube_URL ):
    song =   '-'.join(map(lambda tok: tok.strip( ), input_data[ 'song' ].split('/')))
    artist = '-'.join(map(lambda tok: tok.strip( ), input_data[ 'artist' ].split('/')))
    album = input_data[ 'album' ]
    trackno = input_data[ 'trackno' ]
    tottracks = input_data[ 'tottracks' ]
    assert( trackno > 0 )
    assert( tottracks > 0 )
    assert( tottracks >= trackno )
    #
    year_string_split = list(map(lambda tok: tok.strip( ), input_data[ 'year string' ].split('-')))[:3]
    assert( len( year_string_split ) > 0 )
    year_string = '-'.join( year_string_split )
    #
    outputfile = '%s.%s.m4a' % ( artist, song )
    #
    ## first check if the thing is an URL
    if validators.url( album_cover_filename_or_URL ):
        get_youtube_file( youtube_URL, outputfile )
        fill_m4a_metadata(
            outputfile,
            { 'song' : song, 'album' : album, 'artist' : artist, 'year' : year_string,
              'tracknumber' : trackno, 'total tracks' : tottracks, 'album url' : album_cover_filename_or_URL, } )
        mp4tags = mutagen.mp4.MP4( outputfile )
        mp4tags[ 'aART' ] = [ artist, ]
        mp4tags.save( )
        return
    #
    ## then must be a file
    album_cover_filename = album_cover_filename_or_URL
    assert( os.path.exists( album_cover_filename ) )
    val = IMAGETYPE.check_format( album_cover_filename )
    if val == IMAGETYPE.IS_INVALID:
        raise ValueError("Error, %s is not a PNG or JPEG." %
                         os.path.abspath( album_cover_filename ) )
    #
    get_youtube_file( youtube_URL, outputfile )
    #
    fill_m4a_metadata(
        outputfile,
        data_dict = { 'song' : song, 'album' : album, 'artist' : artist, 'year' : year_string,
                      'tracknumber' : trackno, 'total tracks' : tottracks, 'album url' : '', },
        image_data = BytesIO( open( album_cover_filename, 'rb' ).read( ) ) )
    #
    mp4tags = mutagen.mp4.MP4( outputfile )
    mp4tags[ 'aART' ] = [ artist, ]
    mp4tags.save( )

def download_compilation_song(
        input_data, album_cover_filename_or_URL, youtube_URL ):
    song =   '-'.join(map(lambda tok: tok.strip( ), input_data[ 'song' ].split('/')))
    artist = '-'.join(map(lambda tok: tok.strip( ), input_data[ 'artist' ].split('/')))
    album = input_data[ 'album' ]
    trackno = input_data[ 'trackno' ]
    tottracks = input_data[ 'tottracks' ]
    assert( trackno > 0 )
    assert( tottracks > 0 )
    assert( tottracks >= trackno )
    #
    year_string_split = list(map(lambda tok: tok.strip( ), input_data[ 'year string' ].split('-')))[:3]
    assert( len( year_string_split ) > 0 )
    year_string = '-'.join( year_string_split )
    #
    outputfile = '%s.%s.m4a' % ( artist, song )
    #
    ## first check if the thing is an URL
    if validators.url( album_cover_filename_or_URL ):
        get_youtube_file( youtube_URL, outputfile )
        fill_m4a_metadata(
            outputfile,
            { 'song' : song, 'album' : album, 'artist' : artist, 'year' : year_string,
              'tracknumber' : trackno, 'total tracks' : tottracks, 'album url' : album_cover_filename_or_URL, } )
        mp4tags = mutagen.mp4.MP4( outputfile )
        mp4tags[ 'aART' ] = [ 'Various Artists', ]
        mp4tags[ 'cpil' ] = True
        mp4tags.save( )
        return
    #
    ## then must be a file
    album_cover_filename = album_cover_filename_or_URL
    assert( os.path.exists( album_cover_filename ) )
    val = IMAGETYPE.check_format( album_cover_filename )
    if val == IMAGETYPE.IS_INVALID:
        raise ValueError("Error, %s is not a PNG or JPEG." %
                         os.path.abspath( album_cover_filename ) )
    #
    get_youtube_file( youtube_URL, outputfile )
    #
    fill_m4a_metadata(
        outputfile,
        data_dict = { 'song' : song, 'album' : album, 'artist' : artist, 'year' : year_string,
                      'tracknumber' : trackno, 'total tracks' : tottracks, 'album url' : '', },
        image_data = BytesIO( open( album_cover_filename, 'rb' ).read( ) ) )
    #
    mp4tags = mutagen.mp4.MP4( outputfile )
    mp4tags[ 'aART' ] = [ 'Various Artists', ]
    mp4tags[ 'cpil' ] = True
    mp4tags.save( ) 
    # with io.BytesIO( ) as csio2:
    #     img = Image.open( album_cover_filename )
    #     if val == IMAGETYPE.IS_PNG:
    #         img.save( csio2, format = 'png' )
    #         mp4tags[ 'covr' ] = [
    #             mutagen.mp4.MP4Cover( csio2.getvalue( ),
    #                                     mutagen.mp4.MP4Cover.FORMAT_PNG ), ]
    #     else:
    #         img.save( csio2, format = 'jpeg' )
    #         mp4tags[ 'covr' ] = [
    #                 mutagen.mp4.MP4Cover( csio2.getvalue( ),
    #                                      mutagen.mp4.MP4Cover.FORMAT_JPEG ), ]
    # mp4tags.save( )

def main_compilation( ):
    parser = ArgumentParser( )
    parser.add_argument( '-s', dest = 'song', type = str, required = True, help = 'Name of song in compilation album.' )
    parser.add_argument( '-a', dest = 'artist', type = str, required = True, help = 'Name of the artist in compilation album.' )
    parser.add_argument( '-A', dest = 'album', type = str, required = True, help = 'Name of the compilation album.' )
    parser.add_argument( '-t', dest = 'trackno', type = int, required = True, help = 'Track number of song in compilation album.' )
    parser.add_argument( '-T', dest = 'tottracks', type = int, required = True,
                         help = 'Total number of tracks in compilation album.' )
    parser.add_argument( '-y', dest = 'year_string', type = str, required = True, help = 'Year string (of form YYYY-MM-DD, YYYY-MM, or YYYY) for when compilation album was published.' )
    parser.add_argument( '-f', dest = 'album_cover_filename', type = str, required = True,
                         help = 'Name of the album cover file for the compilation album.' )
    parser.add_argument( '-U', dest = 'youtube_URL', type = str, required = True,
                         help = 'The YouTube URL of the song in the compilation album.' )
    #
    args = parser.parse_args( )
    #
    input_data = {
        'song' : args.song,
        'artist' : args.artist,
        'album' : args.album,
        'trackno' : args.trackno,
        'tottracks' : args.tottracks,
        'year string' : args.year_string, }
    #
    download_compilation_song(
        input_data, args.album_cover_filename, args.youtube_URL )


def main_individual( ):
    parser = ArgumentParser( )
    parser.add_argument( '-s', dest = 'song', type = str, required = True, help = 'Name of song in compilation album.' )
    parser.add_argument( '-a', dest = 'artist', type = str, required = True, help = 'Name of the artist in compilation album.' )
    parser.add_argument( '-A', dest = 'album', type = str, required = True, help = 'Name of the compilation album.' )
    parser.add_argument( '-t', dest = 'trackno', type = int, required = True, help = 'Track number of song in compilation album.' )
    parser.add_argument( '-T', dest = 'tottracks', type = int, required = True,
                         help = 'Total number of tracks in compilation album.' )
    parser.add_argument( '-y', dest = 'year_string', type = str, required = True, help = 'Year string (of form YYYY-MM-DD, YYYY-MM, or YYYY) for when compilation album was published.' )
    parser.add_argument( '-f', dest = 'album_cover_filename', type = str, required = True,
                         help = 'Name of the album cover file for the compilation album.' )
    parser.add_argument( '-U', dest = 'youtube_URL', type = str, required = True,
                         help = 'The YouTube URL of the song in the compilation album.' )
    #
    args = parser.parse_args( )
    #
    input_data = {
        'song' : args.song,
        'artist' : args.artist,
        'album' : args.album,
        'trackno' : args.trackno,
        'tottracks' : args.tottracks,
        'year string' : args.year_string, }
    #
    download_indiv_song(
        input_data, args.album_cover_filename, args.youtube_URL )

    
