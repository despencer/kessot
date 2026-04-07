import logging

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

