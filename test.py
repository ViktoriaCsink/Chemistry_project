# -*- coding: utf-8 -*-
"""
Test Chemistry_recipes.ipynb

"""

from main_chemicals import main_chemicals


def test():
    
    x = main_chemicals()
    
    assert isinstance(x, list)
