from __future__ import annotations
from lintception import linters # type: ignore
import pytest

from hypickle.MyClasses import Specs
from hypickle import leveling, Colours

Specs.set_common_specs(False)

def print_pit_colours() -> None:
    """Tests all the 13 pit ranks shown in the image here: https://pit.wiki/Prestige.
       These contain all prestige and level colours."""
    ranks = ("0-84", "II-40", "VI-39", "XIV-16", "XV-113", "XXII-1", "XXVIII-98",
             "XXXI-62", "XXXIX-101", "XLII-56", "XLVI-25", "XLIX-77", "L-120")
    for rank in ranks:
        Colours.print_pit_rank(rank)

def non_automated_tests() -> None:
    print_pit_colours()

class Tests:
    """
    @pytest.fixture
    def example_fixture(self):
        pass
    """

    def test_deep_copy_Specs_constructor(self):
        friends_specs = Specs(False, True, None, 1)
        specs = Specs(False, False, friends_specs, 0)
        specs._friends_specs._just_uuids = True
        assert not friends_specs._just_uuids

    def test_network_levels(self):
        level_range = range(1, 10001)
        xps = [leveling.getTotalExpToLevelFloor(l) for l in level_range]
        assert xps[0] == 0 and xps[1] == 10000 and xps[2] == 22500 and xps[-1] == 125062492500
        assert all(isinstance(xp, int) for xp in xps)
        expected_xp = 0
        for i, xp in enumerate(xps):
            assert xp == expected_xp
            lvl = level_range[i]
            assert leveling.getLevelFloor(xp) == lvl
            if xp > 0:
                assert leveling.getLevelFloor(xp-1) == lvl-1
            assert leveling.getLevelFloor(xp+1) == lvl
            with pytest.raises(AssertionError):
                leveling.getLevelFloor(xp-0.00001)
            with pytest.raises(AssertionError):
                leveling.getLevelFloor(xp+0.00001)
            expected_xp += (10000 + 2500*i)

    def test_leveling_errors(self):
        with pytest.raises(AssertionError):
            leveling.getTotalExpToLevelFloor(0)
        with pytest.raises(AssertionError):
            leveling.getLevelFloor(-1)
        leveling.getLevelFloor(1_000_000_000_000)
        with pytest.raises(AssertionError):
            leveling.getLevelFloor(1_000_000_000_001)
        with pytest.raises(AssertionError):
            leveling.getTotalExpToLevelFloor(10001)
        with pytest.raises(AssertionError):
            leveling.getTotalExpToLevelFloor(1.00001)
        with pytest.raises(AssertionError):
            leveling.getTotalExpToLevelFloor(1.9999)

    def test_lintception(self):
        assert linters.run_linters() == linters.LintResult.SUCCESS

if __name__ == '__main__':
    non_automated_tests()
