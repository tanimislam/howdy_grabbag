__author__ = 'Tanim Islam'
__email__ = 'tanim.islam@gmail.com'

import os
from howdy.core import core
from shutil import which

def _find_exec( exec_name = 'ffmpeg' ):
    which_exec = which( exec_name )
    if which_exec is None: return None
    #
    ## now check if we can execute on it
    if os.access( which_exec, os.X_OK ): return which_exec
    #
    ## otherwise look in /usr/bin
    which_exec = which( exec_name, path='/usr/bin')
    if which_exec is None: return None
    if os.access( which_exec, os.X_OK ): return which_exec
    return None

hcli_exec        = _find_exec( 'HandBrakeCLI' )
mkvpropedit_exec = _find_exec( 'mkvpropedit' )
mkvmerge_exec    = _find_exec( 'mkvmerge' )
nice_exec        = _find_exec( 'nice' )
ffmpeg_exec      = _find_exec( 'ffmpeg' )
ffprobe_exec     = _find_exec( 'ffprobe' )

assert( hcli_exec        is not None )
assert( mkvpropedit_exec is not None )
assert( mkvmerge_exec    is not None )
assert( nice_exec        is not None )
assert( ffmpeg_exec      is not None )
assert( ffprobe_exec     is not None )
