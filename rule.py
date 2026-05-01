import logging
import kessot_pb2
import tuples

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
        rule.definition = tuples.Tuple.make(header)
        for e in expressions:
            rule.expressions.append( tuples.Tuple.make(e) )
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
            if len(results) > 0:
                break
        return results

    def save(self, context, prules):
        for r in self.rules:
            prules.append(r.save(context))

    def load(self, context, prules):
        for pr in prules:
            self.rules.append(Rule.load(context, pr))
