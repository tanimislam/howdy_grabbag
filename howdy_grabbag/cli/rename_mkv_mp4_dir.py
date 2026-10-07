import os, sys, logging, time
from howdy.tv import tv_attic
from howdy_grabbag import utils
from argparse import ArgumentParser

def rename_directory_episodes(
    tvshow, seasno, dirname,
    firstAiredYear = None ):
    #
    time0 = time.perf_counter( )
    assert( os.path.isdir( os.path.realpath( dirname ) ) )
    #
    ## now get the series info - seasno
    epdicts = tv_attic.get_tot_epdict_tmdb(
        tvshow,
        showFuture = True,
        minmatch = 10.0,
        firstAiredYear = firstAiredYear )
    assert( epdicts is not None )
    assert( seasno in epdicts )
    epdicts_sub = {
        seasno : { epno : epdicts[seasno][epno][0].replace("/", "; ") for
                  epno in epdicts[seasno] } for seasno in epdicts }
    #
    ## now perform the rename
    utils.rename_files_in_directory(
        epdicts_sub,
        showname,
        dirname = os.path.realpath( dirname ),
        seasno = seasno )
    logging.info( 'processed %02d episodes in %s in %0.3f seconds.' % (
        len( epdicts_sub[ seasno ] ), os.path.realpath( dirname ),
        time.perf_counter( ) - time0 ) )

def main( ):
    parser = ArgumentParser( )
    parser.add_argument(
        '-d', '--directory', dest = 'directory', type = str, action = 'store', default = os.getcwd( ),
        help = ' '.join([
            'Name of the directory where we wish to rename the MP4 or MKV files.',
            'Default is %s.' % os.getcwd( ) ] ) )
    parser.add_argument(
        '-s', '--series', dest='seriesName', type=str, action='store',
        help = 'Name of the TV show.', required = True )
    parser.add_argument(
        '-S', '--season', dest = 'seasno', type = int, action = 'store', required = True,
        help = 'The season number (not season 0 which is specials) of the series to use.' )
    parser.add_argument(
        '-F', '--firstAiredYear', dest = 'firstAiredYear', type=int, action='store',
        help = 'Year in which the first episode of the TV show aired.' )
    parser.add_argument(
        '-N', '--noinfo', dest='do_info', action='store_false', default = True,
        help = 'If chosen, then run with NO INFO logging (less debugging).' )
    #
    args = parser.parse_args( )
    #
    ## error checking
    directory = os.path.realpath( os.path.expanduser( args.directory ) )
    assert( os.path.isdir( directory ) )
    #
    assert( args.seasno > 0 )
    #
    ##
    logger = logging.getLogger( )
    if args.do_info: logger.setLevel( logging.INFO )
    #
    ## now do the operation
    rename_directory_episodes(
        args.seriesName,
        args.seasno,
        directory,
        firstAiredYear = args.firstAiredYear )
    
