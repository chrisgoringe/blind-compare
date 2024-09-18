import random, argparse, os, re
import customtkinter
from PIL import Image
from typing import Optional

class MissingImageException(Exception): pass
class AllDone(Exception): pass

class ImageChooser:
    def __init__(self, directory:str, match:Optional[str], rmatch:Optional[str], sub:list[str], verbose:int, **kwargs):
        self.directory = directory
        self.verbose = verbose

        matches = (lambda a : re.match(rmatch, a)) if rmatch else (lambda a: match in a)
        self.base_imagepaths = [os.path.join(self.directory, file) for file in os.listdir(self.directory) if matches(file)]
        random.shuffle(self.base_imagepaths)
        self.sub = [match,] + list(x.strip() for x in sub.split(","))
        if self.sub[0]==self.sub[1]: self.sub=self.sub[1:]

        if verbose>0: print(f"{len(self.base_imagepaths)} base images found")
        self.base_imagepaths = [ bip for bip in self.base_imagepaths if all(os.path.exists(bip.replace(self.sub[0], sub)) for sub in self.sub) ]

        self.batches = len(self.base_imagepaths)
        if verbose>0: 
            print(f"{self.batches} image sets")
            if verbose>1: print("\n".join(self.base_imagepaths))


        self.batch_size = len(self.sub)
        self.scores = None
        self.order = list(range(self.batch_size))

        self.pointer = -1

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
    def __init__(self, ic:ImageChooser, height:int, perrow:int, keypad:bool, scorelist:bool, verbose:int, **kwargs):
        self.app = customtkinter.CTk()
        self.app.title("")
        self.ic = ic
        self.height=height
        self.scorelist = scorelist
        if scorelist and not ic.batch_size>2:
            print(f"--scorelist ignored when only comparing between two images")
            self.scorelist = False
        self.done = 0
        self.verbose = verbose
        perrow = perrow if perrow>=1 else ic.batch_size
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

    def keyup(self,k):
        if k.char=='q': self.app.quit()
        try:
            if k.char==' ' and self.scorelist:
                self.ic.scorelist(self.scores)
            else:              
                choice = int(self.keymap[int(k.char)])
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
            self.app.title(f"{self.done}/{self.ic.batches}")
        except AllDone:
            self.app.quit()

class CommentArgumentParser(argparse.ArgumentParser):
    def convert_arg_line_to_args(self, arg_line):
        if arg_line.startswith('#'): return [] 
        line = "=".join(a.strip() for a in arg_line.split('='))
        return [line,] if len(line) else []

def parse_arguments():
    parser = CommentArgumentParser("Blind compare image pairs. Normal usage python blind_ab_score.py @arguments.txt", fromfile_prefix_chars='@')
    parser.add_argument('--directory', help="Directory images are in", required=True)
    parser.add_argument('--match', required=True, help="String to match to identify first image set")
    parser.add_argument('--rmatch', help="Optional regex to identify first image set. --match and --sub still used for replacements")
    parser.add_argument('--sub', help="Replacement string to go from first image to second. If comma separated list, all are shown", required=True)
    parser.add_argument('--height', type=int, default=768, help="Height to display each image")
    parser.add_argument('--perrow', type=int, default=3, help="Number of images per row")
    parser.add_argument('--keypad', action="store_true", help="Use the keypad layout to select images")
    parser.add_argument('--scorelist', action="store_true", help="Enter sequence of preferences ")
    parser.add_argument('--verbose', type=int, default=1, help="Verbosity 2 gives spoilers")

    return parser.parse_args()

def main():
    args = vars(parse_arguments())
    ic = ImageChooser(**args)
    app = TheApp(ic, **args)
    app.app.mainloop()
    if ic.scores is not None:
        for i, label in enumerate(ic.sub):
            print(f"{label} : {ic.scores[i]}")

if __name__=="__main__":
    main()
    
