import random, argparse, os
import customtkinter
from PIL import Image

class CommentArgumentParser(argparse.ArgumentParser):
    def convert_arg_line_to_args(self, arg_line):
        if arg_line.startswith('#'): return [] 
        line = "=".join(a.strip() for a in arg_line.split('='))
        return [line,] if len(line) else []

def parse_arguments():
    parser = CommentArgumentParser("Blind compare image pairs. Normal usage python blind_ab_score.py @arguments.txt", fromfile_prefix_chars='@')
    parser.add_argument('--directory', help="Directory images are in", required=True)
    parser.add_argument('--match', help="String to match to identify first image set", required=True)
    parser.add_argument('--sub', help="Replacement string to go from first image to second. If comma separated list, all are shown", required=True)
    parser.add_argument('--height', type=int, default=768, help="Height to display each image")
    parser.add_argument('--perrow', type=int, default=-1, help="Number of images per row")
    parser.add_argument('--keypad', action="store_true", help="Use the keypad layout to select images")
    parser.add_argument('--scorelist', action="store_true", help="Enter sequence of preferences ")
    parser.add_argument('--verbose', action="store_true", help="Print selections to the console")

    return parser.parse_args()

def main():
    args = parse_arguments()
    ic = ImageChooser(args.directory, args.match, args.sub, args.verbose)
    app = TheApp(ic, args.height, args.perrow, args.keypad, args.scorelist)
    app.app.mainloop()
    for i, label in enumerate(ic.sub):
        print(f"{label} : {ic.scores[i]}")

class ImageChooser:
    def __init__(self, directory:str, match:str, sub:str, verbose:bool):
        self.directory = directory
        self.verbose = verbose

        self.base_imagepaths = [os.path.join(self.directory, file) for file in os.listdir(self.directory) if match in file]
        random.shuffle(self.base_imagepaths)

        self.sub = [match,] + list(x.strip() for x in sub.split(","))
        self.number = len(self.sub)
        self.scores = None
        self.order = list(range(self.number))

        self.pointer = -1

    def next_image_set(self):
        self.pointer += 1
        self.base_imagepath = self.base_imagepaths[self.pointer]
        images = list( Image.open(self.base_imagepath.replace(self.sub[0], sub)) for sub in self.sub )
        random.shuffle(self.order)
        return tuple( images[self.order[i]] for i in range(self.number) )

    def score(self, picked):
        if not self.scores: self.scores = list(0 for _ in range(self.number))
        set_number = self.order[picked]
        self.scores[set_number] += 1      
        if self.verbose: 
            picked_filename = os.path.split(self.base_imagepath)[1].replace(self.sub[0], self.sub[set_number])
            print(f"You chose image #{picked+1} which was {picked_filename}")

    def scorelist(self, picked):
        if not self.scores: self.scores = list(list(0 for _ in range(self.number)) for _ in range(self.number))
        for i, pick in enumerate(picked):
            set_number = self.order[pick]
            self.scores[set_number][i] += 1
       
    @property
    def aspect_ratio(self):
        i = Image.open(os.path.join(self.directory, self.base_imagepaths[0]))
        return i.width / i.height 

class TheApp:
    def __init__(self, ic:ImageChooser, height:int, perrow:int, keypad_layout:bool, scorelist:bool):
        self.app = customtkinter.CTk()
        self.app.title("")
        self.ic = ic
        self.height=height
        self.scorelist = scorelist
        self.done = 0
        perrow = perrow if perrow>=1 else ic.number
        if keypad_layout:
            if (perrow>3 or ic.number//perrow>3):
                raise Exception(f"--keypad incompatible with {ic.number} sets displayed {perrow} per row")
            self.keymap = [" 2  1  0  ", " 45 23 01 ", " 678345012"][perrow-1]
        else:
            self.keymap = " 0123456789"

        self.app.geometry(f"{height*ic.aspect_ratio*ic.number}x{height}")
        self.image_labels = [customtkinter.CTkLabel(self.app, text="") for _ in range(ic.number)]
        
        for i, label in enumerate(self.image_labels): label.grid(row=(i//perrow), column=(i % perrow))

        self.app.bind("<KeyRelease>", self.keyup)
        self.pick_images()
        
    def pick_images(self):
        image_set = self.ic.next_image_set()
        for i, im in enumerate(image_set):
            self.image_labels[i].configure(image = customtkinter.CTkImage(light_image=im, size=(int(self.height*im.width/im.height),self.height)))
        if self.scorelist: self.scores = []
        self.done += 1

    def keyup(self,k):
        if k.char=='q': self.app.quit()
        try:
            digit = int(k.char)
            choice = int(self.keymap[digit])
            if choice<self.ic.number:
                if (self.scorelist):
                    self.scores.append(choice)
                    print(f"{self.scores}")
                    if (len(self.scores)) == self.ic.number:
                        self.ic.scorelist(self.scores)
                        self.pick_images()
                else:
                    self.ic.score(choice)
                    self.pick_images()
            self.app.title(f"{self.done}")
        except IndexError:
            self.app.quit()
        except:
            print(f"keypress {k.char} ignored")

if __name__=="__main__":
    main()
    
