#!/usr/bin/env python3

import os
import sys
from logging import basicConfig, INFO, getLogger

basicConfig(format='%(asctime)s %(levelname)s [%(process)d/%(threadName)s %(pathname)s:%(lineno)d]: %(message)s',
            stream=sys.stderr, level=INFO)


logger = getLogger("makeradmin")


def main():

    logger.info("I am MultiAccessSync, hello!")
    
    raise Exception("Hej")
    
    
if __name__ == '__main__':

    try:
        main()
        if os.name == 'nt':
            input("Export finished, enter to close: ")
    except Exception as e:
        if os.name == 'nt':
            logger.exception(e)
            input("Program failed, enter to close: ")
        else:
            raise
