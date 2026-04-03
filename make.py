#!/usr/bin/python3

import yaml
import logging
import reasoning
import interface

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, filename='make.log', filemode='w',
                        format='%(asctime)s %(name)s %(levelname)s %(message)s')
    with open('calc.prompt') as fprompt:
        yprompt = yaml.load(fprompt, Loader=yaml.Loader)
        body = reasoning.Body()
        interface = interface.Interface(body)
        interface.do(yprompt)
        body.save('calc.kess')