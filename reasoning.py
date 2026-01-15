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

    def save(self, context, patoms):
        for i, a in enumerate(self.atoms.values()):
            pa = kessot_pb2.Atom()
            pa.id = i
            pa.word = a.word
            patoms.append(pa)
            context.atoms[a] = i

class Fact:
    def __init__(self, args):
        self.args = {}
        for a in args:
            self.args[a[0]] = a[1]

    def match(self, args):
        for a in args:
            if a[0] not in self.args or self.args[a[0]] != a[1]:
                return False
        return True

    def get(self, targets):
        result = []
        for t in targets:
            if t in self.args:
                result.append( (t, self.args[t]) )
            else:
                result.append( (t, None) )
        return result

    def makequery(self, context, query):
        for aname, avalue in self.args.items():
            if avalue.isvariable():
                value = context.getvalue(avalue)
                if value == None:
                    query.targets.append( (aname, avalue) )
                    query.tarvars[aname] = avalue
                else:
                    query.args.append( (aname, value) )
            else:
                query.args.append( (aname, avalue) )

    def __repr__(self):
        return f'<Fact {self.args}>'

    def save(self, context):
        pfact = kessot_pb2.Fact()
        for ak, av in self.args.items():
            parg = kessot_pb2.Argument()
            parg.role = context.atoms[ak]
            parg.value = context.atoms[av]
            pfact.args.append(parg)
        return pfact

class Query:
    def __init__(self, action):
        self.action = action
        self.args = []
        self.targets = []
        self.tarvars = {}

    def resolve(self):
        return self.action.resolvequery(self)

class Clause:
    def __init__(self, action, args):
        self.action = action
        self.args = Fact(args)

    def makequery(self, context):
        query = Query(self.action)
        self.args.makequery(context, query)
        return query

    def save(self, context):
        pclause = kessot_pb2.Clause()
        pclause.action = context.atoms[self.action.action]
        pclause.args.CopyFrom( self.args.save(context) )
        return pclause

class RuleResolveContext:
    def __init__(self, rule, args):
        self.rule = rule
        self.lvars = {}
        for v in self.rule.args.values():
            self.lvars[v] = None
        for a in args:
            self.lvars[self.rule.args[a[0]]] = a[1]
        self.expressions = []

    def resolve(self):
        logging.debug(f'Resolving context #{id(self):X}: {self.rule} with {self.lvars}')
        expressions = []
        expressions.append( ExpressionResolveContext(self) )
        for e in self.rule.expressions:
            nextctx = []
            for ec in expressions:
                query = e.makequery(ec)
                logging.debug(f'Resolving context #{id(self):X}: expression query {query.args} {query.targets}')
                for r in query.resolve():
                    nextctx.append( self.makenext(ec, r) )
            expressions = nextctx
        result = []
        for e in expressions:
            result.append(e.lvars)
            logging.debug(f'Resolving context #{id(self):X}: result {e.lvars}')
        return result

    def makenext(self, ectx, varval):
        result = ExpressionResolveContext(self)
        for n,v in ectx.lvars.items():
            if v != None:
                result.lvars[n] = v
        for n,v in varval.items():
            result.lvars[n] = v
        return result

class ExpressionResolveContext:
    def __init__(self,  context):
        self.context = context
        self.lvars = {}
        for v in self.context.rule.inplace:
            self.lvars[v] = None

    def getvalue(self, varname):
        if varname in self.lvars:
            return self.lvars[varname]
        return self.context.lvars[varname]

class Rule:
    def __init__(self, body, definition, expression):
        ''' definition is a list of args; expression is a list of tuples (action, args). Args are tuples themselves '''
        logging.debug(f'Rule #{id(self):X} creation for {definition} {expression}')
        self.args = {}
        self.inplace = []
        self.definition = Fact(definition)
        largs = []
        for d in definition:
            if d[1].isvariable() and d[1] not in self.args:
                self.args[d[0]] = d[1]
                largs.append(d[1])
        self.expressions = []
        for e in expression:
            self.expressions.append( Clause( body.getconcept(e[0]), e[1]) )
            for ea in e[1]:
                if ea[1].isvariable() and ea[1] not in largs and ea[1] not in self.inplace:
                    self.inplace.append(ea[1])
        logging.debug(f'Rule #{id(self):X} created with {self.args} and {self.inplace}')

    def resolve(self, args, targets):
        logging.debug(f'Rule #{id(self):X} resolving with {args} and {targets}')
        context = RuleResolveContext(self, args)
        logging.debug(f'Rule #{id(self):X} resolving, context #{id(context):X} created with {context.lvars}')
        result = []
        for r in context.resolve():
            ts = []
            for tr in targets:
                ts.append( (tr, r[self.args[tr]]) )
            result.append(ts)
        return result

    def __repr__(self):
        return f'<Rule {self.args} {self.definition} {self.inplace}>'

    def save(self, context):
        prule = kessot_pb2.Rule()
        prule.definition.CopyFrom( self.definition.save(context) )
        for e in self.expressions:
            prule.expressions.append( e.save(context) )
        return prule

class Concept:
    def __init__(self, action):
        self.action = action
        self.facts = []
        self.rules = []

    def append(self, args):
        for f in self.facts:
            if f.match(args):
                return
        self.facts.append( Fact(args) )
        logging.debug(f'Concept {self.action} {args} added')

    def addrule(self, body, definition, expression):
        self.rules.append( Rule(body, definition, expression) )

    def resolvequery(self, query):
        resolved = self.resolve(query.args, map(lambda x:x[0], query.targets) )
        result = []
        for r in resolved:
            vals = {}
            for k,v in r:
                vals[query.tarvars[k]] = v
            result.append(vals)
        logging.info(f'Concept resolved query with {query.targets} and {resolved} with {result}')
        return result

    def resolve(self, args, targets):
        result = []
        for f in self.facts:
            if f.match(args):
                result.append(f.get(targets))
        if len(result) == 0:
            for r in self.rules:
                result.extend(r.resolve(args, targets))
        logging.info(f'Concept resolved with with {result}')
        return result

    def save(self, context):
        pconcept = kessot_pb2.Concept()
        pconcept.action = context.atoms[self.action]
        for f in self.facts:
            pconcept.facts.append(f.save(context))
        for r in self.rules:
            pconcept.rules.append(r.save(context))
        return pconcept

class BodySaver:
    def __init__(self):
        self.atoms = {}
        self.concepts = {}

class Body:
    def __init__(self):
        self.atoms = AtomManager()
        self.concepts = {}

    def addfact(self, action, args):
        (action, args) = self.atomize(action, args)
        self.getconcept(action).append(args)

    def addrule(self, definition, expression):
        definition = self.atomize(*definition)
        expression = list(map( lambda x: self.atomize(*x), expression))
        self.getconcept( definition[0] ).addrule(self, definition[1], expression)

    def resolve_strings(self, action, args, results):
        (action, args) = self.atomize(action, args)
        results = list(map( lambda x: self.atoms.get(x), results))
        return self.resolve(action, args, results)

    def resolve(self, action, args, results):
        if action not in self.concepts:
            return None
        logging.info(f'Resolving {action} {args} {results}')
        return self.concepts[action].resolve(args, results)

    def atomize(self, action, args):
        action = self.atoms.get(action)
        args = list(map( lambda x: tuple(map(lambda y:self.atoms.get(y), x.split(':'))), args))
        return (action, args)

    def getconcept(self, action):
        if action not in self.concepts:
            self.concepts[action] = Concept(action)
        return self.concepts[action]

    def save(self, filename):
        context = BodySaver()
        pbody = kessot_pb2.Body()
        self.atoms.save(context, pbody.atoms)
        for c in self.concepts.values():
            context.concepts[c] = context.atoms[c.action]
        for c in self.concepts.values():
            pbody.concepts.append( c.save(context) )
        with open(filename, 'wb') as f:
            f.write(pbody.SerializeToString())
