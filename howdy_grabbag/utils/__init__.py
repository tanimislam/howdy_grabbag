import os, sys, time, subprocess, glob, json, titlecase, re, logging, shlex
from howdy.core import core_rsync, SSHUploadPaths
from itertools import chain
from shutil import which

def find_valid_aliases( mediatype = SSHUploadPaths.MediaType.movie ):
    data_remote_collections = core_rsync.get_remote_connections( )
    valid_aliases = sorted(
        set( filter(lambda alias: data_remote_collections[ alias ][ 'media type' ] == mediatype.name,
                    data_remote_collections ) ) )
    return valid_aliases

def get_rsync_commands_lowlevel(
    alias, subdir, outputfile, mediatype = SSHUploadPaths.MediaType.movie ):
    #
    valid_aliases = find_valid_aliases( mediatype = mediatype )
    if alias not in valid_aliases:
        print( "ERROR, chosen alias = %s for remote %s media directory collection not one of %s." % (
            alias, mediatype.name, valid_aliases ) )
        return None
    remote_collection = core_rsync.get_remote_connections( show_password = True )[ alias ]
    sshpath = remote_collection[ 'ssh path' ]
    maindir = remote_collection[ 'main directory' ]
    finaldir = os.path.join( maindir, subdir )
    #
    logging.info( 'MOVIE FILE TO UPLOAD: %s.' % outputfile )
    logging.info( 'REMOTE %s MEDIA DIRECTORY COLLECTION SSH PATH: %s.' % ( mediatype.name.upper( ), sshpath ) )
    logging.info( 'REMOTE %s MEDIA DIRECTORY COLLECTION UPLOAD DIRECTORY: %s.' % ( mediatype.name.upper( ), finaldir ) )
    status = core_rsync.check_remote_connection_paths(
        sshpath, remote_collection[ 'password' ], finaldir )
    if status != 'SUCCESS':
        logging.debug( "ERROR MESSAGE: %s." % status )
        return None
    #
    ## now the command to upload via rsync
    data_rsync = {
        'password'  : remote_collection[ 'password' ],
        'sshpath'   : sshpath,
        'subdir'    : finaldir,
        'local_dir' : '' }
    mycmd, mxcmd = core_rsync.get_rsync_command(
        data_rsync, outputfile, do_download = False,
        use_local_dir_for_upload = False )
    return mycmd, mxcmd

def get_rsync_commands(
    alias, outputfile, subdir = None, mediatype = SSHUploadPaths.MediaType.movie ):
    #
    valid_aliases = find_valid_aliases( mediatype = mediatype )
    if alias not in valid_aliases:
        print( "ERROR, chosen alias = %s for remote %s media directory collection not one of %s." % (
            alias, mediatype.name, valid_aliases ) )
        return None
    remote_collection = core_rsync.get_remote_connections( show_password = True )[ alias ]
    sshpath = remote_collection[ 'ssh path' ]
    maindir = remote_collection[ 'main directory' ]
    if len( remote_collection[ 'sub directories' ] ) == 0:
        finaldir = maindir
    else:
        if subdir is None:
            print( "ERROR, sub directory key must be one of %s." % sorted( remote_collection[ 'sub directories' ] ) )
            return None
        if subdir not in remote_collection[ 'sub directories' ]:
            print( "ERROR, sub directory key = %s must be one of %s." % (
                subdir,
                sorted( remote_collection[ 'sub directories' ] ) ) )
            return None
        finaldir = os.path.join( maindir, remote_collection[ 'sub directories' ][ subdir ] )
    #
    logging.info( 'MOVIE FILE TO UPLOAD: %s.' % outputfile )
    logging.info( 'REMOTE %s MEDIA DIRECTORY COLLECTION SSH PATH: %s.' % ( mediatype.name.upper( ), sshpath ) )
    logging.info( 'REMOTE %s MEDIA DIRECTORY COLLECTION UPLOAD DIRECTORY: %s.' % ( mediatype.name.upper( ), finaldir ) )
    #
    ## now the command to upload via rsync
    data_rsync = {
        'password'  : remote_collection[ 'password' ],
        'sshpath'   : sshpath,
        'subdir'    : finaldir,
        'local_dir' : '' }
    mycmd, mxcmd = core_rsync.get_rsync_command(
        data_rsync, outputfile, do_download = False,
        use_local_dir_for_upload = False )
    return mycmd, mxcmd


def rsync_upload_mkv( mycmd, mxcmd, numtries = 10 ):
    assert( numtries > 0 )
    mystr_split = [ 'STARTING THIS RSYNC CMD: %s' % mycmd ] # 20260121 TODO: try mycmd
    logging.info( mystr_split[-1] )
    logging.info( 'TRYING UP TO %d TIMES.' % numtries )
    time0 = time.perf_counter( )
    for idx in range( numtries ):
        time00 = time.perf_counter( )
        stdout_val = subprocess.check_output(
            shlex.split( mycmd ), stderr = subprocess.STDOUT )
        if not any(map(lambda line: 'dispatch_run_fatal' in line, stdout_val.decode('utf-8').split('\n'))):
            mystr_split.append(
                'SUCCESSFUL ATTEMPT %d / %d IN %0.3f SECONDS.' % (
                    idx + 1, numtries, time.perf_counter( ) - time00 ) )
            logging.debug( '%s\n' % stdout_val.decode( 'utf-8' ) )
            logging.info( mystr_split[-1] )
            return 'SUCCESS', '\n'.join( mystr_split )
        mystr_split.append('FAILED ATTEMPT %d / %d IN %0.3f SECONDS.' % (
            idx + 1, numtries, time.perf_counter( ) - time00 ) )
        logging.info( mystr_split[-1] )
        logging.debug( '%s\n' % stdout_val.decode( 'utf-8' ) )
    mystr_split.append( 'ATTEMPTED AND FAILED %d TIMES IN %0.3f SECONDS.' % (
        numtries, time.perf_counter( ) - time0 ) )
    logging.info( mystr_split[-1] )
    return 'FAILURE', '\n'.join( mystr_split )

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
                                       ( "mp4", "avi", "mpg", "mkv", "wmv", "flv", "webm", "m4v" ))))) }
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
    assert( len(mp4files) == len(srtfiles)), "ERROR, %d MP4 FILES != %d SRT FILES." % (
      len( mp4files ), len( srtfiles ) )
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

def process_mp4_srt_eps_to_mkv_simple(
    srtglob = '*.srt',
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
        mp4file, srtfile = tup
        newfile = os.path.join( dirname, os.path.basename( mp4file ).replace( '.mp4', '.mkv' ) )
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
