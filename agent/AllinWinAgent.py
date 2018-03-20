from collections import namedtuple
from enum import Enum
from holdem import PLAYER_STATE, COMMUNITY_STATE, STATE, ACTION, action_table
from holdem.AllinWinModel import ExpectedValue
from holdem.AllinWinModel import to_pickle, load_pickle
import os
import random

class AllinWinAction():
    def __init__(self, ai_model_path=None):
        self._nothing = "test"
        self.reload_left = 2
        self.model = None
        self._ai_model_path = ai_model_path
        self.loadModel(self._ai_model_path)

        self.action_history = []
        self.init_stack = -1
        

    def init_round_info(self, stack):
        self.init_stack = stack

    def end_episode(self, final_stack):
        self.model.episode += 1
        self.model.episode_reward += final_stack
        self.saveModel(self._ai_model_path)

    def batchTrainModel(self):
        return

    def onlineTrainModel(self):
        return

    def loadModel(self, path=None):
        if path is not None and os.path.exists(path) is True:
            try:
                self.model = load_pickle(path)
            except Exception:
                self.model = ExpectedValue()
        else:
            self.model = ExpectedValue()
        return

    def saveModel(self, path=None):
        if path is None:
            path = check_file_name_exists('temp-model')
        to_pickle(self.model, path)
        return

    def update_model(self, final_stack, bigblind):
        reward = final_stack - self.init_stack
        for action, table, hand in self.action_history:
            if bigblind == 0:
                self.model.update_action(action, table, hand, reward)
            else:
                self.model.update_action(action, table, hand, float(reward) / bigblind)
        del self.action_history[:]

    def takeExptectedAction(self, state, playerid):
        action = self.model.take_action(state.community_card, state.player_states[playerid].hand)
        if action == 3:
            self.model.fold_count += 1
        table_length = sum(1 for x in state.community_card if x != -1)
        if table_length == 3 or table_length == 4:
            self.action_history.append((action, state.community_card, state.player_states[playerid].hand))
        return ACTION(action, state.community_state.bigblind)

    def takeAction(self, state, playerid):
        return ACTION(action_table.CALL, state.community_state.to_call)
        ''' (Predict/ Policy) Select Action under state'''
        if state.community_state.to_call > 0:
            if random.random() > 0.7 :
                return ACTION(action_table.FOLD, 0)
            else:
                return ACTION(action_table.CALL, state.community_state.to_call)
        else:
            if random.random() > 0.7:
                return ACTION(action_table.RAISE, 50)
            elif random.random() > 0.9:
                return ACTION(action_table.RAISE, state.player_states[playerid].stack)
            else:
                return ACTION(action_table.CHECK, 0)

    def takeRuleAction(self, table, hand, trainModel, state, blindid_info, playerid):
        if len(table) == 0:
            if state.community_state.current_player in blindid_info:
                # inblind, always call
                return ACTION(action_table.CALL, state.community_state.to_call)
            else:
                """
                Do rule based
                1) one pair, call
                2) has J, Q, K, A in hand, call
                3) if same suit, 50% call
                """
                if hand[0][0] == hand[1][0]:
                    return ACTION(action_table.CALL, state.community_state.to_call)
                elif hand[0][0] in 'JQKA' or hand[1][0] in 'JQKA':
                    return ACTION(action_table.CALL, state.community_state.to_call)
                elif hand[0][1] == hand[1][1]:
                    if random.random() > 0.5:
                        return ACTION(action_table.CALL, state.community_state.to_call)
                return ACTION(action_table.FOLD, 0)
        else:
            rank, value = trainModel.get_expected_value(table, hand)
            if len(table) == 5:
                other_rank, other_value = trainModel.get_expected_value(table[:3], table[3:])
                if other_rank > rank * 1.5:
                    if random.random() < 0.5:
                        return ACTION(action_table.FOLD, 0)
                    else:
                        return ACTION(action_table.CALL, state.community_state.to_call)
                else:
                    return ACTION(action_table.CALL, state.community_state.to_call)
            else:
                if rank > 18:
                    return ACTION(action_table.RAISE, state.player_states[playerid].stack)
                elif rank > 15:
                    if random.random() < 0.5:
                        bet = min(state.community_state.to_call * 2, state.player_states[playerid].stack)
                        return ACTION(action_table.RAISE, bet)
                    else:
                        return ACTION(action_table.RAISE, state.player_states[playerid].stack)
                elif rank > 10:
                    if random.random() < 0.8:
                        bet = min(state.community_state.to_call * 2, state.player_states[playerid].stack)
                        return ACTION(action_table.RAISE, bet)
                    else:
                        return ACTION(action_table.RAISE, state.player_states[playerid].stack)
                elif rank > 5:
                    if random.random() < 0.1:
                        return ACTION(action_table.RAISE, state.player_states[playerid].stack)
                    else:
                        return ACTION(action_table.CALL, state.community_state.to_call)
                elif rank > 2:
                    return ACTION(action_table.CALL, state.community_state.to_call)
                else:
                    if random.random() > 0.7:
                        return ACTION(action_table.CALL, state.community_state.to_call)
                    else:
                        return ACTION(action_table.FOLD, 0)

    def getReload(self, state, playerid):
        for player in state.player_state:
            if player.seat == playerid:
                my_stack = player.stack
        '''return `True` if reload is needed under state, otherwise `False`'''
        if self.reload_left > 0 and my_stack < state.community_state.bigblind:
            self.reload_left -= 1
            return True
        else:
            return False

def check_file_name_exists(path):
    path = os.path.abspath(path)
    index = 0
    origin_output_file = path
    while os.path.exists(path):
        # add index number to filename if filename exist
        basename = os.path.basename(origin_output_file)
        ext_name = ''
        if '.' in basename:
            sp_name = basename.split('.')
            ext_name = '.{}'.format(sp_name[-1])
            basename = basename[0:len(basename) - len(ext_name)]
        index += 1
        path = os.path.join(os.path.dirname(path),
                            '{0}_{1:02}{2}'.format(basename, index, ext_name))
    return path
