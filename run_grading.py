#!/usr/bin/env python3
"""
Wrapper script to run the exam grading system from root directory
Chạy chương trình chấm điểm từ thư mục gốc
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run main app
from src.app import main

if __name__ == "__main__":
    main()
