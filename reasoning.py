import logging
import kessot_pb2
import atom
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

class EmptyRule:
    def __init__(self):
        self.definition = None
        self.query = None

    def __repr__(self):
        return f'<Empty {self.definition} => {self.expressions}>'

    @classmethod
    def make(cls, header, query):
        rule = cls()
        rule.definition = Tuple.make(header)
        rule.query = Tuple.make(query)
        return rule

    def match(self, args, body):
        logging.debug(f'EmptyRule #{id(self):X}: match request for {args}')
        lvars = {}
        for k,v in args.items():
            if k not in self.definition:
                return False
            if self.definition[k].isvariable():
                lvars[ self.definition[k] ] = v
        aquery = {}
        for k,v in self.query.items():
            if v.isvariable():
                aquery[k] = lvars[v]
            else:
                aquery[k]=v
        logging.debug(f'EmptyRule #{id(self):X}: request for body with {aquery}')
        return body.match(aquery)

    def save(self, context):
        prule = kessot_pb2.Empty()
        self.definition.saveto(context, prule.definition)
        self.query.saveto(context, prule.query)
        return prule

    @classmethod
    def load(cls, context, prule):
        rule = cls()
        rule.definition = Tuple.load(context, prule.definition)
        rule.query = Tuple.load(context, prule.query)
        return rule

class EmptyContainer:
    def __init__(self):
        self.rules = []

    def append(self, header, query):
        rule = Empty.make(header, query)
        self.rules.append(rule)
        logging.info(f'{rule} appended')
        return rule

    def match(self, args, body):
        for r in self.rules:
            if r.match(args, body):
                return r

    def save(self, context, prules):
        for r in self.rules:
            prules.append(r.save(context))

    def load(self, context, prules):
        for pr in prules:
            self.rules.append(Rule.load(context, pr))


class ParsingRule:
    def __init__(self):
        self.definition = None
        self.expressions = []

    def __repr__(self):
        return f'<ParsingRule {self.definition} => {self.expressions}>'

    def match(self, context):
        return self.definition.match(context.current[-1], strict=True)

    def apply(self, context):
        logging.debug(f'Applying starts {self} for {context}')
        current = context.current.pop(-1)
        lvars = {}
        for k, v in self.definition:
            if v.isvariable():
                lvars[v] = current[k]
        logging.debug(f'Lvars {lvars}')
        for e in self.expressions:
            nextcur = {}
            for k,v in e:
                if v.isvariable():
                    nextcur[k] = lvars[v]
                else:
                    nextcur[k] = v
            context.current.append(nextcur)
        logging.debug(f'Applying ends {self} for {context}')

    @classmethod
    def make(cls, header, expressions):
        rule = cls()
        rule.definition = Tuple.make(header)
        for e in expressions:
            rule.expressions.append( Tuple.make(e) )
        return rule

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
        return rule

class ParsingContainer:
    def __init__(self):
        self.rules = []

    def append(self, header, expressions):
        rule = ParsingRule.make(header, expressions)
        self.rules.append(rule)
        logging.info(f'{rule} appended')
        return rule

    def parse(self, context):
        logging.info(f'Parsing starts with {context}')
        todo = True
        while todo:
            todo = False
            for r in self.rules:
                if r.match(context):
                    r.apply(context)
                    todo = True
        logging.info(f'Parsing ends with {context}')

    def save(self, context, prules):
        for r in self.rules:
            prules.append(r.save(context))

    def load(self, context, prules):
        for pr in prules:
            self.rules.append(ParsingRule.load(context, pr))

class ParsingContext:
    def __init__(self):
        self.current = [ {} ]

    def __repr__(self):
        return f'{self.current}'

    def put(self, key, value):
        self.current[-1][key] = value

    def get(self, key):
        if key in self.current[-1]:
            return self.current[-1][key]
        return None

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
        self.atoms = atom.AtomManager()
        self.facts = tuples.TupleContainer()
        self.rules = RuleContainer()
        self.empty = EmptyContainer()
        self.parsing = ParsingContainer()

    def addfact(self, args):
        self.facts.append(self.atoms.atomize(args))

    def addrule(self, header, expressions):
        self.rules.append(self.atoms.atomize(header), list(map(lambda x: self.atoms.atomize(x), expressions)) )

    def addparsing(self, header, expressions):
        self.parsing.append(self.atoms.atomize(header), list(map(lambda x: self.atoms.atomize(x), expressions)) )

    def addempty(self, header, query):
        self.empty.append(self.atoms.atomize(header), self.atoms.atomize(query) )

    def resolve(self, args, targets):
        logging.info(f'Resolving {args} {targets}')
        results = self.facts.resolve(args, targets)
        if len(results) == 0:
            results = self.rules.resolve(args, targets, self)
        logging.info(f'Concept resolved with with {results}')
        return results

    def parse(self, context):
        self.parsing.parse(context)

    def resolve_strings(self, args, results):
        return self.resolve(self.atoms.atomize(args), list(map(lambda x: self.atoms.get(x), results)) )

    def getatom(self, astr):
        return self.atoms.get(astr)

    def save(self, filename):
        context = BodySaver(self)
        pbody = kessot_pb2.Body()
        self.atoms.save(context, pbody.atoms)
        self.facts.save(context, pbody.facts)
        self.rules.save(context, pbody.rules)
        self.parsing.save(context, pbody.parsing)
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
        body.parsing.load(context, pbody.parsing)
        return body

class Talker:
    def __init__(self, body):
        self.body = body
        self.next = self.body.getatom('next')
        self.reaction = self.body.getatom('reaction')
        self.context = ParsingContext()
        self.reactions = { self.body.getatom('resolve') : self.resolve }

    def put(self, prompt):
        logging.info(f'Prompt "{prompt}" provided, context={self.context}')
        result = []
        for c in prompt:
            ac = self.body.getatom(c)
            logging.info(f'Processing {ac}, context={self.context}')
            self.context.put(self.next, ac)
            self.body.parse(self.context)
            reaction = self.context.get(self.reaction)
            if reaction != None:
                result.extend( self.reactions[reaction]() )
        logging.info(f'Prompt "{prompt}" done, context={self.context}')
        return ''.join( map(lambda x: x.word, result))

    def resolve(self):
        logging.debug(f'Resolving starts with {self.context}')
        current = self.context.current.pop(-1)
        current.pop(self.reaction)
        self.context.current.append({})
        question = current.pop(self.body.getatom('question'))
        result = self.body.resolve(current, [ question ] )
        logging.debug(f'Resolving ends with {self.context}')
        if len(result) > 0:
            if question in result[0]:
                return [ result[0][question] ]
        return []

def load(filename):
    return Body.load(filename)

def maketalker(filename):
    return Talker(load(filename))
