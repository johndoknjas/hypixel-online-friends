from __future__ import annotations
import copy
import re

from . import Utils
from . import Files

class Args:
    def __init__(self, args: list[str]):
        assert re.split(r'/|\\', args[0])[-1] in ('main.py', 'hypickle')
        args = [arg if arg.endswith('.txt') else arg.lower() for arg in args[1:]]
        self._ARGS = Files.apply_aliases(args)
        self._ARG_KEYWORDS = ('all', 'friendsoffriends', 'justuuids', 'checkresults',
                              'diff', 'starsort', 'pitsort',
                              'fileoutput', 'updateuuids', 'matchingignsuuids',
                              'includemultiplayerfiles', 'keepfirstdictmultifiles',
                              'addadditionalfriends', 'addadditionals', 'addfriends',
                              'noadditionalfriends', 'noadditionals',
                              'addaliases', 'updatealiases', 'adduuidaliases', 'updateuuidaliases',
                              'showaliases', 'printaliases',
                              'getplayerjson', 'playerjson', 'noverify', 'dontverify', 'nover',
                              'pitpercent', 'pit%', 'pitplot', 'nwplot', 'bwplot', 'contains',
                              'trackargs', 'argsonline', 'newest', 'oldest',
                              'debugapi', 'showjsondiff', 'showjsonupdates',
                              'norecentgame', 'norecentgames', 'list', 'copyable')
        # These keywords are possible options the user can specify for using the program. All of these are
        # 'non-positional'; i.e., it doesn't matter where they appear in the user's command line argument list.
        # For 'positional' arguments, there are fewer (e.g., '-', 'friendedwhen', 'intersect').
        # They don't appear in this class, but are instead used directly in the logic for main.py.
        Utils.print_list(self.get_args(False), prepended_msg="self._ARGS list after applying aliases: ")
        self._validation_checks()

    def get_args(self, remove_keywords_and_dates: bool) -> list[str]:
        args = copy.copy(self._ARGS)
        if remove_keywords_and_dates:
            args = Utils.remove_date_strings(Utils.list_subtract(args, self._ARG_KEYWORDS))
        return args

    def get_keywords(self) -> list[str]:
        return list(self._ARG_KEYWORDS)

    def find_friends_of_friends(self) -> bool:
        return 'friendsoffriends' in self._ARGS

    def just_online_friends(self) -> bool:
        return 'all' not in self._ARGS and not self.find_friends_of_friends()

    def check_results(self) -> bool:
        return 'checkresults' in self._ARGS

    def diff_f_lists(self) -> bool:
        return 'diff' in self._ARGS

    def sort_by_star(self) -> bool:
        return 'starsort' in self._ARGS

    def sort_by_pit_rank(self) -> bool:
        return 'pitsort' in self._ARGS

    def just_uuids(self) -> bool:
        return 'justuuids' in self._ARGS

    def date_cutoff(self) -> str | None:
        return Utils.get_date_string_if_exists(self._ARGS)

    def do_file_output(self) -> bool:
        return 'fileoutput' in self._ARGS

    def update_uuids(self) -> bool:
        return 'updateuuids' in self._ARGS

    def find_matching_igns_or_uuids_in_results(self) -> bool:
        return 'matchingignsuuids' in self._ARGS

    def include_multi_player_files(self) -> bool:
        return 'includemultiplayerfiles' in self._ARGS

    def skip_first_dict_in_multi_player_files(self) -> bool:
        assert self.include_multi_player_files()
        # Only makes sense to call this function if the above is true.
        return 'keepfirstdictmultifiles' not in self._ARGS

    def add_additional_friends(self) -> bool:
        return any(x in self._ARGS for x in ('addadditionalfriends', 'addadditionals', 'addfriends'))

    def get_additional_friends(self) -> bool:
        return all(x not in self._ARGS for x in ('noadditionalfriends', 'noadditionals'))

    def update_aliases(self) -> bool:
        return 'addaliases' in self._ARGS or 'updatealiases' in self._ARGS

    def add_uuid_aliases(self) -> bool:
        return 'adduuidaliases' in self._ARGS or 'updateuuidaliases' in self._ARGS

    def print_aliases(self) -> bool:
        return 'printaliases' in self._ARGS or 'showaliases' in self._ARGS

    def get_player_json(self) -> bool:
        return 'getplayerjson' in self._ARGS or 'playerjson' in self._ARGS

    def verify_requests(self) -> bool:
        return all(x not in self._ARGS for x in ('noverify', 'dontverify', 'nover'))

    def pit_percent(self) -> bool:
        return 'pitpercent' in self._ARGS or 'pit%' in self._ARGS

    def pit_plot(self) -> bool:
        return 'pitplot' in self._ARGS

    def network_plot(self) -> bool:
        return 'nwplot' in self._ARGS

    def bedwars_plot(self) -> bool:
        return 'bwplot' in self._ARGS

    def contains_substr(self) -> bool:
        return 'contains' in self._ARGS

    def track_if_arg_players_online(self) -> bool:
        return 'trackargs' in self._ARGS or 'argsonline' in self._ARGS

    def get_newest_friends(self) -> bool:
        return 'newest' in self._ARGS

    def get_oldest_friends(self) -> bool:
        return 'oldest' in self._ARGS

    def debug_api(self) -> bool:
        return 'debugapi' in self._ARGS

    def show_json_updates(self) -> bool:
        """Returns whether to show what parts of the player json have updated, for players whose online
           status isn't shown."""
        return 'showjsondiff' in self._ARGS or 'showjsonupdates' in self._ARGS

    def output_recent_game(self) -> bool:
        return all(x not in self._ARGS for x in ('norecentgame', 'norecentgames')) and not self.just_uuids()

    def comma_sep_list(self) -> bool:
        """Returns whether to print the uuids of each player's friends in comma-separated lists, followed
           by the igns after that."""
        return 'list' in self._ARGS or 'copyable' in self._ARGS

    def do_mini_program(self) -> bool:
        mini_programs = (self.update_aliases(), self.add_uuid_aliases(), self.print_aliases(),
                         self.contains_substr(), self.add_additional_friends(), self.get_player_json(),
                         self.pit_percent(), self.pit_plot(), self.network_plot(), self.bedwars_plot(),
                         self.comma_sep_list())
        assert (bool_sum := sum(1 for x in mini_programs if x)) <= 1
        return bool_sum == 1

    def _validation_checks(self) -> None:
        assert all(arg.endswith('.txt') or arg.lower() == arg
                   for arg in self.get_args(False))
        assert set(self.get_keywords()).isdisjoint(Files.get_aliases().keys())
        if self.do_file_output():
            assert self.date_cutoff() is None and not self.just_online_friends()
            assert not self.get_newest_friends() and not self.get_oldest_friends()
        assert not (self.sort_by_pit_rank() and self.sort_by_star())
        if any((self.update_aliases(), self.print_aliases(), self.pit_plot(), self.network_plot(),
                self.bedwars_plot())):
            assert not self.get_args(True) and len(self.get_args(False)) == 1
        if self.add_additional_friends():
            assert len(self.get_args(True)) == 1 and len(self.get_args(False)) == 2
        if any((self.get_player_json(), self.pit_percent(), self.add_uuid_aliases(),
                self.comma_sep_list(), self.contains_substr())):
            assert len(self.get_args(True)) >= 1 and len(self.get_args(False)) >= 2
        assert not (self.get_newest_friends() and self.get_oldest_friends())