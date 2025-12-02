#!/usr/bin/python3

class Atom:
    def __init__(self, word):
        self.word = word

    def __repr__(self):
        return '#' + self.word

class AtomManager:
    def __init__(self):
        self.atoms = {}

    def get(self, word):
        if word not in self.atoms:
            self.atoms[word] = Atom(word)
        return self.atoms[word]

class Fact:
    def __init__(self, args):
        self.args = {}
        for a in args:
            self.args[a[0]] = a[1]

    def match(self, args):
        for a in args:
            if a[0] not in self.args or self.args[a[0]] != a[1]:
                return False
        return True

    def get(self, targets):
        result = []
        for t in targets:
            if t in self.args:
                result.append( (t, self.args[t]) )
            else:
                result.append( (t, None) )
        return result

class Concept:
    def __init__(self, action):
        self.action = action
        self.facts = []

    def append(self, args):
        for f in self.facts:
            if f.match(args):
                return
        self.facts.append( Fact(args) )

    def resolve(self, args, targets):
        result = []
        for f in self.facts:
            if f.match(args):
                result.append(f.get(targets))
        return result

class Body():
    def __init__(self):
        self.atoms = AtomManager()
        self.concepts = {}

    def addfact(self, action, args):
        action = self.atoms.get(action)
        args = list(map( lambda x: tuple(map(lambda y:self.atoms.get(y), x.split(':'))), args))
        if action not in self.concepts:
            self.concepts[action] = Concept(action)
        self.concepts[action].append(args)

    def resolve_strings(self, action, args, results):
        action = self.atoms.get(action)
        args = list(map( lambda x: tuple(map(lambda y:self.atoms.get(y), x.split(':'))), args))
        results = list(map( lambda x: self.atoms.get(x), results))
        return self.resolve(action, args, results)

    def resolve(self, action, args, results):
        if action not in self.concepts:
            return None
        return self.concepts[action].resolve(args, results)

if __name__ == '__main__':
    body = Body()
    body.addfact('plus', ['dobj:1', 'iobj:1', 'result:2'])
    body.addfact('plus', ['dobj:1', 'iobj:2', 'result:3'])
    body.addfact('plus', ['dobj:1', 'iobj:3', 'result:4'])
    body.addfact('plus', ['dobj:1', 'iobj:4', 'result:5'])
    print(body.resolve_strings('plus', ['dobj:1', 'iobj:2'], ['result']))
