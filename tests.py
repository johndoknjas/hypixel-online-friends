from __future__ import annotations
import subprocess
from subprocess import PIPE
import glob
import pytest
import vulture # type: ignore
import mypy.api

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

    def test_vulture(self):
        v = vulture.Vulture()
        v.scavenge(['.'])
        assert not v.get_unused_code()
        # https://stackoverflow.com/a/59564370/7743427

    def test_mypy(self):
        assert mypy.api.run(['.']) == ('Success: no issues found in 19 source files\n', '', 0)
        # https://mypy.readthedocs.io/en/stable/extending_mypy.html#integrating-mypy-into-another-python-application

    def test_vermin(self):
        result = subprocess.run(['vermin', 'hypickle'], stdout=PIPE, stderr=PIPE, universal_newlines=True)
        expected_output = """Tips:
            - Generic or literal annotations might be in use. If so, try using: --eval-annotations
            But check the caveat section: https://github.com/netromdk/vermin#caveats
            - You're using potentially backported modules: dataclasses, enum, typing
            If so, try using the following for better results: --backport dataclasses --backport enum --backport typing
            - Since '# novm' or '# novermin' weren't used, a speedup can be achieved using: --no-parse-comments
            (disable using: --no-tips)

            Minimum required versions: 3.8
            Incompatible versions:     2"""
        assert (
            [line.strip() for line in expected_output.splitlines()] ==
            [line.strip() for line in result.stdout.splitlines()]
        )
        assert (result.returncode, result.stderr) == (0, '')

    def test_future_annotations(self):
        for filename in glob.iglob('**/*.py', recursive=True):
            assert filename.endswith(".py")
            with open(filename) as file:
                first_code_line = next(
                    (line.rstrip('\n') for line in file.readlines() if is_code_line(line)), None
                )
                if filename in (r"hypickle/__init__.py", r"hypickle\__init__.py"):
                    assert first_code_line is None
                else:
                    assert first_code_line == "from __future__ import annotations"

# Helpers:

def is_code_line(line: str) -> bool:
    return (bool(line.strip()) and not line.lstrip().startswith(('#', '"""')) and
            not line.rstrip().endswith('"""'))

if __name__ == '__main__':
    non_automated_tests()
