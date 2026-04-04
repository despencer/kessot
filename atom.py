import logging
import kessot_pb2

class Atom:
    def __init__(self, word):
        self.word = word

    def isvariable(self):
        return self.word[0] == '$'

    def __repr__(self):
        return '#' + self.word

class AtomManager:
    def __init__(self):
        self.atoms = {}

    def get(self, word):
        if word not in self.atoms:
            self.atoms[word] = Atom(word)
            logging.info(f'Atom {word} registered')
        return self.atoms[word]

    def atomize(self, adict):
        result = {}
        for k,v in adict.items():
            result[self.get(k)] = self.get(v)
        return result

    def save(self, context, patoms):
        for i, a in enumerate(self.atoms.values()):
            pa = kessot_pb2.Atom()
            pa.id = i
            pa.word = a.word
            patoms.append(pa)
            context.atoms[a] = i

    def load(self, context, patoms):
        for pa in patoms:
            context.atoms[pa.id] = self.get(pa.word)
