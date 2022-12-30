import pytest
from copy import deepcopy

from Utils import *
from Files import *
from MyClasses import *
from Player import *

Specs.set_common_specs(False, False)

class Tests:
    @pytest.fixture
    def example_fixture(self):
        pass
    
    def test_deep_copy_Specs_constructor(self):
        friends_specs = Specs(True, True, None, 1)
        specs = Specs(True, False, friends_specs, 0)
        specs._friends_specs._include_players_name_and_fkdr = False
        assert friends_specs._include_players_name_and_fkdr
        # specs.print_fields()
