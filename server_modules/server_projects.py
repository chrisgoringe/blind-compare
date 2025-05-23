from blind_ab_scorer import ImageChooser, AllDone, MissingImageException
import os, random
from typing import Self
from .utils import ProjectException

SortingNames = { 'bin':'z', 'flux':'x', 'done':'c', 'pony':'b', 'AAA':'a', 'sdxl':'v' }

ReversedSortingNames = { SortingNames[k]:k for k in SortingNames }

class NoImagesException(ProjectException): pass
class NoMoreImagesException(ProjectException): pass
class NoSuchProjectException(ProjectException): pass
    
class Project:
    def __init__(self, directory, name=None, **kwargs):
        try:
            self.ic:ImageChooser = ImageChooser(directory=directory, **kwargs)
            self.latest_images:list[str] = None
            self.directory = directory
            self.name = name or os.path.split(directory)[1]
        except MissingImageException:
            raise NoImagesException(f"No images")

    def image_details(self, index=0) -> tuple[str,str]:
        filename = os.path.split(self.latest_images[index])[1]
        fullpath = os.path.join(self.directory, filename)
        return filename, fullpath

    def next_image_set(self) -> list[str]:
        try:
            self.latest_images = self.next_image_set_impl()
        except AllDone as e:
            raise NoMoreImagesException(str(e))
        return [f"image/{f}" for f in self.latest_images]
    
    def next_image_set_impl(self) -> list[str]:
        return [os.path.split(f)[1] for f in self.ic.next_image_set(as_paths=True)]
    
    def project(self) -> dict:
        dic = self.introduction_impl()
        dic['n_per_set'] = self.ic.batch_size
        dic['n_sets'] = self.ic.batches
        dic['aspect_ratio'] = self.ic.guess_widest_aspect_ratio
        dic['name'] = self.name
        return dic

    def introduction_impl(self) -> dict: return {}

    def response(self, response:dict): 
        return self.response_impl(response) or {}
    
    def response_impl(self, response:dict): pass

    def status(self): 
        return {'html':f"Done {self.ic.pointer} of {self.ic.batches} in '{self.name}'"}
    
    current_project:Self = None
    args = None
    tag:str = None

    @classmethod
    def setup(cls, clazz, args={}, tag:str=""):
        cls.args = args
        cls.clazz = clazz
        cls.tag = tag

    @classmethod
    def clear(cls):
        cls.tag = None
        cls.current_project = None

    @classmethod
    def get_project(cls) -> Self:
        if cls.current_project is None:
            if cls.args is None: cls.setup()
            cls.current_project = cls.clazz(**cls.args)
        return cls.current_project

class SortProject(Project):
    def __init__(self, directory, buttons=['z','x','c','v','b','n'], **kwargs):
        kwargs['match'] = kwargs.get('match',None) or "."
        super().__init__(directory=directory, sort_mode=True, **kwargs)
        self.buttons = buttons

    def introduction_impl(self) -> dict: return { 'mode':'sort', 'buttons':self.buttons, 'labels':{k:ReversedSortingNames[k] for k in self.buttons} }

    def response_impl(self, response):
        if (p := response.get('rating', None)) in self.buttons:
            self.ic.move_file(p, verbose=True)
        elif p==' ':
            pass
        elif p=='__info__':
            return {'info':self.ic.get_text()}
        elif p=='__undo__':
            self.ic.undo_last()
            return {'info':"undid last selection"}
        else:
            raise ProjectException(f"{response} not understood as a response")
        
class PickProject(Project):
    def __init__(self, directory, match, **kwargs):
        super().__init__(directory=directory, match=match, **kwargs)
        self.scores = [0,]*self.ic.batch_size

    def introduction_impl(self) -> dict: return { 'mode':'pick' }

    def response_impl(self, response):
        try:
            p = response.get('pick','')
            if p==' ':
                pass
            elif p=='__info__':
                return {'info':self.ic.get_text()}
            else:
                pick = int(response.get('pick',''))
                self.ic.score(pick, and_print=True)
        except ValueError:
            raise ProjectException(f"{response}")
        except IndexError:
            raise ProjectException(f"{pick} out of range")
        
    
    def status(self): 
        st = super().status()
        st['html'] += "&nbsp;--&nbsp;" + self.ic.print_scores().replace("\n", "&nbsp;--&nbsp;")
        return st

        