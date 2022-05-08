import os, sys, time, subprocess, glob
from distutils.spawn import find_executable

def process_mp4_srt_eps_to_mkv( epdicts, series_name, seasno = 1, srtglob = '*.srt' ):
    mp4files = sorted(glob.glob( '*.mp4'))
    srtfiles = sorted(glob.glob( srtglob ) )
    assert( len(mp4files) == len(srtfiles))
    epdicts_max = set(map(lambda idx: idx + 1, range(len(mp4files))))
    assert( len( epdicts_max - set( epdicts[ seasno ] ) ) == 0 )
    ffmpeg_exec   = find_executable( 'ffmpeg' )
    mkvmerge_exec = find_executable( 'mkvmerge' )
    assert( ffmpeg_exec is not None )
    assert( mkvmerge_exec is not None )
    #
    time00 = time.perf_counter( )
    for idx, tup in enumerate(zip( mp4files, srtfiles ) ):
        time0 = time.perf_counter( )
        epno = idx + 1
        mp4file, srtfile = tup
        newfile = '%s - s%02de%02d - %s.mkv' % (
            series_name, seasno, epno, epdicts[seasno][epno] )
        stdout_val = subprocess.check_output([
            ffmpeg_exec, '-y', '-i', mp4file, '-codec', 'copy', 'file:%s' % newfile ],
                                             stderr = subprocess.PIPE )
        try:
            stdout_val = subprocess.check_output([
                mkvmerge_exec, '-o', 'default.mkv', newfile,
                '--language', '0:eng', '--track-name', '0:English', srtfile ],
                                                 stderr = subprocess.PIPE )
        except Exception as e:
            pass
        os.rename( 'default.mkv', newfile )
        os.chmod( newfile, 0o644 )
        os.remove( mp4file )
        os.remove( srtfile )
        print( 'processed file %02d / %02d in %0.3f seconds.' % (
            idx+1, len( mp4files ), time.perf_counter( ) - time0 ) )
    #
    print( 'processed all %02d files in %0.3f seconds.' % (
        len( mp4files ), time.perf_counter( ) - time00 ) ) 
