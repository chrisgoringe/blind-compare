import argparse, os, shutil
from PIL import Image

class CommentArgumentParser(argparse.ArgumentParser):
    def convert_arg_line_to_args(self, arg_line):
        if arg_line.startswith('#'): return [] 
        line = "=".join(a.strip() for a in arg_line.split('='))
        return [line,] if len(line) else []
    
def parse_arguments():
    parser = CommentArgumentParser("Sort by aspect ratio", fromfile_prefix_chars='@')
    parser.add_argument('--dir', help="Directory images are in", required=True)
    parser.add_argument('--min', default=1.1, help="Minimum ratio - less is considered square")
    return  parser.parse_args()

def getlist(dir,mn):
    results = {'landscape':[], 'portrait':[], 'square':[]}
    for x in os.listdir(dir):
        try:
            im = Image.open(os.path.join(dir, x))
            ratio = im.width / im.height
            sub = 'square'
            if ratio > mn: sub = 'landscape'
            if ratio < (1/mn): sub = 'portrait'
            results[sub].append(x)
        except Exception as e:
            pass
    return results

def main():
    args = parse_arguments()
    for sub in ['landscape', 'portrait', 'square']:
        if not os.path.exists(os.path.join(args.dir, sub)):
            os.makedirs(os.path.join(args.dir, sub))
    results = getlist(args.dir, args.min)

    for k in results:
        for x in results[k]:
            os.rename( os.path.join(args.dir, x), os.path.join(args.dir, k, x) )

if __name__=='__main__':
    main( )