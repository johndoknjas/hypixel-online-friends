from typing import List, Optional

import Utils

class Args:
    def __init__(self, args: List[str], extra_keywords: List[str] = []):
        self._ARGS = [arg if arg.endswith('.txt') else arg.lower() for arg in args[1:]]
        self._ARG_KEYWORDS = (  ['All', 'FriendsOfFriends', 'JustUUIDs', 'CheckResults', 'epoch',
                                 'diff', 'diffl', 'diffr', 'SortStar', 'SortByStar', 'StarSort',
                                 'NoFileOutput', 'FileOutput', 'UpdateUUIDs', 'MinusResults', 'trivial',
                                 'MatchingIGNsUUIDs', 'IncludeMultiPlayerFiles',
                                 'IncludeMultiPlayerFilesWithFirstDict',
                                 'AddAdditionalFriends', 'NoAdditionalFriends', 'NotAllFromResults']
                              + extra_keywords)
        self._ARG_KEYWORDS = [x.lower() for x in self._ARG_KEYWORDS]
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
        return Utils.in_str_lst(self._ARGS, 'FriendsOfFriends')
    
    def just_online_friends(self) -> bool:
        return Utils.not_in_str_lst(self._ARGS, 'all') and not self.find_friends_of_friends()
    
    def check_results(self) -> bool:
        return Utils.in_str_lst(self._ARGS, 'CheckResults') or self.minus_results()
    
    def diff_left_to_right(self) -> bool:
        return Utils.any_in(self._ARGS, ['diff', 'diffr'])
    
    def diff_right_to_left(self) -> bool:
        return Utils.any_in(self._ARGS, ['diff', 'diffl'])
    
    def sort_by_star(self) -> bool:
        return Utils.any_in(self._ARGS, ['SortStar', 'SortByStar', 'StarSort'])
    
    def epoch(self) -> bool:
        return Utils.in_str_lst(self._ARGS, 'epoch')
    
    def just_uuids(self) -> bool:
        return Utils.in_str_lst(self._ARGS, 'JustUUIDs')
    
    def date_cutoff(self) -> Optional[str]:
        return Utils.get_date_string_if_exists(self._ARGS)
    
    def do_file_output(self) -> bool:
        if Utils.in_str_lst(self._ARGS, 'FileOutput'):
            assert Utils.not_in_str_lst(self._ARGS, 'NoFileOutput')
            return True
        elif Utils.in_str_lst(self._ARGS, 'NoFileOutput'):
            return False
        else:
            # User didn't explicitly specify, so decide based on the following:
            return not self.just_online_friends() or self.just_uuids()
    
    def update_uuids(self) -> bool:
        return Utils.in_str_lst(self._ARGS, 'UpdateUUIDs')
    
    def minus_results(self) -> bool:
        """Return true if the user doesn't want to get f lists of uuids that already have their f list
        stored in the results folder."""
        return Utils.in_str_lst(self._ARGS, 'MinusResults')
    
    def get_trivial_dicts_in_results(self) -> bool:
        if Utils.in_str_lst(self._ARGS, 'trivial'):
            assert (self.check_results() and not self.minus_results() and not self.update_uuids()
                    and not self.find_matching_igns_or_uuids_in_results())
            # The user should only be wanting to see how many total unique uuids are in results, if
            # the 'trivial' command has been entered with check_results.
            return True
        return False
    
    def find_matching_igns_or_uuids_in_results(self) -> bool:
        return Utils.in_str_lst(self._ARGS, 'MatchingIGNsUUIDs')
    
    def include_multi_player_files(self) -> bool:
        return Utils.any_in(self._ARGS, ['IncludeMultiPlayerFiles', 'IncludeMultiPlayerFilesWithFirstDict'])
    
    def skip_first_dict_in_multi_player_files(self) -> bool:
        assert self.include_multi_player_files()
        # Only makes sense to call this function if the above is true.
        return Utils.not_in_str_lst(self._ARGS, 'IncludeMultiPlayerFilesWithFirstDict')
    
    def from_results_for_all(self) -> bool:
        return Utils.not_in_str_lst(self._ARGS, 'NotAllFromResults')
    
    def add_additional_friends(self) -> bool:
        return Utils.in_str_lst(self._ARGS, 'AddAdditionalFriends')
    
    def get_additional_friends(self) -> bool:
        return Utils.not_in_str_lst(self._ARGS, 'NoAdditionalFriends')