import sys
import os

s_in = sys.argv[1]

os.chdir('solutions/' + s_in)
sys.exit(os.system('python ' + s_in + '.py'))

