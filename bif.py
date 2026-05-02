import logging

class BuiltinFunctions:
    def __init__(self, atoms):
        self.atoms = atoms
        self.keys = {}
        for k in ['action', 'dobj', 'iobj', 'result']:
            self.keys[k] = atoms.get(k)
        self.bifs = {}
        for k,v in { 'concat':self.concat }.items():
            self.bifs[atoms.get(k)] = v

    def resolve(self, args, targets, solver):
        if self.keys['action'] in args and args[self.keys['action']] in self.bifs:
            return self.bifs[args[self.keys['action']]](args, targets, solver)
        return []

    def concat(self, args, targets, solver):
        logging.debug(f'{solver.indent()}Concatenating {args} for {targets}')
        return [{ self.keys['result'] : self.atoms.get(args[self.keys['dobj']].word + args[self.keys['iobj']].word) }]