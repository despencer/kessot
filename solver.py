#!/usr/bin/python3

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
        return self.atoms[word]

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
        expressions = []
        expressions.append( ExpressionResolveContext(self) )
        for e in self.rule.expressions:
            nextctx = []
            for ec in expressions:
                query = e.makequery(ec)
                print('q', query.args, query.targets)
                for r in query.resolve():
                    nextctx.append( self.makenext(ec, r) )
            expressions = nextctx
        result = []
        for e in expressions:
            result.append(e.lvars)
            print('qr', e.lvars)
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
        self.args = {}
        self.inplace = []
        self.definition = Fact(definition)
        largs = []
        for d in definition:
            if d[1].isvariable() and d[1] not in self.args:
                self.args[d[0]] = d[1]
                largs.append(d[1])
        print('d', definition)
        self.expressions = []
        for e in expression:
            print('ei', e[1])
            self.expressions.append( Clause( body.getconcept(e[0]), e[1]) )
            for ea in e[1]:
                if ea[1].isvariable() and ea[1] not in largs and ea[1] not in self.inplace:
                    self.inplace.append(ea[1])
        print('a', self.args)
        print('p', self.inplace)

    def resolve(self, args, targets):
        print('rs', targets)
        context = RuleResolveContext(self, args)
        print('cv', context.lvars)
        result = []
        for r in context.resolve():
            ts = []
            for tr in targets:
                ts.append( (tr, r[self.args[tr]]) )
            result.append(ts)
        return result

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
        print('rr', query.targets, resolved, result)
        return result

    def resolve(self, args, targets):
        result = []
        for f in self.facts:
            if f.match(args):
                result.append(f.get(targets))
        if len(result) == 0:
            for r in self.rules:
                result.extend(r.resolve(args, targets))
        return result

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
        self.getconcept( definition[0] ).addrule(body, definition[1], expression)

    def resolve_strings(self, action, args, results):
        (action, args) = self.atomize(action, args)
        results = list(map( lambda x: self.atoms.get(x), results))
        return self.resolve(action, args, results)

    def resolve(self, action, args, results):
        if action not in self.concepts:
            return None
        return self.concepts[action].resolve(args, results)

    def atomize(self, action, args):
        action = self.atoms.get(action)
        args = list(map( lambda x: tuple(map(lambda y:self.atoms.get(y), x.split(':'))), args))
        return (action, args)

    def getconcept(self, action):
        if action not in self.concepts:
            self.concepts[action] = Concept(action)
        return self.concepts[action]

if __name__ == '__main__':
    body = Body()
    body.addfact('plus', ['dobj:1', 'iobj:1', 'result:2'])
    body.addfact('plus', ['dobj:1', 'iobj:2', 'result:3'])
    body.addfact('plus', ['dobj:1', 'iobj:3', 'result:4'])
    body.addfact('plus', ['dobj:1', 'iobj:4', 'result:5'])
    body.addrule( ('plus', ['dobj:$x', 'iobj:$y', 'result:$z']),
                  [ ('plus', ['dobj:1','iobj:$a','result:$x']), ('plus', ['dobj:$a','iobj:$y','result:$b']), ('plus',['dobj:1','iobj:$b','result:$z']) ] )
#    print(body.resolve_strings('plus', ['dobj:1', 'iobj:2'], ['result']))
#    print(body.resolve_strings('plus', ['iobj:3', 'result:4'], ['dobj']))
    print(body.resolve_strings('plus', ['dobj:2', 'iobj:3'], ['result']))
