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
        friends_specs = Specs(False, True, None, 1)
        specs = Specs(False, False, friends_specs, 0)
        specs._friends_specs._just_uuids = True
        assert not friends_specs._just_uuids
        # specs.print_fields()
