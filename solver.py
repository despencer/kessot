#!/usr/bin/python3

import logging
import reasoning

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, filename='solver.log', filemode='w',
                        format='%(asctime)s %(name)s %(levelname)s %(message)s')
    body = reasoning.Body()
    print(body.resolve_strings('plus', ['dobj:1', 'iobj:2'], ['result']))
    print(body.resolve_strings('plus', ['iobj:3', 'result:4'], ['dobj']))
    print(body.resolve_strings('plus', ['dobj:2', 'iobj:3'], ['result']))
