#!/usr/bin/python3

import logging
import reasoning

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, filename='loader.log', filemode='w',
                        format='%(asctime)s %(name)s %(levelname)s %(message)s')
    body = reasoning.Body()
    body.addfact('plus', ['dobj:1', 'iobj:1', 'result:2'])
    body.addfact('plus', ['dobj:1', 'iobj:2', 'result:3'])
    body.addfact('plus', ['dobj:1', 'iobj:3', 'result:4'])
    body.addfact('plus', ['dobj:1', 'iobj:4', 'result:5'])
    body.addrule( ('plus', ['dobj:$x', 'iobj:$y', 'result:$z']),
                  [ ('plus', ['dobj:1','iobj:$a','result:$x']), ('plus', ['dobj:$a','iobj:$y','result:$b']), ('plus',['dobj:1','iobj:$b','result:$z']) ] )
    body.save('calc.kess')

