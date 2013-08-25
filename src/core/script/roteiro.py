#-*-coding:utf-8-*-
import json


class Roteiro(list):
    def __init__(self, filename, iterable=None):
        if iterable != None:
            super(list, self).__init__(iterable)
        else:
            super(list, self).__init__()
        self.filename = filename
    
    def add(self, activity):
        self.append(activity)
        
    def removeAt(self, index):
        self.pop(index)
        
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
        
        
    def listItems(self):
        for i in self:
            print i
