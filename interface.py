import logging

def select(lookup, item):
    itemtype = list(item.keys())[0]
    if itemtype not in lookup:
        raise Exception(f'Unknown option {itemtype}')
    return lookup[itemtype], item[itemtype]

class Maintenance:
    def __init__(self, body):
        self.body = body

    def do(self, prompt):
        logging.info('Entering maintenance mode')
        for yfunc in prompt:
            func, value = select( {'fact': self.addfact}, yfunc)
            func(value)
        logging.info('Leaving maintenance mode')

    def addfact(self, yfact):
        logging.info(f'About to add fact {yfact}')
        self.body.addfact(yfact)
        logging.info(f'Fact {yfact} added')

class Interface:
    def __init__(self, body):
        self.body = body

    def do(self, prompt):
        for ymode in prompt:
            cls, value = select( {'maintenance':Maintenance}, ymode)
            mode = cls(self.body)
            mode.do(value)
