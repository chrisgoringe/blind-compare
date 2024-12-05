import random, argparse, os, re, shutil
import customtkinter
from PIL import Image
from typing import Optional

class MissingImageException(Exception): pass
class AllDone(Exception): pass

IMAGE_EXT = [".jpg", ".jpeg", ".png"]

DEFAULT_PER_ROW = [0,1,2,3,2,3,3,4,3,3,4,4,4]

def is_image(filepath):
    return(os.path.isfile(filepath) and os.path.splitext(filepath)[1].lower() in IMAGE_EXT)

class ImageChooser:
    def __init__(self, directory:str, match:Optional[str], rmatch:Optional[str], sub:list[str], verbose:int, sort_mode:bool, recurse:bool, noshuffle:bool, **kwargs):
        self.directory = directory
        self.verbose = verbose

        if sort_mode: matches = lambda a : True
        elif rmatch:  matches = lambda a : re.match(rmatch, a)
        else:         matches = lambda a : match in a

        candidate_imagepaths = []
        def scan_directory(d):
            for f in os.listdir(d):
                if matches(f) and is_image(os.path.join(d,f)):      candidate_imagepaths.append( os.path.join(d,f) )
                if recurse    and os.path.isdir(os.path.join(d,f)): scan_directory(os.path.join(d,f))
        scan_directory(self.directory)

        if not candidate_imagepaths:
            raise MissingImageException("No matching images found")
        
        if (not noshuffle):
            random.shuffle(candidate_imagepaths)
        if verbose>0: print(f"{len(candidate_imagepaths)} base images found")

        if sort_mode: 
            self.sub = [".",]
            self.base_imagepaths = candidate_imagepaths
        else:
            if not sub: self.sub = self.guess_subs(candidate_imagepaths[0], match)
            else: self.sub = [match,] + list(x.strip() for x in sub.split(","))
            if self.sub[0]==self.sub[1]: self.sub=self.sub[1:]
            self.base_imagepaths = [ bip for bip in candidate_imagepaths if all(os.path.exists(bip.replace(self.sub[0], sub)) for sub in self.sub) ]
            
        self.batches = len(self.base_imagepaths)
        if verbose>0: 
            print(f"{self.batches} image sets")
            if verbose>1: print("\n".join(self.base_imagepaths))

        if not self.batches:
            def any_matches(the_sub): return any(os.path.exists(the_base.replace(self.sub[0], the_sub)) for the_base in candidate_imagepaths)
            raise MissingImageException("No image sets - no matches for: "+",".join( sub for sub in self.sub if not any_matches(sub)))

        self.batch_size = len(self.sub)
        self.scores = None
        self.order = list(range(self.batch_size))

        self.pointer = -1

    def guess_subs(self, one_match:str, match_term:str):
        before, after = one_match.split(match_term)
        subs = []
        for f in os.listdir(self.directory):
            p = os.path.join(self.directory, f)
            if p.startswith(before) and p.endswith(after):
                subs += [p[len(before):-len(after)],]
        print(f"Guessing {subs}")
        return subs


    def next_image_set(self):
        self.pointer += 1
        try:
            self.base_imagepath = self.base_imagepaths[self.pointer]
            images = list( Image.open(self.base_imagepath.replace(self.sub[0], sub)) for sub in self.sub )
        except FileNotFoundError as e:
            raise MissingImageException(*e.args)
        except IndexError:
            raise AllDone()
        random.shuffle(self.order)
        return tuple( images[self.order[i]] for i in range(self.batch_size) )

    def score(self, picked):
        if not self.scores: self.scores = list(0 for _ in range(self.batch_size))
        set_number = self.order[picked]
        self.scores[set_number] += 1      
        if self.verbose>1: 
            picked_filename = os.path.split(self.base_imagepath)[1].replace(self.sub[0], self.sub[set_number])
            print(f"You chose image #{picked+1} which was {picked_filename}")

    def scorelist(self, picked):
        if not self.scores: self.scores = list(list(0 for _ in range(self.batch_size)) for _ in range(self.batch_size))
        for i, pick in enumerate(picked):
            set_number = self.order[pick]
            self.scores[set_number][i] += 1
       
    @property
    def aspect_ratio(self):
        i = Image.open(os.path.join(self.directory, self.base_imagepaths[0]))
        return i.width / i.height 

class TheApp:
    def __init__(self, ic:ImageChooser, height:int, perrow:int, keypad:bool, scorelist:bool, verbose:int, sort_mode:bool, directory:str, **kwargs):
        self.app = customtkinter.CTk()
        self.header = 'ZM sort' if sort_mode else 'AB Compare'
        self.sort_mode = sort_mode
        self.directory = directory

        self.ic = ic
        self.height=height
        self.scorelist = scorelist
        self.done = 0
        self.verbose = verbose
        if keypad:
            if (perrow>3 or ic.batch_size//perrow>3):
                raise Exception(f"--keypad incompatible with {ic.batch_size} sets displayed {perrow} per row")
            self.keymap = [" 2  1  0  ", " 45 23 01 ", " 678345012"][perrow-1]
        else:
            self.keymap = " 0123456789"

        self.app.geometry(f"{height*ic.aspect_ratio*ic.batch_size}x{height}")
        self.image_labels = [customtkinter.CTkLabel(self.app, text="") for _ in range(ic.batch_size)]
        
        for i, label in enumerate(self.image_labels): label.grid(row=(i//perrow), column=(i % perrow))

        self.app.bind("<KeyRelease>", self.keyup)
        self.pick_images()

    def set_title(self): self.app.title(f"{self.header} {self.done}/{self.ic.batches}")  
        
    def pick_images(self):
        try:
            image_set = self.ic.next_image_set()
            for i, im in enumerate(image_set):
                self.image_labels[i].configure(image = customtkinter.CTkImage(light_image=im, size=(int(self.height*im.width/im.height),self.height)))
            if self.scorelist: self.scores = []
            self.done += 1
        except MissingImageException as e:
            if self.verbose: print(f"Missing image: {e.args[0]}")
            self.pick_images()
        self.set_title()

    def keyup(self,k):
        char = k.char or k.keysym
        if char=='q': self.app.quit()
        try:
            if self.sort_mode:
                if char in 'zxcvbnm123456789':
                    subdir = os.path.join(self.directory, char)
                    if not os.path.exists(subdir): os.makedirs(subdir)
                    newpath = os.path.join(subdir, os.path.basename(self.ic.base_imagepath))
                    shutil.move(self.ic.base_imagepath, newpath)
                elif k.char==' ': 
                    pass
                else:
                    return
            else:
                if char==' ' and self.scorelist:
                    self.ic.scorelist(self.scores)
                else:              
                    choice = int(self.keymap[int(char)])
                    if choice<self.ic.batch_size:
                        if (self.scorelist):
                            self.scores.append(choice)
                            if self.verbose: print(f"{self.scores}")
                            if (len(self.scores)) != self.ic.batch_size: return
                            self.ic.scorelist(self.scores)
                        else:
                            self.ic.score(choice)
                    else: return
            self.pick_images()
        except AllDone:
            self.app.quit()

class CommentArgumentParser(argparse.ArgumentParser):
    def convert_arg_line_to_args(self, arg_line):
        arg_line = arg_line.split('#')[0]
        if not arg_line: return []
        line = "=".join(a.strip() for a in arg_line.split('='))
        return [line,] if len(line) else []

class ArgumentException(Exception): pass

def parse_arguments(override):
    parser = CommentArgumentParser("Blind compare image pairs. Normal usage python blind_ab_score.py @arguments.txt", fromfile_prefix_chars='@')
    parser.add_argument('--directory', help="Directory images are in", required=True)
    parser.add_argument('--recurse', action="store_true", help="include subdirectories")
    parser.add_argument('--rmatch', help="Optional regex to identify first image set. --match and --sub still used for replacements")
    parser.add_argument('--match', help="String to match to identify first image set")
    parser.add_argument('--sub', help="Replacement string to go from first image to second. If comma separated list, all are shown")
    parser.add_argument('--height', type=int, default=768, help="Height of app")
    parser.add_argument('--perrow', type=int, help="Number of images per row")
    parser.add_argument('--keypad', action="store_true", help="Use the keypad layout to select images")
    parser.add_argument('--scorelist', action="store_true", help="Enter sequence of preferences ")
    parser.add_argument('--verbose', type=int, default=1, help="Verbosity 2 gives spoilers")
    parser.add_argument('--sort_mode', action="store_true", help="Ignore match and subs, show one image at a time, sort with 'z' and m'")
    parser.add_argument('--extensions', default=[], action="append", help="Extra extensions to count as images (.jpg, .jpeg and .png default)")
    parser.add_argument('--noshuffle', action='store_true', help="don't randomise the order of sets")

    args = parser.parse_args() if not override else parser.parse_args(override)
    if not args.sort_mode and not args.match:
        raise ArgumentException("Either --sort_mode (for sorting) or --match (for comparing) are required")

    for e in args.extensions:
        global IMAGE_EXT
        IMAGE_EXT += e.lower() if e[0]=='.' else f".{e}".lower()

    return vars(args)

def main():
    try:
        args = parse_arguments()
    except:
        args = parse_arguments(["@arguments.txt",])
    ic = ImageChooser(**args)
    args['perrow'] = args.get('perrow') or DEFAULT_PER_ROW[ic.batch_size]
    rows = ((ic.batch_size-1) // args['perrow']) + 1
    args['height'] = args['height'] // rows
    app = TheApp(ic, **args)
    app.app.mainloop()
    if ic.scores is not None:
        print(f"{len(ic.base_imagepaths)} sets total")
        for i, label in enumerate(ic.sub):
            print(f"{label} : {ic.scores[i]}")

if __name__=="__main__":
    try: main()
    except ArgumentException as e:
        print(e.args[0])
    
