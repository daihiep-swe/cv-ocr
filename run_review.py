#!/usr/bin/env python3
"""
Review exam script wrapper
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.review import main

if __name__ == "__main__":
    main()
