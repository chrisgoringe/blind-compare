import os

dir = r'C:\Users\chris\Documents\GitHub\ComfyUI\output\more'

with open('out.csv', 'w') as outfile:
    for s in [1,2,3,4]:
        for f in os.listdir(os.path.join(dir, str(s))):
            otk = float(f[6:10])
            rb = float(f[15:19])
            print(f"{otk},{rb},{s}", file=outfile)