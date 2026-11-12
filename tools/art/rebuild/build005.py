"""Anatomical art master. Saves editable geometry before reviewing images."""
from pathlib import Path
import sys,runpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
import body005
sys.modules['anatomy']=body005
import art005
art005.install()
import polish005
polish005.install()
import finish005
finish005.install()
import surface005
surface005.install()
import final006
final006.install()
import detail006
detail006.install()
if '--detail' not in sys.argv:sys.argv+=['--detail','2']
runpy.run_path(str(Path(__file__).with_name('finish_art.py')),run_name='__main__')
