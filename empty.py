import logging

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
