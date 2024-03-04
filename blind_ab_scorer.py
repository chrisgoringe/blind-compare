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
    parser.add_argument('--sub', help="Replacement string to go from first image to second", required=True)
    parser.add_argument('--height', type=int, default=768, help="Window height")

    return parser.parse_args()

def main():
    args = parse_arguments()
    ic = ImageChooser(args.directory, args.match, args.sub)
    app = TheApp(ic, args.height)
    app.app.mainloop()
    print(f"{args.match} chosen {ic.score_a} times, {args.sub} chosen {ic.score_b} times")

class ImageChooser:
    def __init__(self, directory, match, sub):
        self.directory = directory
        self.match = match
        self.sub = sub
        self.image_as = [file for file in os.listdir(self.directory) if match in file]
        random.shuffle(self.image_as)
        self.score_a, self.score_b = (0,0)
        self.pointer = -1

    def next_image_pair(self):
        self.pointer += 1
        image_a = self.image_as[self.pointer]
        ia = Image.open(os.path.join(self.directory, image_a))
        ib = Image.open(os.path.join(self.directory, image_a.replace(self.match, self.sub)))
        self.left_is_a = random.random()<0.5
        return (ia,ib) if self.left_is_a else (ib,ia)

    def score(self, left_picked):
        if left_picked:
            self.score_a += self.left_is_a
            self.score_b += not self.left_is_a
        else:
            self.score_a += not self.left_is_a
            self.score_b += self.left_is_a          

    def aspect_ratio(self):
        i = Image.open(os.path.join(self.directory, self.image_as[0]))
        return i.width / i.height 

class TheApp:
    def __init__(self, ic:ImageChooser, height:int):
        self.app = customtkinter.CTk()
        self.app.title("")
        self.ic = ic
        self.height=height

        maw = ic.aspect_ratio()
        self.app.geometry(f"{height*maw*2}x{height}")
        self.image_labels = [customtkinter.CTkLabel(self.app, text="") for _ in (0,1)]
        self.image_labels[0].grid(row=0, column=0)
        self.image_labels[1].grid(row=0, column=1)
        self.app.bind("<KeyRelease>", self.keyup)
        self.pick_images()
        
    def pick_images(self):
        image_pair = self.ic.next_image_pair()
        for i in (0,1):
            im = image_pair[i]
            self.image_labels[i].configure(image = customtkinter.CTkImage(light_image=im, size=(int(self.height*im.width/im.height),self.height)))

    def keyup(self,k):
        try:
            if k.char in "12": 
                self.ic.score(k.char=='1')
                self.pick_images()
        except IndexError:
            self.app.quit()

if __name__=="__main__":
    main()
    
