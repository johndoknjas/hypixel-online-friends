import pytest

from MyClasses import Specs
import leveling

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
    
    def test_network_levels(self):
        level_range = range(1, 10000)
        xps = [leveling.getTotalExpToLevelFloor(l) for l in level_range]
        assert xps[0] == 0 and xps[1] == 10000 and xps[2] == 22500 and xps[-1] == 125037487500
        assert all(isinstance(xp, int) for xp in xps)
        for i, xp in enumerate(xps):
            lvl = level_range[i]
            assert leveling.getLevelFloor(xp) == lvl
            if xp > 0:
                assert leveling.getLevelFloor(xp-1) == lvl-1
            assert leveling.getLevelFloor(xp+1) == lvl

    def test_leveling_errors(self):
        with pytest.raises(AssertionError):
            leveling.getLevelFloor(0.0001)
        with pytest.raises(AssertionError):
            leveling.getLevelFloor(10000-0.0001)
        with pytest.raises(AssertionError):
            leveling.getTotalExpToLevelFloor(0)
        with pytest.raises(AssertionError):
            leveling.getTotalExpToLevelFloor(10000)
        with pytest.raises(AssertionError):
            leveling.getTotalExpToLevelFloor(1.00001)
        with pytest.raises(AssertionError):
            leveling.getTotalExpToLevelFloor(1.9999)
