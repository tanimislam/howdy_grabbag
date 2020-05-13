__author__ = 'Tanim Islam'
__email__ = 'tanim.islam@gmail.com'

import os, sys
from plexstuff.plexcore import plexcore

# code to handle Ctrl+C, convenience method for command line tools
def signal_handler( signal, frame ):
    print( "You pressed Ctrl+C. Exiting...")
    sys.exit( 0 )
