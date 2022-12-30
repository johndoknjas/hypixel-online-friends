import pytest
import copy

from Utils import *
from Files import *
from MyClasses import *
from Player import *

Specs.set_common_specs(False, False)

@deep_copy_params
def modify_params(d1: dict, d2: dict, l1: list = [], player: Player = []) -> None:
    d1[3] = 'three'
    d2['val'] = 'text'
    d2['friend'].set_friends(None)
    l1.extend([4,5])
    player.set_specs(Specs(False, False, None, 0))

class Tests:
    @pytest.fixture
    def example_fixture(self):
        pass

    def test_deep_copy_decorator(self):
        specs = Specs(False, True, Specs(False, False, None, 2), 1)
        vars = {'d1': {1: 'one', 2: 'two'}, 'd2': {'friend': Player(get_uuid('itstreasonthen'), specs=specs)},
                'p1': Player(get_uuid('itstreasonthen'), specs=specs), 'l1': [1,2,3]}
        original_vals = copy.deepcopy(vars)
        modify_params(vars['d1'], vars['d2'], vars['l1'], vars['p1'])
        assert vars == original_vals
        print(vars)
        print(original_vals)
