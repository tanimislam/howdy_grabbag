import os, sys, glob, subprocess, time, yaml, gzip
from shutil import which
from argparse import ArgumentParser

nice_exec        = which( 'nice' )
mkvmerge_exec    = which( 'mkvmerge' )
mkvpropedit_exec = which( 'mkvpropedit' )
ffmpeg_exec      = which( 'ffmpeg' )

assert( nice_exec is not None )
assert( mkvmerge_exec is not None )
assert( mkvpropedit_exec is not None )
assert( ffmpeg_exec is not None )

def process_mkv_add_subtitles_files(
    mkvfiles,
    srtfiles,
    outdir = os.getcwd( ) ):
    #
    assert( len( mkvfiles ) == len( srtfiles ) )
    time00 = time.perf_counter( )
    for idx, (mkvfile, srtfile) in enumerate(zip(mkvfiles, srtfiles)):
        time0 = time.perf_counter( )
        newfile = os.path.abspath( os.path.join( outdir, os.path.basename( mkvfile ) ) )
        try: stdout_val = subprocess.check_output([
                nice_exec, '-n', '19', mkvmerge_exec, '-o', newfile, mkvfile, '--language', '0:eng',
            '--track-name', '0:English', srtfile ], stderr = subprocess.PIPE )
        except: pass
        try: stdout_val = subprocess.check_output([
                mkvpropedit_exec,
                "--add-track-statistics-tags", newfile ], stderr = subprocess.PIPE )
        except: pass
        os.chmod( newfile, 0o644 )
        os.remove( srtfile )
        os.remove( mkvfile )
        print( 'processed episode %02d / %02d in %0.3f seconds.' % (
            idx + 1, len( mkvfiles ), time.perf_counter( ) - time0 ) )
    #
    print( 'processed %02d episodes in %0.3f seconds.' % (
        len( mkvfiles ), time.perf_counter( ) - time00 ) )

def process_mp4_add_subtitles_files(
    mp4files,
    srtfiles,
    outdir = os.getcwd( ) ):
    #
    assert( len( mp4files ) == len( srtfiles ) )
    time00 = time.perf_counter( )
    for idx, (mp4file, srtfile) in enumerate(zip(mp4files, srtfiles)):
        time0 = time.perf_counter( )
        suffix = os.path.basename( mp4file ).split('.')[-1].strip( )
        newfile = os.path.abspath(
            os.path.join(
                outdir,
                os.path.basename( mp4file ).replace('.%s' % suffix, '.mkv' ) ) )
        try: stdout_val = subprocess.check_output([
                nice_exec, '-n', '19', ffmpeg_exec, '-y', '-i', mp4file, '-i', srtfile,
                '-map', '0:v', '-map', '0:a', '-map', '1:s', '-codec', 'copy',
                newfile ], stderr = subprocess.PIPE )
        except: pass
        try: stdout_val = subprocess.check_output([
                mkvpropedit_exec,
                "--add-track-statistics-tags", newfile ], stderr = subprocess.PIPE )
        except: pass
        os.chmod( newfile, 0o644 )
        os.remove( srtfile )
        os.remove( mp4file )
        print( 'processed episode %02d / %02d in %0.3f seconds.' % (
            idx + 1, len( mp4files ), time.perf_counter( ) - time0 ) )
    #
    print( 'processed %02d episodes in %0.3f seconds.' % (
        len( mp4files ), time.perf_counter( ) - time00 ) )
            
    
def main( ):
    parser = ArgumentParser( )
    parser.add_argument( '-M', '--mkvfiles', dest = 'mkvfiles', type = str, required = True,
                         help = 'Globbed name of the MKV files to add ENGLISH subtitles.' )
    parser.add_argument( '-S', '--srtfiles', dest = 'srtfiles', type = str, required = True,
                         help = 'Globbed name of the SRT files of ENGLISH subtitles to add.' )
    parser.add_argument( '-o', '--outdir', dest = 'outdir', type = str, default = os.getcwd( ),
                         help = ' '.join([
                             'The directory into which to store new MKV files muxed with ENGLISH subtitles.',
                             'Default is %s.' % os.getcwd( ) ] ) )
    #
    args = parser.parse_args( )
    mkvfiles = sorted(set( glob.glob( args.mkvfiles ) ) )
    srtfiles = sorted(set(filter(os.path.isfile, map(os.path.realpath, glob.glob( args.srtfiles ) ) ) ) )
    outdir   = os.path.realpath( os.path.expanduser( args.outdir ) )
    print( "NUMBER OF MKV FILES = %d." % len( mkvfiles ) )
    print( "NUMBER OF SRT FILES = %d." % len( srtfiles ) )
    #
    ## make sure it all works out
    assert( len( mkvfiles ) == len( srtfiles ) )
    assert( os.path.isdir( outdir ) )
    #
    ## now do the processing
    process_mkv_add_subtitles_files(
        mkvfiles,
        srtfiles,
        outdir = outdir )

def main_mp4( ):
    parser = ArgumentParser( )
    parser.add_argument( '-M', '--mp4files', dest = 'mp4files', type = str, required = True,
                         help = 'Globbed name of the MP4/M4V files to add ENGLISH subtitles.' )
    parser.add_argument( '-S', '--srtfiles', dest = 'srtfiles', type = str, required = True,
                         help = 'Globbed name of the SRT files of ENGLISH subtitles to add.' )
    parser.add_argument( '-o', '--outdir', dest = 'outdir', type = str, default = os.getcwd( ),
                         help = ' '.join([
                             'The directory into which to store new MKV files muxed with ENGLISH subtitles.',
                             'Default is %s.' % os.getcwd( ) ] ) )
    #
    args = parser.parse_args( )
    mp4files = sorted(set( glob.glob( args.mp4files ) ) )
    srtfiles = sorted(set(filter(os.path.isfile, map(os.path.realpath, glob.glob( args.srtfiles ) ) ) ) )
    outdir   = os.path.realpath( os.path.expanduser( args.outdir ) )
    print( "NUMBER OF MP4/M4V FILES = %d." % len( mp4files ) )
    print( "NUMBER OF SRT FILES = %d." % len( srtfiles ) )
    #
    ## make sure it all works out
    assert( len( mp4files ) == len( srtfiles ) )
    assert( os.path.isdir( outdir ) )
    #
    ## now do the processing
    process_mp4_add_subtitles_files(
        mp4files,
        srtfiles,
        outdir = outdir )
    
