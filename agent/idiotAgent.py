from collections import namedtuple
from enum import Enum
from holdem import PLAYER_STATE, COMMUNITY_STATE, STATE, ACTION, action_table
import random

class idiotModel():
    def __init__(self):
        self._nothing = "test"
        self.reload_left = 2
        self.model = {"seed":831}
        self.reset_state()
        
    def reset_state(self):
        self._roundRaiseCount = 0

    def batchTrainModel(self):
        return

    def onlineTrainModel(self):
        return

    def saveModel(self, path):
        return

    def loadModel(self, path):
        return

    def takeAction(self, state, playerid):
        ''' (Predict/ Policy) Select Action under state'''
        (action, amount) = (action_table.CHECK, 0)
        if state.community_state.to_call > state.player_states[playerid].betting:
            if random.random() > 0.7 :
                action = action_table.FOLD
            else:
                (action, amount) = (action_table.CALL, state.community_state.to_call)
        elif state.player_states[playerid].stack > 0 and self._roundRaiseCount < 4:
            if random.random() > 0.7:
                (action, amount) = (action_table.RAISE, state.community_state.to_call)
            elif random.random() > 0.9:
                (action, amount) = (action_table.RAISE, state.player_states[playerid].stack)
        if action == action_table.RAISE:
            self._roundRaiseCount += 1
        return ACTION(action, amount)

    def getReload(self, state):
        '''return `True` if reload is needed under state, otherwise `False`'''
        if self.reload_left > 0:
            self.reload_left -= 1
            return True
        else:
            return False