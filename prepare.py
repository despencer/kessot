#!/usr/bin/python3

import logging
import reasoning

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, filename='loader.log', filemode='w',
                        format='%(asctime)s %(name)s %(levelname)s %(message)s')
    body = reasoning.Body()
    body.addfact({'action':'plus', 'dobj':'1', 'iobj':'1', 'result':'2'})
    body.addfact({'action':'plus', 'dobj':'1', 'iobj':'2', 'result':'3'})
    body.addfact({'action':'plus', 'dobj':'1', 'iobj':'3', 'result':'4'})
    body.addfact({'action':'plus', 'dobj':'1', 'iobj':'4', 'result':'5'})
    body.addrule( {'action':'plus','dobj':'$x', 'iobj':'$y', 'result':'$z'},
          [ {'action':'plus', 'dobj':'1', 'iobj':'$a', 'result':'$x'},
            {'action':'plus', 'dobj':'$a', 'iobj':'$y', 'result':'$b'},
            {'action':'plus', 'dobj':'1', 'iobj':'$b', 'result':'$z'} ] )
    body.save('calc.kess')

