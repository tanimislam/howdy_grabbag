import os, sys, glob, subprocess, logging, time, json, re, datetime
from shutil import which
from howdy_grabbag.utils import hcli_exec

def _get_dvd_chapter_infos_from_stdout( 
    stdout_val_line_split, min_duration_mins = 19 ):
    #
    ##
    min_duration = min_duration_mins * 60
    def _return_valid_title( subcoll, min_dur ):
        duration_strings = list(filter(lambda line: line.startswith("+ duration:" ), subcoll))
        assert( len( duration_strings ) == 1 )
        duration_string = max( duration_strings )
        #
        title_number = int( subcoll[0].replace(":", "").strip( ).split()[-1] )
        td = datetime.datetime.strptime(
            re.sub(".*duration:", "", duration_string).strip( ), "%H:%M:%S" ) - \
            datetime.datetime.strptime("00:00:00", "%H:%M:%S" )
        duration_in_secs = td.seconds
        if td.seconds < min_dur:
            return None
        return ( title_number, re.sub(".*duration:", "", duration_string).strip( ) )
            
    starts_of_chapter_lines = sorted(
        map(lambda entry: entry[0],
            filter(lambda entry: entry[1].startswith('+ title'),
                   enumerate( stdout_val_line_split ) ) ) )
    assert( starts_of_chapter_lines[-1] <= len( stdout_val_line_split ) )
    starts_of_chapter_lines.append( 1 + len( stdout_val_line_split ) )
    #
    subcolls = map(lambda entry: stdout_val_line_split[ entry[ 0 ]: entry[ 1 ] ],
                   zip( starts_of_chapter_lines[:-1], starts_of_chapter_lines[1:] ) )
    colls = dict(filter(None, map(
        lambda subcoll: _return_valid_title( subcoll, min_duration ), subcolls ) ) )
    return colls

def _get_stdout_val_line_split( video_ts_dir ):
    stdout_val = subprocess.check_output(
        [ hcli_exec, '-i', video_ts_dir, '-t', '0' ],
        stderr = subprocess.STDOUT )
    stdout_val_line_split = list(
        map(lambda line: line.strip( ),
            filter(lambda line: line.strip( ).startswith( '+' ),
                   stdout_val.decode( 'utf8', 'ignore' ).split( '\n' ) ) ) )
    return stdout_val_line_split
                   
def get_dvd_chapter_infos_in_directory(
    dvd_directory, min_duration_mins = 19 ):
    #
    act_directory = os.path.realpath( dvd_directory )
    if not os.path.isdir( act_directory ):
        return 0
    #
    video_ts_dir = os.path.join(
        act_directory, 'VIDEO_TS' )
    if not os.path.isdir( video_ts_dir ):
        return 0
    #
    stdout_val_line_split = _get_stdout_val_line_split( video_ts_dir )
    #
    dvd_chapter_infos = _get_dvd_chapter_infos_from_stdout(
        stdout_val_line_split, min_duration_mins = min_duration_mins )
    return dvd_chapter_infos
