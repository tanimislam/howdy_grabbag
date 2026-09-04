__author__ = 'Tanim Islam'
__email__ = 'tanim.islam@gmail.com'

import sys

def signal_handler( signal, frame ):
    """
    This is a convenience method that ``kills`` a Python execution when ``Ctrl+C`` is pressed. Its usage is fairly straightforward, shown in the code block below.

    .. code-block:: python

       import signal
       signal.signal( signal.SIGINT, howdy.signal_handler )

    This block of code at the top of the executable will capture ``Ctrl+C`` and then hard kill the executable by invoking ``sys.exit( 0 )``.

    :param dict signal: the POSIX_ signal to capture. See `the Python 3 signal high level overview <signal_high_level_overview_>`_ to begin to understand what POSIX_ signals are, and how Python can expose functionality to interact with them.
    :param frame: the stack frame. I don't know what it is, or why it's necessary in this context, when trying to capture a ``Ctrl+C`` and cleanly exit. It is of type :py:class:`frame`.
    
    .. _signal_high_level_overview: https://docs.python.org/3/library/signal.html
    .. _POSIX: https://en.wikipedia.org/wiki/POSIX
    """
    print( "You pressed Ctrl+C. Exiting...")
    sys.exit( 0 )


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
