from typing import List, Optional

import Utils

class Args:
    def __init__(self, args: List[str], arg_keywords: List[str]):
        self._ARGS = [arg if arg.endswith('.txt') else arg.lower() for arg in args[1:]]
        self._ARG_KEYWORDS = [x.lower() for x in arg_keywords]
    
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
        return 'checkresults' in self._ARGS
    
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