from geometry.path import CutPath
from geometry.typecuts import *

CUT_FUNCTIONS = {
    ("HP", "type6"): hp_type6,
    ("HP", "type9"): hp_type9,
    ("Angle", "type11"): angle_type11,
    ("Angle", "type83"): angle_type83,
    ("Rect", "type85"): rect_type85,
    ("Rect", "v_cut"): rect_v_cut,
}


class Profile:
    
    def __init__(self, profiel=None, width=None, thickness=None, length=None, height=None):
        self.profile_type = profiel
        self.width = width
        self.thickness = thickness
        self.length = length
        self.height = height
        self.cuts = []

        if self.profile_type == 'AngleEven':
            self.height = self.width
            self.profile_type = 'Angle'

        mogelijkheiden = ['Angle', 'AngleEven', 'HP', 'Rect']


    def __iter__(self):
        return iter(self.cuts)

    def __getitem__(self, cut_number):
          return self.cuts[cut_number]



    def add_cut(self,cuttype,position=0,side=None,Y=None,X=None,Angle=None,lengthwise=None,H=None,A=None):
        key = (self.profile_type, cuttype)

        if key not in CUT_FUNCTIONS:
            raise ValueError(f"Geen snijfunctie voor profiel {self.profile_type!r} en snijtype {cuttype!r}")

        cut_function = CUT_FUNCTIONS[key]


        parameters = {"width": self.width, "height": self.height, "thickness": self.thickness, 
                      "X": X, "Y": Y, "Angle": Angle, "H": H, "A": A,
                      "side": side, "lengthwise": lengthwise,}

        parameters = {
            key: value
            for key, value in parameters.items()
                if value is not None
        }


        path3d = cut_function(**parameters)

        cut = CutPath(path3d, self)
        cut.make_6d()
        cut.at_position = position
        
        self.cuts.append(cut)





    
