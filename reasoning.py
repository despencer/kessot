#!/usr/bin/python3

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

class Tuple:
    def __init__(self):
        self.args = {}

    def __iter__(self):
        return iter(self.args.items())

    def __getitem__(self, key):
        return self.args[key]

    def __contains__(self, key):
        return key in self.args

    def match(self, args):
        for k,v in args.items():
            if k not in self.args:
                return False
            if (not self.args[k].isvariable()) and self.args[k] != v:
                return False
        return True

    def get(self, targets):
        result = {}
        for t in targets:
            if t in self.args:
                result[t] = self.args[t]
            else:
                result[t] = None
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

class RuleExpressionSolver:
    def __init__(self, lvars):
        self.lvars = dict(lvars)

    def __repr__(self):
        return f'<RES {self.lvars}>'

    def __iter__(self):
        return iter(self.lvars.items())

    def __getitem__(self, key):
        return self.lvars[key]

    def __contains__(self, key):
        return key in self.lvars

    def solve(self, expression, body):
        logging.debug(f'RES #{id(self):X}: local vars {self.lvars} expression {expression}')
        args = {}
        targets = []
        for k,v in expression:
            if v.isvariable():
                if self.lvars[v] == None:
                    targets.append(k)
                else:
                    args[k] = self.lvars[v]
            else:
                args[k] = v
        res = body.resolve(args, targets)
        logging.debug(f'RES #{id(self):X}: {args} for {targets} => {res}')
        results = []
        for r in res:
            tarvar = dict(self.lvars)
            for k,v in expression:
                if v.isvariable() and tarvar[v] == None:
                    tarvar[v] = r[k]
            results.append(tarvar)
        return results

class RuleSolver:
    def __init__(self, rule, body):
        self.rule = rule
        self.body = body

    def run(self, args):
        lvars = dict(self.rule.lvars)
        for k,v in self.rule.definition:
            if v.isvariable() and k in args:
                lvars[v] = args[k]
        logging.debug(f'RuleSolver #{id(self):X}: started local vars set to {lvars}')
        current = [ RuleExpressionSolver(lvars) ]
        for e in self.rule.expressions:
            nextctx = []
            for c in current:
                results = c.solve(e, self.body)
                logging.debug(f'RuleSolver #{id(self):X}: intermediate results {results}')
                for r in results:
                    nextctx.append( RuleExpressionSolver(r) )
            current = nextctx
        logging.debug(f'RuleSolver #{id(self):X}: finished with {current}')
        return current

class Rule:
    def __init__(self):
        self.definition = None
        self.expressions = []
        self.lvars = {}

    def makevars(self):
        self.lvars = {}
        for d in [ self.definition, *self.expressions ]:
            for v in d.getvars():
                self.lvars[v] = None

    def __repr__(self):
        return f'<Rule {self.definition} => {self.expressions}>'

    @classmethod
    def make(cls, header, expressions):
        rule = cls()
        rule.definition = Tuple.make(header)
        for e in expressions:
            rule.expressions.append( Tuple.make(e) )
        rule.makevars()
        return rule

    def match(self, args):
        return self.definition.match(args)

    def apply(self, args, targets, body):
        logging.debug(f'Applying {args} for {targets} to {self.expressions}')
        solver = RuleSolver(self, body)
        results = []
        for r in solver.run(args):
            resvar = {}
            for t in targets:
                resvar[t] = r[self.definition[t]]
            results.append(resvar)
        return results

    def save(self, context):
        prule = kessot_pb2.Rule()
        self.definition.saveto(context, prule.definition)
        for e in self.expressions:
            prule.expressions.append( e.save(context) )
        return prule

    @classmethod
    def load(cls, context, prule):
        rule = cls()
        rule.definition = Tuple.load(context, prule.definition)
        for e in prule.expressions:
            rule.expressions.append( Tuple.load(context, e) )
        rule.makevars()
        return rule

class RuleContainer:
    def __init__(self):
        self.rules = []

    def append(self, header, expressions):
        rule = Rule.make(header, expressions)
        self.rules.append(rule)
        logging.info(f'{rule} appended')
        return rule

    def resolve(self, args, targets, body):
        results = []
        for r in self.rules:
            if r.match(args):
                results.extend( r.apply(args, targets, body) )
        return results

    def save(self, context, prules):
        for r in self.rules:
            prules.append(r.save(context))

    def load(self, context, prules):
        for pr in prules:
            self.rules.append(Rule.load(context, pr))


class BodySaver:
    def __init__(self, body):
        self.body = body
        self.atoms = {}

class BodyLoader:
    def __init__(self, body):
        self.body = body
        self.atoms = {}

class Body:
    def __init__(self):
        self.atoms = AtomManager()
        self.facts = TupleContainer()
        self.rules = RuleContainer()

    def addfact(self, args):
        self.facts.append(self.atoms.atomize(args))

    def addrule(self, header, expressions):
        self.rules.append(self.atoms.atomize(header), list(map(lambda x: self.atoms.atomize(x), expressions)) )

    def resolve(self, args, targets):
        logging.info(f'Resolving {args} {targets}')
        results = self.facts.resolve(args, targets)
        if len(results) == 0:
            results = self.rules.resolve(args, targets, self)
        logging.info(f'Concept resolved with with {results}')
        return results

    def resolve_strings(self, args, results):
        return self.resolve(self.atoms.atomize(args), list(map(lambda x: self.atoms.get(x), results)) )

    def save(self, filename):
        context = BodySaver(self)
        pbody = kessot_pb2.Body()
        self.atoms.save(context, pbody.atoms)
        self.facts.save(context, pbody.facts)
        self.rules.save(context, pbody.rules)
        with open(filename, 'wb') as f:
            f.write(pbody.SerializeToString())

    @classmethod
    def load(cls, filename):
        pbody = kessot_pb2.Body()
        with open(filename, 'rb') as f:
            pbody.ParseFromString(f.read())
        body = cls()
        context = BodyLoader(body)
        body.atoms.load(context, pbody.atoms)
        body.facts.load(context, pbody.facts)
        body.rules.load(context, pbody.rules)
        return body

def load(filename):
    return Body.load(filename)
