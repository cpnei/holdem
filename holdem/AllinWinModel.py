import pickle
import expected
import os
from treys import Evaluator
from treys import Card
import random


def expectedRank(value):
    rank = int(value / 5) + 1
    return rank


class ExpectedValue(object):
    def __init__(self, explore=0.1):
        # key of expected Dict is the combination of expected rank + treys rank
        # values of expected Dict are counter, reward times
        self.expectedActionDict = {}
        self.evaluator = Evaluator()
        self.explore = explore
        self.episode = 0
        self.episode_reward = 0
        self.fold_count = 0

    def update_action(self, action, table, hand, reward):
        # table, hand are cards on table and in hand
        # the reward is final reward win or loss
        key = self.expected_key(table, hand)
        if key in self.expectedActionDict:
            self.expectedActionDict[key][action]['counter'] += 1
            self.expectedActionDict[key][action]['reward'] += reward
            if reward > 0:
                self.expectedActionDict[key][action]['win'] += 1
            elif reward < 0:
                self.expectedActionDict[key][action]['loss'] += 1
        else:
            self.expectedActionDict[key] = {}
            for i in range(4):
                self.expectedActionDict[key][i] = {'counter': 0, 'reward': 0, 'win': 0, 'loss': 0}
            self.expectedActionDict[key][action]['counter'] = 1
            self.expectedActionDict[key][action]['reward'] = reward
            if reward > 0:
                self.expectedActionDict[key][action]['win'] = 1
            elif reward < 0:
                self.expectedActionDict[key][action]['loss'] = 1

    def take_action(self, table, hand):
        key = self.expected_key(table, hand)
        if random.random() >= self.explore and key in self.expectedActionDict.keys():
            # do exploit
            max_reward = None
            action_list = []
            for action, value in self.expectedActionDict[key].items():
                if max_reward is None:
                    action_list = [action]
                    if value['counter'] == 0:
                        max_reward = 0
                    else:
                        max_reward = float(value['reward']) / value['counter']
                else:
                    if value['counter'] == 0:
                        action_reward = 0
                    else:
                        action_reward = float(value['reward']) / value['counter']
                    if action_reward > max_reward:
                        action_list = [action]
                        max_reward = action_reward
                    elif action_reward == max_reward:
                        action_list.append(action)
            return random.choice(action_list)
        else:
            return random.choice([ActionTable.FOLD,
                                  ActionTable.CALL,
                                  ActionTable.RAISE,
                                  ActionTable.CHECK])

    def card_to_str(self, card_list=[]):
        return [Card.int_to_str(card) for card in card_list if card != -1]
        """
        cards = []
        for card in card_list:
            if card != -1:
                cards.append(Card.int_to_str(card))
        return cards
        """

    def convert_card(self, table, hand):
        for i in range(len(table)):
            table[i] = "{}{}".format(table[i][0], table[i][1].lower())
        for i in range(2):
            hand[i] = "{}{}".format(hand[i][0], hand[i][1].lower())
        return table, hand

    def expected_key(self, table, hand):
        table = self.card_to_str(table)
        hand = self.card_to_str(hand)

        table, hand = self.convert_card(table, hand)
        ontable = [Card.new(card) for card in table]
        inhand = [Card.new(card) for card in hand]
        try:
            treys_rank = self.evaluator.evaluate(ontable, inhand)
        except Exception:
            treys_rank = -1
        all_cards = table + hand
        allinwin_rank = expectedRank(expected.get_expected_value(all_cards))
        return '{}-{}'.format(allinwin_rank, treys_rank)

    def get_expected_value(self, table, hand):
        all_cards = table + hand
        expectedvalue = expected.get_expected_value(all_cards)
        return expectedRank(expectedvalue), expectedvalue


class ActionTable(object):
    CHECK = 0
    CALL = 1
    RAISE = 2
    FOLD = 3


def to_pickle(obj, path):
    # path = check_file_name_exists(path)
    with open(path, 'wb') as f:
        pickle.dump(obj, f)


def load_pickle(path):
    with open(path, 'rb') as f:
        return pickle.load(f)


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
