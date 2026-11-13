"""Actual-mesh face review. Fixed cameras and inherited fixed Art013 lights.
This script renders files, never generates substitute concept images.
"""
import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import review013
review013.SHOTS.update({
 'face-front':((0,-3,1.808),(0,-.09,1.808),.34,1.,False),
 'face-quarter':((1.6,-3,1.82),(0,-.09,1.808),.36,1.,False),
 'face-side':((3,0,1.81),(0,-.075,1.808),.36,1.,False),
 'face-quarter-other':((-1.6,-3,1.82),(0,-.09,1.808),.36,1.,False)
})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--shots',default='face-front,face-quarter,face-side');p.add_argument('--width',type=int,default=800);p.add_argument('--samples',type=int,default=32)
 a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);review013.render(a.source,a.out,a.shots,a.width,a.samples)
