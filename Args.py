from typing import List, Optional
import copy

import Utils
import Files

class Args:
    def __init__(self, args: List[str]):
        args = [arg if arg.endswith('.txt') else arg.lower() for arg in args[1:]]
        self._ARGS = Files.apply_aliases(args)
        self._ARG_KEYWORDS = ['all', 'friendsoffriends', 'justuuids', 'checkresults', 'epoch',
                              'diff', 'diffl', 'diffr', 'starsort', 'pitsort',
                              'fileoutput', 'updateuuids', 'minusresults',
                              'matchingignsuuids', 'includemultiplayerfiles',
                              'keepfirstdictmultifiles', 'notallfromresults',
                              'addadditionalfriends', 'addadditionals',
                              'noadditionalfriends', 'noadditionals', 'addaliases',
                              'getplayerjson', 'playerjson', 'noverify', 'dontverify']
        # These keywords are possible options the user can specify for using the program. All of these are
        # 'non-positional'; i.e., it doesn't matter where they appear in the user's command line argument list.
        # For 'positional' arguments, there are fewer (e.g., '-', 'fromresults', 'friendedwhen', 'intersect'). 
        # They don't appear in this class, but are instead used directly in the logic for main.py.
        Utils.print_list(self.get_args(False, False), prepended_msg="self._ARGS list after applying aliases: ")
        self._validation_checks()
    
    def get_args(self, remove_keywords: bool, remove_dates: bool) -> List[str]:
        args = copy.copy(self._ARGS)
        if remove_keywords:
            args = Utils.list_subtract(args, self._ARG_KEYWORDS)
        if remove_dates:
            args = Utils.remove_date_strings(args)
        return args

    def get_keywords(self) -> List[str]:
        return copy.copy(self._ARG_KEYWORDS)
    
    def find_friends_of_friends(self) -> bool:
        return 'friendsoffriends' in self._ARGS
    
    def just_online_friends(self) -> bool:
        return 'all' not in self._ARGS and not self.find_friends_of_friends()
    
    def check_results(self) -> bool:
        return 'checkresults' in self._ARGS or self.minus_results()
    
    def diff_left_to_right(self) -> bool:
        return 'diff' in self._ARGS or 'diffr' in self._ARGS
    
    def diff_right_to_left(self) -> bool:
        return 'diff' in self._ARGS or 'diffl' in self._ARGS
    
    def sort_by_star(self) -> bool:
        return 'starsort' in self._ARGS
    
    def sort_by_pit_rank(self) -> bool:
        return 'pitsort' in self._ARGS
    
    def epoch(self) -> bool:
        return 'epoch' in self._ARGS
    
    def just_uuids(self) -> bool:
        return 'justuuids' in self._ARGS
    
    def date_cutoff(self) -> Optional[str]:
        return Utils.get_date_string_if_exists(self._ARGS)
    
    def do_file_output(self) -> bool:
        return 'fileoutput' in self._ARGS
    
    def update_uuids(self) -> bool:
        return 'updateuuids' in self._ARGS
    
    def minus_results(self) -> bool:
        """Return true if the user doesn't want to get f lists of uuids that already have their f list
        stored in the results folder."""
        return 'minusresults' in self._ARGS
    
    def find_matching_igns_or_uuids_in_results(self) -> bool:
        return 'matchingignsuuids' in self._ARGS
    
    def include_multi_player_files(self) -> bool:
        return 'includemultiplayerfiles' in self._ARGS
    
    def skip_first_dict_in_multi_player_files(self) -> bool:
        assert self.include_multi_player_files()
        # Only makes sense to call this function if the above is true.
        return 'keepfirstdictmultifiles' not in self._ARGS
    
    def from_results_for_all(self) -> bool:
        return 'notallfromresults' not in self._ARGS
    
    def add_additional_friends(self) -> bool:
        return any(x in self._ARGS for x in ['addadditionalfriends', 'addadditionals'])
    
    def get_additional_friends(self) -> bool:
        return all(x not in self._ARGS for x in ['noadditionalfriends', 'noadditionals'])
    
    def add_aliases(self) -> bool:
        return 'addaliases' in self._ARGS
    
    def get_player_json(self) -> bool:
        return 'getplayerjson' in self._ARGS or 'playerjson' in self._ARGS
    
    def verify_requests(self) -> bool:
        return 'noverify' not in self._ARGS and 'dontverify' not in self._ARGS
    
    def do_mini_program(self) -> bool:
        mini_programs = [self.add_aliases(), self.add_additional_friends(), self.get_player_json()]
        assert (bool_sum := sum(1 for x in mini_programs if x)) <= 1
        return bool_sum == 1
    
    def _validation_checks(self) -> None:
        assert set(self.get_keywords()).isdisjoint([pair[0] for pair in Files.get_aliases()])
        if self.do_file_output():
            assert self.date_cutoff() is None and not self.just_online_friends() and not self.minus_results()
        assert not (self.sort_by_pit_rank() and self.sort_by_star())
        if self.add_aliases():
            assert len(self.get_args(False, False)) == 1
        if self.add_additional_friends():
            assert len(self.get_args(True, True)) == 1
        if self.get_player_json():
            assert len(self.get_args(True, True)) >= 1