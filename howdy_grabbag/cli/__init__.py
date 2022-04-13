import os, sys, numpy

def remove_datetime_epdicts( epdicts ):
    return { seasno : { epno : epdicts[seasno][epno][0] for epno in epdicts[seasno] } for seasno in epdicts }

def rename_alleps( showname, epdicts, season, extension = "mkv", dirname = os.getcwd(), maxnum = 10_000 ):
    assert( maxnum > 0 )
    assert( season in epdicts )
    assert(
        set( filter(lambda epno: epno <= maxnum, filedict ) ) ==
        set( filter(lambda epno: epno <= maxnum, epdicts[ season ] ) ) )
    assert( season != 0 )
    filedict = { idx+1: filename for (idx, filename) in enumerate(sorted(glob.glob( os.path.join( dirname, "*.%s" % extension ))))}
    for epno in filedict:
        newfile = "%s - s%02de%02d - %s.%s" % (
            showname, season, epno, epdicts[season][epno], extension )
        os.rename( filedict[ epno ], newfile )
