import logging
import kessot_pb2
import atom
import tuples
import rule
import empty
import parsing
import bif

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
        self.rules = rule.RuleContainer()
        self.empty = empty.EmptyContainer()
        self.bif = bif.BuiltinFunctions(self.atoms)
        self.parsing = parsing.ParsingContainer()

    def addfact(self, args):
        self.facts.append(self.atoms.atomize(args))

    def addrule(self, header, expressions):
        self.rules.append(self.atoms.atomize(header), list(map(lambda x: self.atoms.atomize(x), expressions)) )

    def addparsing(self, header, expressions):
        self.parsing.append(self.atoms.atomize(header), list(map(lambda x: self.atoms.atomize(x), expressions)) )

    def addempty(self, header, query):
        self.empty.append(self.atoms.atomize(header), self.atoms.atomize(query) )

    def parse(self, context):
        self.parsing.parse(context)

    def getatom(self, astr):
        return self.atoms.get(astr)

    def save(self, filename):
        context = BodySaver(self)
        pbody = kessot_pb2.Body()
        self.atoms.save(context, pbody.atoms)
        self.facts.save(context, pbody.facts)
        self.rules.save(context, pbody.rules)
        self.empty.save(context, pbody.empties)
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
        body.empty.load(context, pbody.empties)
        body.parsing.load(context, pbody.parsing)
        return body

class Query:
    def __init__(self, args, targets):
        self.args = tuples.Tuple.make(args)
        self.targets = targets

    def issame(self, args, targets):
        if not self.args.match(args, strict=True):
            return False
        if len(self.targets) != len(targets):
            return False
        for t in targets:
            if t not in self.targets:
                return False
        return True

class Solver:
    def __init__(self, body):
        self.body = body
        self.queries = []

    def resolve(self, args, targets):
        logging.info(f' {self.indent()}Resolving {args} {targets}')
        if self.checkcycle(args, targets):
            logging.info(' {self.indent()}Cycle detected')
            results = []
        else:
            results = self.body.facts.resolve(args, targets)
            if len(results) == 0:
                results = self.body.rules.resolve(args, targets, self)
            if len(results) == 0 and len(targets) == 0:
                results = self.body.empty.resolve(args, self)
            if len(results) == 0:
                results = self.body.bif.resolve(args, targets, self)
            self.queries.pop(-1)
        logging.info(f' {self.indent()}Concept resolved with with {results}')
        return results

    def checkcycle(self, args, targets):
        for q in self.queries:
            if q.issame(args, targets):
                return True
        self.queries.append( Query(args, targets) )
        return False

    def resolve_strings(self, args, results):
        return self.resolve(self.body.atoms.atomize(args), list(map(lambda x: self.body.atoms.get(x), results)) )

    def indent(self):
        return '  ' * len(self.queries)

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
