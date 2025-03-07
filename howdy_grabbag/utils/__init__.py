import os, sys, time, subprocess, glob, json, titlecase, re
from itertools import chain
from shutil import which

def find_ffmpeg_exec( ):
    ffmpeg_exec = which( 'ffmpeg' )
    if ffmpeg_exec is None: return None
    #
    ## now check if we can execute on it
    if os.access( ffmpeg_exec, os.X_OK ): return ffmpeg_exec
    #
    ## otherwise look in /usr/bin
    ffmpeg_exec = which( 'ffmpeg', path='/usr/bin')
    if ffmpeg_exec is None: return None
    if os.access( ffmpeg_exec, os.X_OK ): return ffmpeg_exec
    return None

def create_epdicts_from_jsonfile( jsonfile ):
    assert( os.path.exists( jsonfile ) )
    epdicts_sub = json.load( open( jsonfile, 'r' ) )
    epdicts = { int(seasno) : { int(idx) : titlecase.titlecase( epdicts_sub[seasno][idx] )
                               for idx in epdicts_sub[seasno] } for seasno in epdicts_sub }
    return epdicts

def rename_files_in_directory( epdicts, series_name, seasno = 1, dirname = "." ):
    time0 = time.perf_counter( )
    filedict = { idx + 1:filename for (idx, filename) in enumerate(
        sorted(chain.from_iterable(map(lambda suffix: glob.glob( os.path.join( dirname, "*.%s" % suffix ) ),
                                       ( "mp4", "avi", "mkv", "wmv", "flv", "webm"))))) }
    assert( seasno in epdicts )
    assert( len( set( epdicts[ seasno ] ) - set( filedict ) ) == 0 )
    for epno in sorted( filedict ):
        suffix = re.sub( ".*\.", "", filedict[epno]).strip()
        newfile = os.path.join( dirname, "%s - s%02de%02d - %s.%s" % (
            series_name, seasno, epno, epdicts[seasno][epno], suffix ) )
        os.rename( filedict[ epno ], newfile)
    print( 'processed %02d files in %0.3f seconds.' % (
        len( filedict ), time.perf_counter( ) - time0 ) )

def process_mp4_srt_eps_to_mkv(
    epdicts, series_name, seasno = 1, srtglob = '*.srt',
    ffmpeg_exec = which( 'ffmpeg' ),
    mkvmerge_exec = which( 'mkvmerge' ),
    dirname = "." ):
    #
    assert( ffmpeg_exec is not None )
    assert( mkvmerge_exec is not None )
    mp4files = sorted(glob.glob( os.path.join( dirname, '*.mp4' ) ) )
    srtfiles = sorted(glob.glob( os.path.join( dirname, srtglob ) ) )
    assert( len(mp4files) == len(srtfiles))
    #epdicts_max = set(map(lambda idx: idx + starteps, range(len(mp4files))))
    #assert( len( epdicts_max - set( epdicts[ seasno ] ) ) == 0 )
    assert( all(map(os.path.exists, ( ffmpeg_exec, mkvmerge_exec ) ) ) )
    #
    time00 = time.perf_counter( )
    for idx, tup in enumerate(zip( mp4files, srtfiles ) ):
        time0 = time.perf_counter( )
        epno = sorted( epdicts[ seasno ] )[ idx ]
        mp4file, srtfile = tup
        newfile = os.path.join( dirname, '%s - s%02de%02d - %s.mkv' % (
            series_name, seasno, epno,
            epdicts[seasno][epno].replace( '/', ', ' ) ) )
        stdout_val = subprocess.check_output([
            ffmpeg_exec, '-y', '-i', mp4file, '-codec', 'copy', 'file:%s' % newfile ],
                                             stderr = subprocess.PIPE )
        try:
            stdout_val = subprocess.check_output([
                mkvmerge_exec, '-o', os.path.join( dirname, 'default.mkv' ), newfile,
                '--language', '0:eng', '--track-name', '0:English', srtfile ],
                                                 stderr = subprocess.PIPE )
        except Exception as e:
            pass
        os.rename( os.path.join( dirname, 'default.mkv' ), newfile )
        os.chmod( newfile, 0o644 )
        os.remove( mp4file )
        os.remove( srtfile )
        print( 'processed file %02d / %02d in %0.3f seconds.' % (
            idx + 1, len( mp4files ), time.perf_counter( ) - time0 ) )
    #
    print( 'processed all %02d files in %0.3f seconds.' % (
        len( mp4files ), time.perf_counter( ) - time00 ) ) 
