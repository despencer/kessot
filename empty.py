import logging
import tuples
import kessot_pb2

class EmptyRule:
    def __init__(self):
        self.definition = None
        self.query = None

    def __repr__(self):
        return f'<Empty {self.definition} => {self.query}>'

    @classmethod
    def make(cls, header, query):
        rule = cls()
        rule.definition = tuples.Tuple.make(header)
        rule.query = tuples.Tuple.make(query)
        return rule

    def match(self, args, solver):
        return self.definition.match(args)

    def resolve(self, args, solver):
        logging.debug(f'{solver.indent()}EmptyRule #{id(self):X}: {self} resolve request for {args}')
        lvars = self.definition.matchvars(args)
        logging.debug(f'{solver.indent()}EmptyRule #{id(self):X}: vars: {lvars}')
        aquery = self.query.substitute(lvars)
        logging.debug(f'{solver.indent()}EmptyRule #{id(self):X}: query: {aquery}')
        if len(solver.resolve(aquery, [])) == 0:
            result = [ {} ]
        else:
            result = []
        logging.debug(f'{solver.indent()}EmptyRule #{id(self):X}: returns with {result}')
        return result

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
        rule = EmptyRule.make(header, query)
        self.rules.append(rule)
        logging.info(f'{rule} appended')
        return rule

    def resolve(self, args, solver):
        results = []
        for r in self.rules:
            if r.match(args, solver):
                results.extend(r.resolve(args, solver))
            if len(results) > 0:
                break
        return results

    def save(self, context, prules):
        for r in self.rules:
            prules.append(r.save(context))

    def load(self, context, prules):
        for pr in prules:
            self.rules.append(EmptyRule.load(context, pr))

