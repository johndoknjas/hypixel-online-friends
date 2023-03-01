from typing import List, Optional

import Utils

class Args:
    def __init__(self, args: List[str], extra_keywords: List[str] = []):
        self._ARGS = [arg if arg.endswith('.txt') else arg.lower() for arg in args[1:]]
        self._ARG_KEYWORDS = (  ['all', 'friendsoffriends', 'justuuids', 'checkresults', 'epoch',
                                 'diff', 'diffl', 'diffr', 'sortstar', 'sortbystar', 'starsort',
                                 'nofileoutput', 'fileoutput', 'updateuuids', 'minusresults', 'trivial',
                                 'matchingignsuuids', 'includemultiplayerfiles',
                                 'keepfirstdictmultifiles', 'notallfromresults',
                                 'addadditionalfriends', 'noadditionalfriends']
                              + [x.lower() for x in extra_keywords] )
        # These keywords are possible options the user can specify for using the program. All of these are
        # 'non-positional'; i.e., it doesn't matter where they appear in the user's command line argument list.
        # For 'positional' arguments, there are fewer (e.g., '-' and 'fromresults'). They don't appear in this
        # class, but are instead used directly in the logic for main.py.
    
    def get_args(self, remove_keywords: bool, remove_dates: bool) -> List[str]:
        args = self._ARGS
        if remove_keywords:
            args = Utils.list_subtract(args, self._ARG_KEYWORDS)
        if remove_dates:
            args = Utils.remove_date_strings(args)
        return args
    
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
        return any(x in self._ARGS for x in ['sortstar', 'sortbystar', 'starsort'])
    
    def epoch(self) -> bool:
        return 'epoch' in self._ARGS
    
    def just_uuids(self) -> bool:
        return 'justuuids' in self._ARGS
    
    def date_cutoff(self) -> Optional[str]:
        return Utils.get_date_string_if_exists(self._ARGS)
    
    def do_file_output(self) -> bool:
        if 'fileoutput' in self._ARGS:
            assert 'nofileoutput' not in self._ARGS
            return True
        elif 'nofileoutput' in self._ARGS:
            return False
        else:
            # User didn't explicitly specify, so decide based on the following:
            return not self.just_online_friends() or self.just_uuids()
    
    def update_uuids(self) -> bool:
        return 'updateuuids' in self._ARGS
    
    def minus_results(self) -> bool:
        """Return true if the user doesn't want to get f lists of uuids that already have their f list
        stored in the results folder."""
        return 'minusresults' in self._ARGS
    
    def get_trivial_dicts_in_results(self) -> bool:
        if 'trivial' in self._ARGS:
            assert (self.check_results() and not self.minus_results() and not self.update_uuids()
                    and not self.find_matching_igns_or_uuids_in_results())
            # The user should only be wanting to see how many total unique uuids are in results, if
            # the 'trivial' command has been entered with check_results.
            return True
        return False
    
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
        return 'addadditionalfriends' in self._ARGS
    
    def get_additional_friends(self) -> bool:
        return 'noadditionalfriends' not in self._ARGS