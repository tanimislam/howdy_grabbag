__author__ = 'Tanim Islam'
__email__ = 'tanim.islam@gmail.com'

import os
from howdy.core import core
from shutil import which

def _find_ffmpeg_exec( ):
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

hcli_exec        = which( 'HandBrakeCLI' )
mkvpropedit_exec = which( 'mkvpropedit' )
mkvmerge_exec    = which( 'mkvmerge' )
nice_exec        = which( 'nice' )
ffmpeg_exec      = _find_ffmpeg_exec( )
ffprobe_exec     = which( 'ffprobe' )

assert( hcli_exec        is not None )
assert( mkvpropedit_exec is not None )
assert( mkvmerge_exec    is not None )
assert( nice_exec        is not None )
assert( ffmpeg_exec      is not None )
assert( ffprobe_exec     is not None )
