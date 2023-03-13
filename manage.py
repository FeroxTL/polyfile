#!/usr/bin/env python
import os

from polyfile.__main__ import main

if __name__ == '__main__':
    os.environ.setdefault('DEBUG', 'True')
    main()
