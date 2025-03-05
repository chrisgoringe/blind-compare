import os, random, re, argparse, shutil

def clean(dir:str) -> str:
    drive, path = dir.split(":\\")
    if not path:
        path = drive
        drive = None
    rejoined = os.path.join(*path.split("\\"))
    return drive + ":\\" + rejoined if drive else rejoined

def regex_dir(dir:str, regex:re.Pattern, invert_regex:bool) -> bool: 
    matches = any(regex.match(d) for d in dir.split(os.sep))
    if invert_regex: matches = not matches
    return matches

def get_images(dir:str, ext:str=".png", recurse:bool=False, regex_str:str="", invert_regex=False):
    regex = re.compile(regex_str)
    if recurse:
        all_files = [ os.path.join(root, file) for root, _, files in os.walk(dir) for file in files]
    else:
        all_files = [os.path.join(dir,f) for f in os.listdir(dir)]
    return [f for f in all_files if os.path.splitext(f)[1].lower()==ext.lower() and regex_dir(dir=f, regex=regex, invert_regex=invert_regex)]

def fix(source:str, prefix:str, target:str, extension=".png", recurse=False, start_idx=0, regex_str="", invert_regex=False):
    idx = start_idx
    prefix = prefix or f"{random.randint(100000,999999)}"

    source = clean(source)
    target = clean(target or source)
    if not os.path.exists(target): os.makedirs(target, exist_ok=True)

    original_paths = get_images(source, extension, recurse, regex_str, invert_regex)
    newpath = lambda i:os.path.join(target, f"{prefix}_{i:0>5}{extension}")

    for path in original_paths:
        while os.path.exists(newpath(idx)): idx += 1
        thenewpath = newpath(idx)

        print(f"{path} -> {thenewpath}")
        shutil.move(path, newpath(idx))

        txtpath = os.path.splitext(path)[0] + ".txt"
        if os.path.exists(txtpath): 
            newtxtpath = os.path.split(thenewpath)[0] + ".txt"
            print(f"{txtpath} -> {newtxtpath}")
            shutil.move(txtpath, newtxtpath)

def distribute(source:str, recurse:bool, target:str, **kwargs):
    fix(source, recurse=recurse, target=os.path.join(target,'bin'),        regex_str="^z$", **kwargs)
    fix(source, recurse=recurse, target=os.path.join(target,'done'),       regex_str="^c$", **kwargs)
    fix(source, recurse=recurse, target=os.path.join(target,'candidates'), regex_str="^x$", **kwargs)

def remove_empties(source:str, **kwargs):
    pass
    
def main():
    a = argparse.ArgumentParser()

    a.add_argument('--justfix', action="store_true", help="Just standardise names in directory")

    a.add_argument('--source', default=None, help="source directory")
    a.add_argument('--target', default=None, help="target for distribute")
    a.add_argument('--prefix', default=None, help="prefix for sorted files. Default is a random 6 digit string")
    a.add_argument('--norecurse', action='store_true', help="don't search source recursively")
    a.add_argument('--extension', default=".png", help="extension to search for. Case insensitive")
    a.add_argument('--keepempty', action='store_true', help="don't remove empty directories afterwards")

    args = vars(a.parse_args())
    args['recurse'] = not args.pop('norecurse')
    
    justfix = args.pop('justfix')
    remove_empty = not args.pop('keepempty')

    if justfix: fix(**args)
    else:       
        distribute(**args)
        if remove_empty: remove_empties(**args)


if __name__=='__main__': main()