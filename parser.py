#!/usr/bin/python3

import logging
import reasoning

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, filename='parser.log', filemode='w',
                        format='%(asctime)s %(name)s %(levelname)s %(message)s')
    talker = reasoning.maketalker('calc.kess')
    print(talker.put('1+1?'))
    print(talker.put('2+3?'))