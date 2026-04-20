import logging
import kessot_pb2

class Tuple:
    def __init__(self):
        self.args = {}

    def __iter__(self):
        return iter(self.args.items())

    def __getitem__(self, key):
        return self.args[key]

    def __contains__(self, key):
        return key in self.args

    def match(self, args, strict=False):
        for k,v in args.items():
            if k not in self.args:
                return False
            if (not self.args[k].isvariable()) and self.args[k] != v:
                return False
        if strict:
            return len(self.args) == len(args)
        return True

    def matchvars(self, args):
        lvars = {}
        for k,v in self.args.items():
            if v.isvariable():
                lvars[v] = args[k]
        return lvars

    def get(self, targets):
        result = {}
        for t in targets:
            if t in self.args:
                result[t] = self.args[t]
            else:
                result[t] = None
        return result

    def substitute(self, lvars):
        result = {}
        for k,v in self.args.items():
            if v.isvariable():
                result[k] = lvars[v]
            else:
                result[k] = v
        return result

    def getvars(self):
        lvars = []
        for v in self.args.values():
            if v.isvariable():
                lvars.append(v)
        return lvars

    def __repr__(self):
        return f'<Tuple {self.args}>'

    @classmethod
    def make(cls, args):
        tup = cls()
        for k,v in args.items():
            tup.args[k] = v
        return tup

    def save(self, context):
        return self.saveto(context, kessot_pb2.Tuple())

    def saveto(self, context, pfact):
        for ak, av in self.args.items():
            parg = kessot_pb2.Argument()
            parg.role = context.atoms[ak]
            parg.value = context.atoms[av]
            pfact.args.append(parg)
        return pfact

    @classmethod
    def load(cls, context, pfact):
        tup = cls()
        for parg in pfact.args:
           tup.args[context.atoms[parg.role]] = context.atoms[parg.value]
        return tup

class TupleContainer:
    def __init__(self):
        self.tuples = []

    def append(self, args):
        if self.match(args) == None:
            self.tuples.append(Tuple.make(args))

    def match(self, args):
        for t in self.tuples:
            if t.match(args):
                return t
        return None

    def resolve(self, args, targets):
        results = []
        for t in self.tuples:
            if t.match(args):
                results.append( t.get(targets) )
        return results

    def save(self, context, ptuples):
        for t in self.tuples:
            ptuples.append(t.save(context))

    def load(self, context, ptuples):
        for pt in ptuples:
            self.tuples.append(Tuple.load(context, pt))
