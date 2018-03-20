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
import logging

DISCOUNT = 0.9
STEP_SIZE = 0.5
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
        self.Q = np.zeros(4*11*11*12*10*10*3).reshape(4,11,11,12,10,10,3)
        self.Q_hit = np.copy(self.Q)
        self.Q_err = np.copy(self.Q)
        self.logger = logging.getLogger('TexasHoldemEnv')
        
    def reset_state(self):
        self.hand_odds = 0.0
        self.ppot = 0.0 
        self.npot = 0.0
        self.lastboard = ""
        self.round = 0
        self.n_opponent = 0
        self.call_risk = 0.0
        self._roundRaiseCount = 0
        self.stack = 0
        self.call_level = 0
        self.lastaction = ACTION(action_table.NA, 0)

    def batchTrainModel(self):
        return

    def onlineTrainModel(self):
        return

    def saveModel(self, path):
        np.save(path, self.Q)
        np.save(path+".hit", self.Q_hit)
        np.save(path+".err", self.Q_err)
        return

    def loadModel(self, path):
        self.Q = np.load(path)
        return
        
    def state2index(self):
        risk = int(self.call_risk*10)
        if risk >= 10:
            risk = 9
        return self.round, int(self.hand_odds*10), int(self.ppot*10), self.call_level, self.n_opponent, risk
        
    def getActionValues(self):
        i = self.state2index()
        return self.Q[i[0], i[1], i[2], i[3], i[4], i[5], :]
        
    def calcHandOdds(self, pocket, board):
        playerWins = Array[Double]([1.0]*9)
        opponentWins = Array[Double]([0.0]*9)
        Hand.HandPlayerOpponentOdds(pocket, board, playerWins, opponentWins)
        return float(sum(playerWins))
    
    def readState(self, state, playerid):
        self.call_risk = float(state.community_state.to_call)/(state.community_state.totalpot+state.community_state.to_call)
        #assert self.call_risk <= 0.5
        pocket = card_list_to_str(state.player_states[playerid].hand)
        board = card_list_to_str(state.community_card)
        self.stack = state.player_states[playerid].stack
        self.call_level = float(state.community_state.to_call)/20
        if self.call_level < 1:
            self.call_level = 0
        else:
            self.call_level = int(np.log2(self.call_level))
        
        #self.logger.info("debug:", board, ",", self.lastboard)
        if state.community_state.round != self.round:
            self.round = state.community_state.round
            self.hand_odds = self.calcHandOdds(pocket, board)
            if self.round < 3 and self.round > 0:
                (r, self.ppot, self.npot) = Hand.HandPotential(pocket, board, Double(0), Double(0))
            else:
                (self.ppot, self.npot) = (0.0, 0.0)
            self.lastboard = board
            self._roundRaiseCount = 0
        
        self.n_opponent = 0
        for p in state.player_states:
            if p.playing_hand:
                self.n_opponent += 1
        if state.player_states[playerid].playing_hand:
            # self is not opponent
            self.n_opponent -= 1
                
        available_actions = [action_table.CALL, action_table.RAISE, action_table.FOLD]
        if state.player_states[playerid].stack == 0 or self._roundRaiseCount == 4:
            available_actions.remove(action_table.RAISE)
        if state.community_state.to_call <= state.player_states[playerid].betting:
            available_actions.remove(action_table.FOLD)
        return available_actions
        
    def takeAction(self, state, playerid):
        ''' (Predict/ Policy) Select Action under state'''
        if self.lastaction.action != action_table.NA:
            I = self.state2index()
            R = state.player_states[playerid].stack-self.stack
            A = self.lastaction.action-1
            I += (A,)
            self.logger.info("sarsaModel: previous stack={}, previous call_level={}".format(self.stack, self.call_level))
            
        available_actions = self.readState(state, playerid)
        self.logger.info("sarsaModel: takeAction: round {}, available_actions={}".format(self.round, available_actions))
        q = self.getActionValues()
        max_a = 0
        max_q = -100000
        for a in available_actions:
            if q[a-1] > max_q:
                max_a = a
                max_q = q[a-1]
        assert len(available_actions) > 0
        self.logger.info("sarsaModel: max_a={}, max_q={}".format(max_a, max_q))
        # Q-learning (off policy TD control)
        if self.lastaction.action != action_table.NA:
            E = R+DISCOUNT*max_q-self.Q[I]
            self.logger.info("sarsaModel: reward {}, error {}".format(R, E))
            self.Q[I] = self.Q[I] + STEP_SIZE*E
            self.Q_hit[I] += 1
            self.Q_err[I] = 0.9*self.Q_err[I]+0.1*np.absolute(E)
        
        # behaviour is epsilon greedy
        action = max_a
        if np.random.random() < EPSILON:
            # exploration
            action = np.random.choice(available_actions)
            self.logger.info("sarsaModel: explore action={}".format(action))
            
        amount = 0.0
        if action == action_table.RAISE:
            self._roundRaiseCount += 1
            amount = state.community_state.to_call
        elif action == action_table.CALL and state.community_state.to_call <= state.player_states[playerid].betting:
            action = action_table.CHECK
        self.lastaction = ACTION(action, amount)
        return self.lastaction
        
    def estimateReward(self, current_stack):
        I = self.state2index()
        R = current_stack-self.stack
        A = self.lastaction.action-1
        I += (A,)
        E = R+0-self.Q[I]
        self.logger.info("sarsaModel: reward {}, lastaction {}, error {}".format(R, self.lastaction.action, E))
        # Action values of terminal state are always zeros
        self.Q[I] = self.Q[I] + STEP_SIZE*(E)

    def getReload(self, state):
        '''return `True` if reload is needed under state, otherwise `False`'''
        if self.reload_left > 0:
            self.reload_left -= 1
            return True
        else:
            return False