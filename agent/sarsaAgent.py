import clr
clr.AddReference("HandEvaluator")
from HoldemHand import Hand
from System import Array, Double, String, Int64
import time
from collections import namedtuple
from enum import Enum
from holdem import PLAYER_STATE, COMMUNITY_STATE, STATE, ACTION, action_table, card_to_normal_str
import random
import numpy as np

DISCOUNT = 0.9
STEP_SIZE = 0.9
EPSILON = 0.1

def card_list_to_str(cards):
    s = ""
    for c in cards:
        if c == -1:
            break
        s += (card_to_normal_str(c) + " ")
    return s.strip()
    
class sarsaModel():
    def __init__(self):
        self._nothing = "test"
        self.reload_left = 2
        self.model = {"seed":831}
        self.reset_state()
        self.Q = np.zeros(4*10*9*10*3).reshape(4,10,9,10,3)
        
    def reset_state(self):
        self.hand_odds = 0.0
        self.lastboard = ""
        self.round = 0
        self.n_players = 0
        self.call_risk = 0.0
        self._roundRaiseCount = 0
        self.stack = 0
        self.lastaction = ACTION(action_table.NA, 0)

    def batchTrainModel(self):
        return

    def onlineTrainModel(self):
        return

    def saveModel(self, path):
        numpy.save("sarsa.npy", self.Q)
        return

    def loadModel(self, path):
        return
        
    def state2index(self):
        return self.round, int(self.hand_odds*10), self.n_players, int(self.call_risk*10)
        
    def getActionValues(self):
        i = self.state2index()
        return self.Q[i[0], i[1], i[2], i[3], :]
        
    def calcHandOdds(self, pocket, board):
        playerWins = Array[Double]([1.0]*9)
        opponentWins = Array[Double]([0.0]*9)
        Hand.HandPlayerOpponentOdds(pocket, board, playerWins, opponentWins)
        return float(sum(playerWins))
    
    def readState(self, state, playerid):
        self.call_risk = float(state.community_state.to_call)/state.community_state.totalpot
        pocket = card_list_to_str(state.player_states[playerid].hand)
        board = card_list_to_str(state.community_card)
        self.stack = state.player_states[playerid].stack
        
        #print("debug:", board, ",", self.lastboard)
        if board != self.lastboard:
            self.hand_odds = self.calcHandOdds(pocket, board)
            self.lastboard = board
            self.round += 1
            self._roundRaiseCount = 0
        
        self.n_players = 0
        for p in state.player_states:
            if p.playing_hand:
                self.n_players += 1
                
        available_actions = [action_table.CALL, action_table.RAISE, action_table.FOLD]
        if state.player_states[playerid].stack == 0 or self._roundRaiseCount == 4:
            available_actions.remove(action_table.RAISE)
        return available_actions
        
    def takeAction(self, state, playerid):
        print("takeAction: at round", self.round)
        ''' (Predict/ Policy) Select Action under state'''
        if self.lastaction.action != action_table.NA:
            I = self.state2index()
            R = state.player_states[playerid].stack-self.stack
            A = self.lastaction.action-1
            
        available_actions = self.readState(state, playerid)
        q = self.getActionValues()
        max_a = 0
        max_q = -100000
        for a in available_actions:
            if q[a-1] > max_q:
                max_a = a
                max_q = q[a-1]
        # Q-learning (off policy TD control)
        if self.lastaction.action != action_table.NA:
            self.Q[I[0], I[1], I[2], I[3], A] = self.Q[I[0], I[1], I[2], I[3], A] + STEP_SIZE*(R+DISCOUNT*max_q-self.Q[I[0], I[1], I[2], I[3], A])
        
        # behaviour is epsilon greedy
        action = max_a
        if np.random.random() < EPSILON:
            # exploration
            action = np.random.choice(available_actions)
            
        amount = 0.0
        if action == action_table.RAISE:
            self._roundRaiseCount += 1
            amount = state.community_state.to_call
        elif action == action_table.CALL and state.community_state.to_call <= 0:
            action = action_table.CHECK
        self.lastaction = ACTION(action, amount)
        return self.lastaction
        
    def estimateReward(self, current_stack):
        I = self.state2index()
        R = current_stack-self.stack
        A = self.lastaction.action-1
        # Action values of terminal state are always zeros
        self.Q[I[0], I[1], I[2], I[3], A] = self.Q[I[0], I[1], I[2], I[3], A] + STEP_SIZE*(R+0-self.Q[I[0], I[1], I[2], I[3], A])

    def getReload(self, state):
        '''return `True` if reload is needed under state, otherwise `False`'''
        if self.reload_left > 0:
            self.reload_left -= 1
            return True
        else:
            return False