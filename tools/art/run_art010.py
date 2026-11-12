"""Run the saved Art010 editor with the selected versioned body sculpt."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bust_drape010
import bust_shape010
bust_drape010.REVISION=bust_shape010.REVISION
if __name__=='__main__':
    bust_drape010.main()
