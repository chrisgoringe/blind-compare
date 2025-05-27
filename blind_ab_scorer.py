import random, argparse, os, re, shutil, time
import customtkinter
import pyautogui
from PIL import Image
from typing import Optional
from functools import cached_property

class MissingImageException(Exception): pass
class AllDone(Exception): pass
class ParameterException(Exception): pass

IMAGE_EXT = [".jpg", ".jpeg", ".png"]

DEFAULT_PER_ROW = [0,1,2,3,2,3,3,4,3,3,4,4,4]
DEFAULT_PER_ROW_KP = [0,1,2,3,2,3,3,3,3,3]

def is_image(filepath):
    return(os.path.isfile(filepath) and 
           os.path.splitext(filepath)[1].lower() in IMAGE_EXT and 
           not os.path.split(filepath)[1].startswith('.'))

def aspect_ratio(path):
    with Image.open(path) as i: return i.width/i.height

def _move_file(basedir, subdir, filepath, verbose=False) -> list[tuple[str,str]]:
    subdir = os.path.join(basedir, subdir)
    if not os.path.exists(subdir): os.makedirs(subdir)
    base, ext = os.path.splitext(os.path.basename(filepath))
    newpath = os.path.join(subdir, base + ext)
    while os.path.exists(newpath):
        base = f"{base}_{random.randint(100000,999999)}"
        newpath = os.path.join(subdir, base + ext)
    shutil.move(filepath, newpath)
    moves = [(filepath, newpath), ]
    
    def drag_along(extension):
        epath = os.path.splitext(filepath)[0]+extension
        if os.path.exists(epath):
            newepath = os.path.splitext(newpath)[0]+extension
            shutil.move(epath, newepath)
            moves.append((epath, newepath))

    drag_along(".txt")
    drag_along(".idx.txt")

    if verbose: print("\n".join(f"Moved {a} to {b}" for (a,b) in moves))
    return moves


class ImageChooser:
    def __init__(self, directory:list[str], match:Optional[str], rmatch:Optional[str]=None, sub:list[str]=None, 
                 verbose:int=0, sort_mode:bool=False, recurse:bool=False, noshuffle:bool=False, allow_missing:bool=True, directory_exclude:str="zxc", **kwargs):
        self.directories = directory if isinstance(directory,list) else [directory,]
        self.verbose = verbose
        self.undo_stack:list[list[tuple[str,str]]]= []

        if sort_mode and match is None: 
            matches = lambda a : True
        elif rmatch:  
            matches = lambda a : re.match(rmatch, a)
        else:         
            matches = lambda a : match in a

        candidate_imagepaths = []
        def scan_directory(d, is_base=False): 
            if os.path.split(d)[1] in directory_exclude and not is_base:
                print(f"excluding {d}")
                return
            try:
                for f in os.listdir(d):
                    if matches(f) and is_image(os.path.join(d,f)):      candidate_imagepaths.append( os.path.join(d,f) )
                    if recurse    and os.path.isdir(os.path.join(d,f)): scan_directory(os.path.join(d,f))
            except Exception as e:
                print(f"Problem reading directory {d} - {e}")

        for directory in self.directories:
            scan_directory(directory, True)

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
            if not allow_missing:
                self.base_imagepaths = [ bip for bip in candidate_imagepaths if all(os.path.exists(bip.replace(self.sub[0], sub)) for sub in self.sub) ]
            else:
                self.base_imagepaths = candidate_imagepaths

        self.batches = len(self.base_imagepaths)
        if verbose>0: 
            print(f"{self.batches} image sets")
            if verbose>1: print("\n".join(self.base_imagepaths))
            if self.batches != len(candidate_imagepaths):
                print(f"Failed to find alternatives for {[x for x in candidate_imagepaths if x not in self.base_imagepaths]}")

        if not self.batches:
            def any_matches(the_sub): return any(os.path.exists(the_base.replace(self.sub[0], the_sub)) for the_base in candidate_imagepaths)
            raise MissingImageException("No image sets - no matches for: "+",".join( sub for sub in self.sub if not any_matches(sub)))

        self.batch_size = len(self.sub)
        self.scores = None
        self.order = list(range(self.batch_size))

        self.pointer = -1

    def get_text(self):
        if len(self.last_sent_images)!=1: return "Can't get info for multiple images"
        if os.path.exists(filepath:=os.path.splitext(self.last_sent_images[0])[0]+".txt"):
            with (open(filepath, "r")) as f:
                return f.read()
        else:
            return "No .txt file"
        
    def undo_last(self, verbose=True):
        '''
        Return the number that 'done' should change by.
        '''
        to_undo = self.undo_stack[-1] if len(self.undo_stack) else None
        self.undo_stack = self.undo_stack[:-1]
        if to_undo:
            for (mv_from, mv_to) in to_undo:
                shutil.move(mv_to, mv_from)
                if verbose: print(f"moved {mv_to} back to {mv_from}")
            self.pointer -= 2
            return -1
        self.pointer -= 1
        return 0


    def skip_this_dir(self):
        '''
        Skip over (do not resolve) all images in the current directory. Return the number that 'done' should change by.
        '''
        this_dir = os.path.dirname(self.base_imagepath)
        skipped = 0
        while self.pointer < self.batches-1 and os.path.dirname(self.base_imagepaths[self.pointer]) == this_dir: 
            self.pointer += 1
            skipped += 1
        return skipped
        
    def move_file(self, subdir, verbose=False):
        assert(len(self.last_sent_images)==1)
        assert(len(self.directories)==1)
        self.undo_stack = _move_file(self.directories[0], subdir, self.last_sent_images[0], verbose)
        

    def guess_subs(self, one_match:str, match_term:str):
        before, after = one_match.split(match_term)
        subs = [match_term,]
        for directory in self.directories:
            for f in os.listdir(directory):
                p = os.path.join(directory, f)
                if p.startswith(before) and p.endswith(after):
                    mt = p[len(before):-len(after)]
                    if (mt!=match_term): subs += [mt,]
        print(f"Guessing {subs}")
        return subs

    def substituted(self, sub:str, as_path=False) -> Image.Image:
        path = self.base_imagepath.replace(self.sub[0], sub)
        if as_path: return path
        return Image.open(path) if os.path.exists(path) else Image.new('RGB', (32,32))

    def next_image_set(self, as_paths=False) -> tuple[Image.Image]:
        self.pointer += 1
        try:
            self.base_imagepath = self.base_imagepaths[self.pointer]
            if self.verbose: print(f"Loading base image {self.base_imagepath}")
            self.last_sent_images = list( self.substituted(sub, as_path=as_paths) for sub in self.sub )
            #if self.verbose: print(f"Loading subs {[self.base_imagepath.replace(self.sub[0], sub) for sub in self.sub]}")
        #except FileNotFoundError as e:
        #    raise MissingImageException(*e.args)
        except IndexError:
            raise AllDone()
        random.shuffle(self.order)
        return tuple( self.last_sent_images[self.order[i]] for i in range(self.batch_size) )

    def score(self, picked, and_print=False):
        if not self.scores: self.scores = list(0 for _ in range(self.batch_size))
        set_number = self.order[picked]
        self.scores[set_number] += 1      
        if self.verbose>1: 
            picked_filename = os.path.split(self.base_imagepath)[1].replace(self.sub[0], self.sub[set_number])
            print(f"You chose image #{picked+1} which was {picked_filename}")
        if and_print: self.print_scores()

    def scorelist(self, picked):
        if not self.scores: self.scores = list(list(0 for _ in range(self.batch_size)) for _ in range(self.batch_size))
        for i, pick in enumerate(picked):
            set_number = self.order[pick]
            self.scores[set_number][i] += 1

    def print_scores(self):
        if not self.scores: return ""
        s = "\n".join(f"{label} : {self.scores[i]}" for i, label in enumerate(self.sub))
        print(s)
        return s
       
    #@property
    #def aspect_ratio(self):
    #    try:
    #        with Image.open(self.base_imagepaths[max(self.pointer,0)]) as i:
    #            return i.width / i.height 
    #    except:
    #        return 1.0
        
    @cached_property
    def guess_widest_aspect_ratio(self):
        return max( aspect_ratio(p) for p in random.choices(self.base_imagepaths, k=20) )

class TheApp:
    def __init__(self, ic:ImageChooser, height:int, perrow:int, keypad:bool, scorelist:bool, verbose:int, sort_mode:bool, directory:list[str], **kwargs):
        self.app = customtkinter.CTk()
        self.header = 'ZM sort' if sort_mode else 'AB Compare'
        self.sort_mode = sort_mode
        self.first_directory = directory[0]

        self.ic = ic
        self.height=height
        self.scorelist = scorelist
        self.done = 0
        self.verbose = verbose

        self.move_first = kwargs.get('move_first', None)
        self.move_chosen = kwargs.get('move_chosen', None)
        self.move_unchosen = kwargs.get('move_unchosen', None)

        rows = ((ic.batch_size-1)//perrow) + 1
        self.height=int(height//rows)
        
        if keypad:
            if (perrow>3 or ic.batch_size//perrow>3):
                raise Exception(f"--keypad incompatible with {ic.batch_size} sets displayed {perrow} per row")
            self.keymap = [" 2  1  0  ", " 45 23 01 ", " 678345012"][perrow-1]
        else:
            self.keymap = " 0123456789"

        self.app.geometry(f"{int(self.height*ic.guess_widest_aspect_ratio*perrow)}x{self.height*rows}")
        self.image_labels = [customtkinter.CTkLabel(self.app, text="") for _ in range(ic.batch_size)]
        
        for i, label in enumerate(self.image_labels): label.grid(row=(i//perrow), column=(i % perrow))

        if (self.move_chosen or self.move_unchosen or self.move_first) and (self.sort_mode):
            print("move_first/move_chosen/move_unchosen not compatible with sort_mode. Ignoring them.")
            self.move_first, self.move_chosen, self.move_unchosen = None, None, None

        self.app.bind("<KeyRelease>", self.keyup)
        self.pick_images()

    def set_title(self): self.app.title(f"{self.header} {self.done}/{self.ic.batches}")  
        
    def pick_images(self):
        try:
            self.image_set = self.ic.next_image_set()
            for i, im in enumerate(self.image_set):
                self.image_labels[i].configure(image = customtkinter.CTkImage(light_image=im, size=(int(self.height*im.width/im.height),self.height)))
            if self.scorelist: self.scores = []
        except MissingImageException as e:
            if self.verbose: print(f"Missing image: {e.args[0]}")
            self.pick_images()
        self.set_title()
        self.last_picked_at = time.monotonic()

    def move_basefile(self, subdir):
        self.ic.undo_stack.append(_move_file(self.first_directory, subdir, self.ic.base_imagepath, self.verbose))
        return 1

    def move_file(self, subdir, choice):
        self.ic.undo_stack.append(_move_file(self.first_directory, subdir, self.image_set[choice].filename, self.verbose))

    def keyup(self,k):
        if (time.monotonic() - self.last_picked_at)<0.1: return
        char = k.char or k.keysym
        if char=='q': self.app.quit()
        try:
            if self.sort_mode:
                if char in 'zxcvbnm123456789':  self.done += self.move_basefile(char)
                elif char==' ':                 self.done += 1
                elif char=='u':                 self.done += self.ic.undo_last()
                elif char=='i':                 self.done += self.ic.skip_this_dir()
                else: return
            else:
                if char==' ':
                    if self.scorelist: 
                        if self.move_first or self.move_chosen or self.move_unchosen:
                            for c in range(len(self.image_set)):
                                if self.move_first and self.scores and c==self.scores[0]: self.move_file(self.move_first, c)
                                elif self.move_chosen and c in self.scores:               self.move_file(self.move_chosen, c)
                                elif self.move_unchosen and c not in self.scores:         self.move_file(self.move_unchosen, c)
                        self.ic.scorelist(self.scores)
                else:              
                    choice = int(self.keymap[int(char)])
                    if choice<self.ic.batch_size:
                        if (self.scorelist):
                            if not choice in self.scores:
                                self.scores.append(choice)
                                if self.verbose: print(f"{self.scores}")
                                if (len(self.scores)) != self.ic.batch_size: return
                                if self.move_chosen: 
                                    for c in self.scores: self.move_file(self.move_chosen, c)
                                self.ic.scorelist(self.scores)
                            else: print("Repeat pick")
                        else:
                            self.ic.score(choice)
                            if self.move_chosen: self.move_file(self.move_chosen, choice)
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
    parser.add_argument('--directory', action="append", help="Directory images are in. Can be specified multiple times.", required=True)
    parser.add_argument('--recurse', action="store_true", help="include subdirectories")
    parser.add_argument('--directory_exclude', default="zxc", help="when recursing, ignore any directory path ending with a single letter directory in this list")
    parser.add_argument('--rmatch', help="Optional regex to identify first image set. --match and --sub still used for replacements")
    parser.add_argument('--match', help="String to match to identify first image set")
    parser.add_argument('--sub', help="Replacement string to go from first image to second. If comma separated list, all are shown")
    parser.add_argument('--height', type=int, help="Height of app")
    parser.add_argument('--width', type=int, help="Width of app")
    parser.add_argument('--perrow', type=int, help="Number of images per row")
    parser.add_argument('--keypad', action="store_true", help="Use the keypad layout to select images")
    parser.add_argument('--scorelist', action="store_true", help="Enter sequence of preferences ")
    parser.add_argument('--verbose', type=int, default=1, help="Verbosity 2 gives spoilers")
    parser.add_argument('--sort_mode', action="store_true", help="Ignore match and subs, show one image at a time, sort with 'z' and m'")
    parser.add_argument('--move_first', type=str, help="Move first pick from each set to this subdirectory")
    parser.add_argument('--move_chosen', type=str, help="Move picks from each set to this subdirectory (if move_first also specified, this applies to subsequent picks only)")
    parser.add_argument('--move_unchosen', type=str, help="Move unpicked from each set to this subdirectory")
    parser.add_argument('--extensions', default=[], action="append", help="Extra extensions to count as images (.jpg, .jpeg and .png default)")
    parser.add_argument('--noshuffle', action='store_true', help="don't randomise the order of sets")
    parser.add_argument('--allow_missing', action='store_true', help="include sets with missing images")

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
    args['perrow'] = args.get('perrow') or (DEFAULT_PER_ROW_KP[ic.batch_size] if args.get('keypad') else DEFAULT_PER_ROW[ic.batch_size])
    rows = ((ic.batch_size-1) // args['perrow']) + 1

    s = pyautogui.size()
    cols = ((ic.batch_size-1) // rows) + 1
    w = args['width'] or int(s.width - 120)
    h = args['height'] or int(s.height - 120)
    args['height'] = min(h, rows*int(w/ic.guess_widest_aspect_ratio) // cols)

    app = TheApp(ic, **args)
    app.app.mainloop()
    if ic.scores is not None:
        print(f"{len(ic.base_imagepaths)} sets total")
        ic.print_scores()


if __name__=="__main__":
    try: main()
    except ArgumentException as e:
        print(e.args[0])
    except MissingImageException as e:
        print(e.args[0])
    
