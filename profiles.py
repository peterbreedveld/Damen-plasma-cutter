
class Profile:

    def __init__(self, profiel, width, thickness, length, height=0):
        self.type = profiel
        self.width = width
        self.thickness = thickness
        self.length = length
        self.height = height

        if self.type == 'AE':
            self.height = self.width

        mogelijkheiden = ['AE', 'AU', 'HP', 'FL']

