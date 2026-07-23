# tests/conftest.py
import sys
import os

# Добавляем пути к исходному коду
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))
