#!/usr/bin/python3

class Atom:
    def __init__(self, word):
        self.word = word

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
            if a[0] in self.args and self.args[a[0]] == a[1]:
                return True
        return False

    def get(self, targets):
        result = []
        for t in targets:
            if t in self.args:
                result.append( (t, self.args[t]) )
            else:
                result.append( (t, None) )
        return None

class Concept
    def __init__(self, action):
        self.action = action
        self.facts = []

    def append(self, args):
        for f in self.facts:
            if f.match(args):
                return
        self.facts.append( Fact(args) )

    def resolve(self, args, results):
        for f in self.facts:
            if f.match(args):
                return f.get(results)

class Body():
    def __init__(self):
        self.atoms = AtomManager()
        self.concepts = {}

    def addfact(self, action, args):
        action = self.atoms.get(action)
        args = map( lambda x: tuple(map(lambda y:self.atoms.get(y), x.split(':'))), args)
        if action not in self.concepts:
            self.concepts[action] = Concept(action)
        self.concepts[action].append(args)

    def resolve_strings(self, action, args, results):
        action = self.atoms.get(action)
        args = map( lambda x: tuple(map(lambda y:self.atoms.get(y), x.split(':'))), args)
        results = map( lambda x: self.atoms.get(x), results)
        return self.resolve(action, args, results)

    def resolve(self, action, args, results)
        if action not in self.concepts:
            return None
        return self.concepts[aact].resolve(args, results)

if __name__ == '__main__':
    body = Body()
    body.addfact('plus', ['dobj:one', 'iobj:one', 'result:two'])
    body.addfact('plus', ['dobj:one', 'iobj:two', 'result:three'])
    body.addfact('plus', ['dobj:one', 'iobj:three', 'result:four'])
    body.addfact('plus', ['dobj:one', 'iobj:four', 'result:five'])
    print(body.resolve_strings('plus', ['dobj:one', 'iobj:two'], ['result']))
