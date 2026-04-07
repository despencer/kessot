import logging
import reasoning

def select(lookup, item):
    itemtype = list(item.keys())[0]
    if itemtype not in lookup:
        raise Exception(f'Unknown option {itemtype}')
    return lookup[itemtype], item[itemtype]

class Test:
    def __init__(self, body):
        self.body = body
        self.solver = reasoning.Solver(body)

    def do(self, prompt):
        logging.info('Entering test mode')
        for yfunc in prompt:
            func, value = select( {'resolve': self.resolve}, yfunc)
            func(value)
        logging.info('Leaving test mode')

    def resolve(self, ytest):
        logging.info(f'About to test resolve {ytest}')
        results = self.solver.resolve_strings( ytest['args'], list(ytest['targets'].keys()) )
        if len(results) != 1:
            print(f'Bad number of results {len(results)}')
        else:
            results = results[0]
            for k,v in ytest['targets'].items():
                ak = self.body.getatom(k)
                if ak not in results:
                    print(f"key '{k}' is not found among results '{results}' in test {ytest}")
                else:
                    if results[ak] != self.body.getatom(v):
                        print(f"Different result for '{k}': {results[ak]} vs '{v}' in test {ytest}")
            if len(results) != len(ytest['targets']):
                print(f"Different number of results {len(results)} vs {len(ytest['targets'])} in test {ytest}")
        logging.info(f'Test {ytest} finished')

class Maintenance:
    def __init__(self, body):
        self.body = body

    def do(self, prompt):
        logging.info('Entering maintenance mode')
        for yfunc in prompt:
            func, value = select( {'fact': self.addfact, 'rule':self.addrule}, yfunc)
            func(value)
        logging.info('Leaving maintenance mode')

    def addfact(self, yfact):
        logging.info(f'About to add fact {yfact}')
        self.body.addfact(yfact)
        logging.info(f'Fact {yfact} added')

    def addrule(self, yrule):
        logging.info(f'About to add rule {yrule}')
        self.body.addrule(yrule['definition'], yrule['expression'])
        logging.info(f'Fact {yrule} added')

class Interface:
    def __init__(self, body):
        self.body = body

    def do(self, prompt):
        for ymode in prompt:
            cls, value = select( {'maintenance':Maintenance, 'test':Test}, ymode)
            mode = cls(self.body)
            mode.do(value)
