# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Aleksander Beloi (beloi.alex@gmail.com)
# Copyright (c) 2018 Sam Wenke (samwenke@gmail.com)
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import logging
from gym import Env, error, spaces, utils
from gym.utils import seeding

from treys import Card, Deck, Evaluator

from .player import Player
from .utils import hand_to_str, format_action, PLAYER_STATE, COMMUNITY_STATE, STATE

class TexasHoldemEnv(Env, utils.EzPickle):
    BLIND_INCREMENTS = [[10,20], [20,40], [40,80], [80,160], [160,320], [320,640], [640,1280], [1280, 2560], [2560, 5120], [5120, 10240]]

    def __init__(self, n_seats, max_limit=20000, debug=False):
        n_suits = 4                     # s,h,d,c
        n_ranks = 13                    # 2,3,4,5,6,7,8,9,T,J,Q,K,A
        n_community_cards = 5           # flop, turn, river
        n_pocket_cards = 2
        n_stud = 5

        self.n_seats = n_seats
        self._deck = Deck()
        self._evaluator = Evaluator()
        self._debug = debug

        self.init()
        
        # fill seats with dummy players
        self._seats = [Player(i, stack=0, emptyplayer=True) for i in range(n_seats)]
        self.emptyseats = n_seats
        self._player_dict = {}

        self.observation_space = spaces.Tuple([
            spaces.Tuple([                # # **players info**
                             spaces.MultiDiscrete([
                                 1,                   #  (boolean) is_emptyplayer
                                 n_seats - 1,         #  (numbers) number of seat
                                 max_limit,           #  (numbers) stack
                                 1,                   #  (boolean) is_playing_hand
                                 max_limit,           #  (numbers) handrank, need_error_msg?  (0 could be no rank, no error_msg needed
                                 1,                   #  (boolean) is_playedthisround
                                 max_limit,           #  (numbers) is_betting
                                 1,                   #  (boolean) isallin
                                 max_limit,           #  (numbers) last side pot
                             ]),
                             spaces.Tuple([
                                              spaces.MultiDiscrete([    # # **players hand**
                                                  1,                # (boolean) is_avalible
                                                  n_suits,          #  (catagory) suit,
                                                  n_ranks,          #  (catagory) rank.
                                              ])
                                          ] * n_pocket_cards)
                         ] * n_seats),
            spaces.Tuple([
                             spaces.Discrete(n_seats - 1), # big blind location
                             spaces.Discrete(max_limit),   # small blind
                             spaces.Discrete(max_limit),   # big blind
                             spaces.Discrete(max_limit*n_seats),   # pot amount
                             spaces.Discrete(max_limit),   # last raise
                             spaces.Discrete(max_limit),   # minimum amount to raise
                             spaces.Discrete(max_limit),   # how much needed to call by current player.
                             spaces.Discrete(n_seats - 1), # current player seat location.
                             spaces.MultiDiscrete([        # community cards
                                 1,                # (boolean) is_avalible
                                 n_suits,          # (catagory) suit
                                 n_ranks,          # (catagory) rank
                                 1,                # (boolean) is_flopped
                             ]),
                         ] * n_stud),
        ])

        self.action_space = spaces.Tuple([
                                             spaces.MultiDiscrete([
                                                 3,                     # action_id
                                                 max_limit,             # raise_amount
                                             ]),
                                         ] * n_seats)
        
        
        self.logger = logging.getLogger('TexasHoldemEnv')
        #self.logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        # create formatter
        formatter = logging.Formatter('%(asctime)s: %(message)s')
        # add formatter to ch
        ch.setFormatter(formatter)
        # add ch to logger
        self.logger.addHandler(ch)
        
    def init(self):
        self._cycle = 0
        self._blind_index = 0
        [self._smallblind, self._bigblind] = TexasHoldemEnv.BLIND_INCREMENTS[0]

        self.community = []
        self._round = 0
        self._button = 0
        self._discard = []

        self._side_pots = [0] * self.n_seats
        self._current_sidepot = 0 # index of _side_pots
        self._totalpot = 0
        self._tocall = 0
        self._lastraise = 0

        
        self._current_player = None
        self._last_player = None
        self._last_actions = None
        
        self.episode_end = False
        self.winning_players = []
        self.round_holder = -1

    def add_player(self, seat_id, stack=1000):
        """Add a player to the environment seat with the given stack (chipcount)"""
        player_id = seat_id
        if player_id not in self._player_dict:
            new_player = Player(player_id, stack=stack, emptyplayer=False)
            if self._seats[player_id].emptyplayer:
                self._seats[player_id] = new_player
                new_player.set_seat(player_id)
            else:
                raise error.Error('Seat already taken.')
            self._player_dict[player_id] = new_player
            self.emptyseats -= 1

    def remove_player(self, seat_id):
        """Remove a player from the environment seat."""
        player_id = seat_id
        try:
            idx = self._seats.index(self._player_dict[player_id])
            self._seats[idx] = Player(0, stack=0, emptyplayer=True)
            del self._player_dict[player_id]
            self.emptyseats += 1
        except ValueError:
            pass

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]
        
    def reset(self):
        self.init()
        for player in self._seats:
            player.reset_stack()
            player.sitting_out = True

    def new_cycle(self):
        self._reset_game()
        self._ready_players()
        self._cycle += 1
        if self._cycle %  self.n_seats == 0:
            self._increment_blinds()

        [self._smallblind, self._bigblind] = TexasHoldemEnv.BLIND_INCREMENTS[self._blind_index]

        alive_player = sum([1 if p.stack > 0 else 0 for p in self._seats])
        if ((self.emptyseats < len(self._seats) - 1) and (alive_player > len(self._seats) // 2)):
            players = [p for p in self._seats if p.playing_hand]
            self.logger.info("new_cycle: jump to next round")
            self._new_round()
            self._round = 0
            self._tocall = 0
            self._current_player = self._first_to_act(players)
            self._post_smallblind(self._current_player)
            self._current_player = self._next(players, self._current_player)
            self._post_bigblind(self._current_player)
            self._current_player = self._next(players, self._current_player)
            self._round = 0
            self._deal_next_round()
            self._folded_players = []
        else:
            self.episode_end = True
        return self._get_current_reset_returns()

    def step(self, actions):
        """ Run one timestep of the game (t -> t+1)
            @param: actions the list of actions that player selected.
            ACTIONS_ENUM {
              CHECK = 0,
              CALL = 1,
              RAISE = 2,
              FOLD = 3
            }
            RAISE_AMT = [0, minraise]
           """
        if len(actions) != len(self._seats):
            raise error.Error('actions must be same shape as number of seats.')

        if self._current_player is None:
            raise error.Error('Round cannot be played without 2 or more players.')

        if self._round == 4:
            raise error.Error('Rounds already finished, needs to go new_cycle.')

        players = [p for p in self._seats if p.playing_hand]
        if len(players) == 1:
            # raise error.Error('Round cannot be played with one player.')
            terminal = True
            self._resolve_round(players)
            return self._get_current_step_returns(terminal)


        self._last_player = self._current_player
        self._last_actions = actions

        #if self._current_player.isallin:
        #    self._current_player = self._next(players, self._current_player)
        #    return self._get_current_step_returns(False)

        move = self._current_player.player_move(
            self._output_state(self._current_player), actions[self._current_player.player_id])

        bet_increment = 0
        folded_player = None
        if move[0] == 'call':
            bet_increment = self._player_bet(self._current_player, self._tocall)
            if self._debug:
                print('[DEBUG] Player', self._current_player.player_id, move)
        elif move[0] == 'check':
            bet_increment = self._player_bet(self._current_player, self._tocall)
            if self._debug:
                print('[DEBUG] Player', self._current_player.player_id, move)
            if self.round_holder == -1:
                self.round_holder = self._current_player.player_id
        elif move[0] == 'raise':
            bet_increment = self._player_bet(self._current_player, move[1]+self._tocall)
            if self._debug:
                print('[DEBUG] Player', self._current_player.player_id, move)
            self.round_holder = self._current_player.player_id
        elif move[0] == 'fold':
            self._current_player.playing_hand = False
            folded_player = self._current_player
            if self._debug:
                print('[DEBUG] Player', self._current_player.player_id, move)

        self._current_player = self._next(players, self._current_player)
        if folded_player:
            players.remove(folded_player)
            self._folded_players.append(folded_player)
        # break if a single player left
        if len(players) == 1:
            self.logger.info("1 player left. Jump to next round.")
            self._resolve(players)
        if self._current_player.player_id == self.round_holder:
            self.logger.info("All played. Jump to next round. current_player = {}".format(self._current_player.player_id))
            self._resolve(players)
        #if len([p for p in players if not p.isallin]) == 0:
        #    self.logger.info("Everyone is all in. Jump to next round.")
        #    self._resolve(players)

        terminal = False
        if self._round == 4:
            terminal = True
            self._resolve_round(players)
        return self._get_current_step_returns(terminal)

    def render(self, mode='machine', close=False):
        self.logger.info('Cycle {}, Round {}, total pot: {}, tocall: {}, holder: {}, next: {} >>>'.format(self._cycle, self._round, self._totalpot, self._tocall, self.round_holder, self._current_player.player_id))
        if not self._last_actions is None:
            pid = self._last_player.player_id
            self.logger.info('last action by player {}:'.format(pid) + '\t' + format_action(self._last_player, self._last_actions[pid]))

        state = self._get_current_state()

        #(player_infos, player_hands) = zip(*state.player_state)

        self.logger.info('community:')
        self.logger.info('-' + hand_to_str(state.community_card, mode))
        self.logger.info('players:')
        for idx, playerstate in enumerate(state.player_states):
            self.logger.info('{}{}stack:{}, bet:{}, playing:{}, isallin:{}'.format(idx, hand_to_str(playerstate.hand, mode), self._seats[idx].stack, self._seats[idx].currentbet, self._seats[idx].playing_hand, self._seats[idx].isallin))
        self.logger.info("<<<")

    def _resolve(self, players):
        self._current_player = self._first_to_act(players)
        #self._resolve_sidepots(players + self._folded_players)
        self._new_round()
        self._deal_next_round()
        if self._debug:
            print('[DEBUG] totalpot', self._totalpot)

    def _deal_next_round(self):
        if self._round == 0:
            self._deal()
        elif self._round == 1:
            self._flop()
        elif self._round == 2:
            self._turn()
        elif self._round == 3:
            self._river()

    def _increment_blinds(self):
        self._blind_index = min(self._blind_index + 1, len(TexasHoldemEnv.BLIND_INCREMENTS) - 1)
        [self._smallblind, self._bigblind] = TexasHoldemEnv.BLIND_INCREMENTS[self._blind_index]

    def _post_smallblind(self, player):
        ''' choosed player to act small blind '''
        if self._debug:
            print('[DEBUG] player ', player.player_id, 'small blind', self._smallblind)
        bet_increment = self._player_bet(player, self._smallblind)
        self.round_holder = player.player_id

    def _post_bigblind(self, player):
        ''' choosed player to act big blind '''
        if self._debug:
            print('[DEBUG] player ', player.player_id, 'big blind', self._bigblind)
        bet_increment = self._player_bet(player, self._bigblind)
        if bet_increment > 0:
            self.round_holder = player.player_id
        self._lastraise = bet_increment

    def _player_bet(self, player, player_bet):
        # print("[DEBUG]", player.player_id, player_bet)
        total_bet = min(player.stack+player.currentbet, player_bet)
        self._roundpot = max(self._roundpot, total_bet)

        # print("Lift is trnge -------- {}, {}, {}".format(player_bet, player.currentbet, player.stack))
        bet_increment = (total_bet - player.currentbet)
        self._totalpot += bet_increment
        # print("{}, {}".format(total_bet, total_bet - player.currentbet))
        player.bet(total_bet) # update acumulative bet (not add another bet)

        self._tocall = max(self._tocall, total_bet)
        #if self._tocall > 0:
        #    self._tocall = max(self._tocall, self._bigblind)
        self._lastraise = max(self._lastraise, total_bet  - self._lastraise)
        return bet_increment

    def _first_to_act(self, players):
        if self._round == 0 and len(players) == 2:
            return self._next(sorted(
                players + [self._seats[self._button]], key=lambda x:x.get_seat()),
                self._seats[self._button])
        try:
            first = [player for player in players if player.get_seat() > self._button][0]
        except IndexError:
            first = players[0]
        return first

    def _next(self, players, current_player):
        ''' get next player '''
        idx = players.index(current_player)
        return players[(idx+1) % len(players)]

    def _deal(self):
        for player in self._seats:
            if player.playing_hand:
                player.hand = self._deck.draw(2)

    def _flop(self):
        self._discard.append(self._deck.draw(1)) #burn
        self.community = self._deck.draw(3)

    def _turn(self):
        self._discard.append(self._deck.draw(1)) #burn
        self.community.append(self._deck.draw(1))

    def _river(self):
        self._discard.append(self._deck.draw(1)) #burn
        self.community.append(self._deck.draw(1))

    def _ready_players(self):
        for p in self._seats:
            if not p.emptyplayer and p.sitting_out:
                p.sitting_out = False
                p.playing_hand = True

    def _resolve_sidepots(self, players_playing):
        players = [p for p in players_playing if p.currentbet]
        if self._debug:
            print('[DEBUG] current bets: ', [p.currentbet for p in players])
            print('[DEBUG] playing hand: ', [p.playing_hand for p in players])
        if not players:
            return
        try:
            smallest_bet = min([p.currentbet for p in players if p.playing_hand])
        except ValueError:
            for p in players:
                self._side_pots[self._current_sidepot] += p.currentbet
                p.currentbet = 0
            return

        smallest_players_allin = [p for p, bet in zip(players, [p.currentbet for p in players]) if bet == smallest_bet and p.isallin]

        for p in players:
            self._side_pots[self._current_sidepot] += min(smallest_bet, p.currentbet)
            p.currentbet -= min(smallest_bet, p.currentbet)
            p.lastsidepot = self._current_sidepot

        if smallest_players_allin:
            self._current_sidepot += 1
            self._resolve_sidepots(players)
        if self._debug:
            print('[DEBUG] sidepots: ', self._side_pots)

    def _new_round(self):
        for player in self._player_dict.values():
            #player.currentbet = 0
            player._roundRaiseCount = 0
            self.round_holder = -1
        self._round += 1
        #self._tocall = 0
        self._lastraise = 0
        self._roundpot = 0

    def _resolve_round(self, players):
        self._resolve_sidepots(players + self._folded_players)
        if len(players) == 1:
            players[0].refund(sum(self._side_pots))
            self._totalpot = 0
        else:
            # compute hand ranks
            for player in players:
                player.handrank = self._evaluator.evaluate(player.hand, self.community)

            # trim side_pots to only include the non-empty side pots
            temp_pots = [pot for pot in self._side_pots if pot > 0]

            # compute who wins each side pot and pay winners
            for pot_idx,_ in enumerate(temp_pots):
                # find players involved in given side_pot, compute the winner(s)
                pot_contributors = [p for p in players if p.lastsidepot >= pot_idx]
                if len(pot_contributors) == 0:
                    print("_resolve_round() error: pot_idx={}, temp_pots={}, lastsidepot={}, _side_pots={}, _current_sidepot={}".format(pot_idx, temp_pots, [p.lastsidepot for p in players], self._side_pots, self._current_sidepot))
                    print("stacks={}".format([p.stack for p in players]))
                else:
                    winning_rank = min([p.handrank for p in pot_contributors])
                    self.winning_players = [p for p in pot_contributors if p.handrank == winning_rank]

                    for player in self.winning_players:
                        split_amount = int(self._side_pots[pot_idx]/len(self.winning_players))
                        if self._debug:
                            print('[DEBUG] Player', player.player_id, 'wins side pot (', int(self._side_pots[pot_idx]/len(self.winning_players)), ')')
                        player.refund(split_amount)
                        self._side_pots[pot_idx] -= split_amount

                # any remaining chips after splitting go to the winner in the earliest position
                if self._side_pots[pot_idx]:
                    earliest = self._first_to_act([player for player in self.winning_players])
                    earliest.refund(self._side_pots[pot_idx])

    def _reset_game(self):
        playing = 0
        for player in self._seats:
            if not player.emptyplayer and not player.sitting_out:
                player.reset_hand()
                playing += 1
        self.community = []
        self._current_sidepot = 0
        self._totalpot = 0
        self._side_pots = [0] * len(self._seats)
        self._deck.shuffle()
        self.round_holder = -1

        if playing:
            self._button = (self._button + 1) % len(self._seats)
            while not self._seats[self._button].playing_hand:
                self._button = (self._button + 1) % len(self._seats)

    def _output_state(self, current_player):
        return {
            'players': [player.player_state() for player in self._seats],
            'community': self.community,
            'my_seat': current_player.get_seat(),
            'pocket_cards': current_player.hand,
            'pot': self._totalpot,
            'button': self._button,
            'tocall': (self._tocall - current_player.currentbet),
            'stack': current_player.stack,
            'bigblind': self._bigblind,
            'player_id': current_player.player_id,
            'lastraise': self._lastraise,
            'minraise': max(self._bigblind, self._tocall),
        }

    def _pad(self, l, n, v):
        if (not l) or (l is None):
            l = []
        return l + [v] * (n - len(l))


    def _get_current_state(self):
        player_states = []
        for player in self._seats:
            player_features = PLAYER_STATE(
                int(player.emptyplayer),
                int(player.get_seat()),
                int(player.stack),
                int(player.playing_hand),
                int(player.handrank),
                int(player.currentbet),
                int(player.isallin),
                int(player.lastsidepot),
                0,
                self._pad(player.hand, 2, -1)
            )
            player_states.append(player_features)

        community_states = COMMUNITY_STATE(
            int(self._round),
            int(self._button),
            int(self._smallblind),
            int(self._bigblind),
            int(self._totalpot),
            int(self._lastraise),
            int(self._roundpot),
            int(self._tocall),
            int(self._current_player.player_id)
        )
        return STATE(tuple(player_states), community_states, self._pad(self.community, 5, -1))

    def _get_current_reset_returns(self):
        return self._get_current_state()

    def _get_current_step_returns(self, terminal):
        obs = self._get_current_state()
        # TODO, make this something else?
        rew = [player.stack for player in self._seats]
        return obs, rew, terminal, [] # TODO, return some info?