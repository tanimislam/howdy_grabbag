import os, sys, logging, subprocess, time, json
from pathos.multiprocessing import Pool, cpu_count
from howdy.tv import tv_attic
from howdy_grabbag.utils import (
    get_directory_names, dvd_utils )
from howdy_grabbag import (
    nice_exec, hcli_exec, mkvpropedit_exec )
from itertools import chain
from argparse import ArgumentParser

def find_all_title_tuples_in_order(
    directory_names, min_duration_mins = 19 ):
    #
    with Pool( processes = cpu_count( ) ) as pool:
        directories_from_glob = sorted(
            filter(lambda entry: len( entry[1] ) > 0,
                   pool.map(
                       lambda dirname: (dirname, dvd_utils.get_dvd_chapter_infos_in_directory(
                           dirname, min_duration_mins = min_duration_mins ) ),
                       directory_names ) ),
            key = lambda entry: entry[0] )
        logging.debug( directories_from_glob )
    title_tuples_in_order = sorted(
        chain.from_iterable(map(lambda entry: map(lambda num: (
            os.path.join( entry[0], 'VIDEO_TS' ), num ), sorted( entry[ 1 ] ) ),
                                directories_from_glob ) ) )
    return title_tuples_in_order

def process_single_episode_in_order(
    showname, epdicts_sub, inputdir, titnum, epno, seasno, outdir, quality = 22 ):
    #
    assert( seasno in epdicts_sub )
    assert( epno in epdicts_sub[ seasno ] )
    assert( os.path.isdir( outdir ) )
    #
    ## newfile
    newfile = os.path.join( outdir, '%s - s%02de%02d - %s.mkv' % (
        showname, seasno, epno, epdicts_sub[ seasno ][ epno ] ) )
    #
    ## now the process
    stdout_val = subprocess.check_output([
        nice_exec, '-n', '19', hcli_exec,
        '-i', inputdir, '-t', '%d' % titnum, '-e', 'x265', '-q', '%d' % quality, '-B', '160',
        '-s', '1,2,3,4,5', '-a', '1,2,3,4,5', '-o', newfile ], stderr = subprocess.STDOUT )
    logging.debug( stdout_val.decode( 'utf8' ) )
    #
    stdout_val = subprocess.check_output([
        nice_exec, '-n', '19', mkvpropedit_exec,
        newfile, '--add-track-statistics-tags' ], stderr = subprocess.STDOUT )
    logging.debug( stdout_val.decode( 'utf8' ) )
    return newfile

def process_single_season(
        directory_names, showname, seasno, outdir, jsonfile, quality = 22, min_duration_mins = 19,
        firstAiredYear = None ):
    assert( os.path.isdir( outdir ) )
    assert( os.path.basename( jsonfile ).endswith( '.json' ) )
    title_tuples_in_order = find_all_title_tuples_in_order(
        directory_names, min_duration_mins = min_duration_mins )
    #
    epdicts = tv_attic.get_tot_epdict_tmdb(
        showname, firstAiredYear = firstAiredYear, showSpecials = True )
    epdicts_sub = { seasno : { epno : epdicts[seasno][epno][0].replace("/", "; ") for
                               epno in epdicts[seasno] } for seasno in epdicts }
    if seasno not in epdicts_sub:
        print( "ERROR, SEASON %d NOT IN %s." % ( seasno, showname.upper( ) ) )
        return
    if len( title_tuples_in_order ) != len( epdicts_sub[ seasno ] ):
        print( "NUMBER OF EPISODES TO CONVERT FOR SEASON %d = %d." % (
            seasno, len( title_tuples_in_order ) ) )
        print( "NUMBER OF EPISODES FOUND FOR %s SEASON %d = %d." % (
            showname.upper( ), seasno, len( epdicts_sub[ seasno ] ) ) )
        if len( title_tuples_in_order ) > len( epdicts_sub[ seasno ] ):
            print( ' '.join([
                "SINCE NUMBER OF EPISODES TO CONVERT FOR SEASON %d = %d >" % (
                    seasno, len( title_tuples_in_order ) ),
                "NUMBER OF EPISODES FOUND FOR %s SEASON %d = %d," % (
                    showname.upper( ), seasno, len( epdicts_sub[ seasno ] ) ),
                "WE WILL EXIT." ]) )
            return
        print( ' '.join([
            "SINCE NUMBER OF EPISODES TO CONVERT FOR SEASON %d = %d <" % (
                seasno, len( title_tuples_in_order ) ),
            "NUMBER OF EPISODES FOUND FOR COSBY 1996 SEASON %d = %d," % (
                seasno, len( epdicts_sub[ seasno ] ) ),
            "WE WILL CONVERT IN ORDER." ]) )
    #
    ##
    time00 = time.perf_counter( )
    list_processed = [ 'found %02d episodes to process for season %d in "%s".' % (
        len( title_tuples_in_order ), seasno, directory_names ), ]
    json.dump( list_processed, open( jsonfile, 'w' ), indent = 1 )
    for idx, entry in enumerate( title_tuples_in_order ):
        time0 = time.perf_counter( )
        inputdir, titnum = entry
        #
        newfile = process_single_episode_in_order(
            showname, epdicts_sub, inputdir, titnum, idx + 1, seasno, outdir, quality = quality )
        #
        os.chmod(newfile, 0o644 )   
        dt0 = time.perf_counter( ) - time0        
        list_processed.append( 'processed episode %02d / %02d in %0.3f seconds' % (
            idx + 1, len( title_tuples_in_order ), dt0 ) )
        json.dump( list_processed, open( jsonfile, 'w' ), indent = 1 )
    dt00 = time.perf_counter( ) - time00
    list_processed.append( 'took %0.3f seconds to process %d episodes' % (
        dt00, len( title_tuples_in_order ) ) )
    json.dump( list_processed, open( jsonfile, 'w' ), indent = 1 )
    
def main( ):
    """
    Example command to run:

    dvd_to_mkv -d "EERIE_INDIANA_DISC_*" -o mov -s "Eerie, Indiana" -S 1 -Q 22 -J processed_s01.json -m 19
    
    """
    parser = ArgumentParser( )
    parser.add_argument( '-d', '--directories', dest='directories', type=str, action = 'store', nargs = '+', default = [ os.getcwd( ), ],
                        help = 'Name of the DVD directories to create episodes. Default is %s.' % [ os.getcwd( ), ] )
    parser.add_argument( '-o', '--outdir', dest = 'outdir', type = str, action = 'store', required = True,
                         help = 'The output directory into which to store the TV show episodes.' )
    parser.add_argument( '-s', '--showname', dest = 'showname', type = str, action = 'store', required = True,
                         help = 'The name of the TV show to look for.' )    
    parser.add_argument( '-S', '--season', dest = 'season', type = int, action = 'store', default = 1,
                         help = 'The season number of the DVD collection needed to process. Default is 1.' )    
    parser.add_argument( '-F', '--firstAiredYear', type=int, action='store',
                       help = 'Year in which the first episode of the TV show aired.' )
    parser.add_argument( '-Q', '--quality', dest = 'quality', type = int, action = 'store',
                         default = 22, help = 'Will dehydrate shows using HEVC video codec with this quality. Default is 22. Must be >= 20.' )
    parser.add_argument( '-m', '--min_duration_mins', dest = 'min_duration_mins', type = int, action = 'store', default = 19,
                         help = 'The minimum duration of DVD titles on disk to be considered an episode. Default is 19. Must be >= 12.' )
    parser.add_argument( '-J', '--jsonfile', dest = 'jsonfile', type = str, action = 'store', 
                         default = 'processed_stuff.json',
                         help = ' '.join([
                             'Name of the JSON file used to write out the progress of the DVD ripping.'
                             'Default = "processed_stuff.json".' ]) )
    parser.add_argument( '-D', '--debug', dest = 'do_debug', action = 'store_true', default = False,
                         help = 'If chosen, then turn on DEBUG LOGGING.' )
    #
    args = parser.parse_args( )
    logger = logging.getLogger( )
    if args.do_debug: logger.setLevel( logging.DEBUG )
    #
    outdir = os.path.realpath( os.path.expanduser( args.outdir ) )
    assert( os.path.isdir( outdir ) )
    #
    directory_names = get_directory_names( args.directories )
    #
    showname = args.showname.strip( )
    epdicts = tv_attic.get_tot_epdict_tmdb(
        showname, firstAiredYear = None, showSpecials = True )
    seasno = args.season
    assert( seasno in epdicts )
    jsonfile = os.path.realpath( os.path.expanduser( args.jsonfile ) )
    assert( os.path.basename( jsonfile ).endswith( '.json' ) )
    #
    assert( args.min_duration_mins >= 15 )
    #
    ## now do the things
    process_single_season(
        directory_names,
        showname,
        seasno,
        outdir,
        jsonfile,
        quality = args.quality,
        min_duration_mins = args.min_duration_mins,
        firstAiredYear = args.firstAiredYear )
