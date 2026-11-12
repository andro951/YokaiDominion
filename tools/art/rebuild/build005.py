"""Resume anatomical art from versioned source; save the editable master before renders."""
from pathlib import Path
import sys, runpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
import body004
sys.modules['anatomy']=body004
runpy.run_path(str(Path(__file__).with_name('finish_art.py')),run_name='__main__')
