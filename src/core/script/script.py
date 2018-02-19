import json


class Script(list):
    def __init__(self, filename=None, iterable=None):
        if iterable != None:
            super().__init__(iterable)
        else:
            super().__init__()
        self.filename = filename

    def save(self):
        save = open(self.filename, 'w')
        json.dump(self, save)
        save.close()

    def saveAs(self, filename):
        save = open(filename, 'w')
        json.dump(self,save)
        save.close()
        self.filename = filename

    def load(self, filename):
        self.__delslice__(0,len(self))
        self.extend(json.load(open(filename)))

    def update(self, filename, index):
        d = json.load(open(filename))
        up = self[index]
        for key in up.keys():
            d[key] = up[key]
        json.dump(d,open(filename, 'w'))
