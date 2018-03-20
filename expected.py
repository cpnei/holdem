CARD_NUMBER = '23456789TJQKA'
HIGHER_J = set(['J', 'Q', 'K', 'A'])

# card_list length should be 5 or 6


def get_expected_value(card_list=[]):
    prob_method = [(straight_flush, 128),
                   (four_of_a_kind, 128),
                   (full_house, 64),
                   (flush, 32),
                   (straight_t, 32),
                   (straight, 16),
                   (three_of_a_kind, 16),
                   (two_pairs_j, 16),
                   (two_pairs, 8),
                   (one_pair_j, 4),
                   (one_pair, 2)]
    expectedValue = 0.0
    for card_type, value in prob_method:
        expectedValue += card_type(card_list) * value
    return expectedValue


def straight_flush(card_list=[]):
    s_string = 'A23456789TJQKA'
    suit_dict = {}
    for card in card_list:
        if card[1] not in suit_dict:
            suit_dict[card[1]] = set([card[0]])
        else:
            suit_dict[card[1]].add(card[0])
    if len(suit_dict) == 4:
        return 0.0
    cards_to_deal = 7 - len(card_list)
    prob = 0.0
    for _, card_number_list in suit_dict.items():
        miss_one = False
        if len(card_number_list) + cards_to_deal < 5:
            continue
        for i in range(len(s_string) - 4):
            straight_set = set(list(s_string[i:i + 5]))
            miss_card = len(straight_set - card_number_list)
            if miss_card == 0:
                return 1.0
            if miss_card <= cards_to_deal:
                if cards_to_deal == 1:
                    # prob += 1 / 46.0
                    if miss_one is False:
                        prob += 0.021739130434782608
                else:
                    if miss_card == 2:
                        # get two card to target cards to become straight flush
                        # prob = (1 / 47) * (1 / 46) * 2
                        if miss_one is False:
                            prob += 0.0009250693802035153
                    else:
                        # miss_card == 1
                        # get one card to become straight and any other one card
                        # enter this block, all prob are considered
                        # prob += (1 / 47) + (46 / 47) * (1 / 46)
                        prob = 0.0425531914893617
                        miss_one = True
    return prob


def four_of_a_kind(card_list=[]):
    card_number_list = set([c[0] for c in card_list])
    if len(card_number_list) > 4:
        return 0.0
    number_dict = {}
    for n in card_number_list:
        number_dict[n] = 0
    cards_to_deal = 7 - len(card_list)

    for c in card_list:
        number_dict[c[0]] += 1
        if number_dict[c[0]] == 4:
            return 1.0

    prob = 0.0
    if cards_to_deal == 1:
        for _, n in number_dict.items():
            if n == 3:
                prob += 0.021739130434782608
    else:
        # cards_to_deal == 2:
        if len(card_number_list) == 4:
            # card type should be 2 1 1 1, need to get two same cards with the pair
            # prob = 2 / 47 * 1 / 46
            prob = 0.0009250693802035153
        elif len(card_number_list) == 2:
            # card type should be 3 2
            # need to get two same cards with the pair or one of the 3 same kind and any other one
            # prob = 2 / 47 * 1 / 46
            # prob += 1 / 47 * 2
            prob = 0.043478260869565216
        else:
            # card type could be 2 2 1 or 3 1 1
            for _, n in number_dict.items():
                if n == 2:
                    # card type be 2 2 1
                    # need to get 2 same card from the pairs
                    # prob = 4 / 47 * 1 / 46
                    prob = 0.0018509949097639982
                    break
                if n == 3:
                    # card type should be 3 1 1
                    # need to get one of the 3 same kind and any other one
                    # prob = 1 / 47 * 2
                    prob = 0.0425531914893617
                    break
    return prob


def full_house(card_list=[]):
    card_number_list = set([c[0] for c in card_list])
    if len(card_number_list) > 4:
        return 0.0
    number_dict = {}
    for n in card_number_list:
        number_dict[n] = 0
    cards_to_deal = 7 - len(card_list)
    count_dict = {1: 0, 2: 0, 3: 0, 4: 0}

    for c in card_list:
        number_dict[c[0]] += 1

    for _, n in number_dict.items():
        count_dict[n] += 1
    if count_dict[3] > 0:
        if count_dict[2] > 0 or count_dict[3] > 1:
            return 1.0
    if count_dict[4] == 1 and count_dict[2] == 1:
        return 1.0

    prob = 0.0
    if cards_to_deal == 1:
        if count_dict[4] == 1:
            # card type should be 4 1 1
            # need get one same with the single cards
            # prob = 6 / 46
            prob = 0.13043478260869565
        else:
            if count_dict[3] > 0:
                # card type should be 3 1 1 1
                # need get one more card same with the single cards
                # prob = 9 / 46
                prob = 0.1956521739130435
            elif count_dict[2] > 1:
                # card type could be 2 2 1 1 or 2 2 2
                # need get one card same with the pairs
                prob = 2 * count_dict[2] / 46.0
    else:
        # cards_to_deal == 2
        if count_dict[4] == 1:
            # card type should be 4 1
            # need get one same card with single and any other card or
            # get two same other cards
            # prob = 3 / 47 + 44 / 47 * 3 / 46
            # prob += 44 / 47 * 3 / 46
            prob = 0.18593894542090658
        else:
            if count_dict[3] > 0:
                # card type should be 3 1 1
                # need get one from the single and any other card or
                # get two same other cards
                # prob = 6 / 47 + 41 / 47 * 6 / 46
                # prob = 41 / 47 * 3 / 46
                prob = 0.29833487511563367
            elif count_dict[2] > 1:
                # card type should be 2 2 1
                # need get one same with the pairs and any one other or
                # get two same cards with the single
                # prob = 4 / 47 + 43 / 47 * 4 / 46
                # prob += 3 / 47 * 2 / 46
                prob = 0.16743755781683625
            else:
                # count_dict[2] == 1:
                # card type should be 2 1 1 1
                # need get one same with the pair and one from the single or
                # two same cards with the single
                # prob = 2 / 47 * 9 / 46 * 2
                # prob += 9 / 47 * 2 / 46
                prob = 0.02497687326549491
    return prob


def flush(card_list=[]):
    suit_list = set([c[1] for c in card_list])
    if len(suit_list) == 4:
        return 0.0
    suit_dict = {}
    for s in suit_list:
        suit_dict[s] = 0
    cards_to_deal = 7 - len(card_list)

    for c in card_list:
        suit_dict[c[1]] += 1
        if suit_dict[c[1]] > 4:
            return 1.0

    prob = 0.0
    if cards_to_deal == 1:
        # need to has 4 cards in a suit
        for _, n in suit_dict.items():
            if n == 4:
                # prob = 9 / 46
                prob = 0.1956521739130435
                break
    else:
        # cards_to_deal == 2
        # need the type with 3 1 1, 3 2, or 4 1
        # if has 3 of a suit, need get two more the same suit
        # if has 4 of a suit, need get one more the same suit and any other one
        # or equal 1 - porb to get two other suits
        for _, n in suit_dict.items():
            if n == 3:
                # prob = 10 / 47 * 9 / 46
                prob = 0.041628122109158186
                break
            elif n == 4:
                # prob = 1 - 38 / 47 * 37 / 46
                prob = 0.3496762257169288
                break
    return prob


def straight_t(card_list=[]):
    straight_set = set(['T', 'J', 'Q', 'K', 'A'])
    card_number_list = set([c[0] for c in card_list])
    cards_to_deal = 7 - len(card_list)
    miss_card = len(straight_set - card_number_list)
    if miss_card == 0:
        return 1.0
    if miss_card <= cards_to_deal:
        if cards_to_deal == 1:
            # prob += 4 / 46.0
            prob = 0.08695652173913043
        else:
            if miss_card == 2:
                # get two card to become straight
                # prob += (4 / 47) * (4 / 46) * 2
                prob = 0.014801110083256245
            else:
                # miss_card == 1
                # get one card to become straight and any other one card
                # prob += (4 / 47) + (43 / 47) * (4 / 46)
                prob = 0.16466234967622573
    else:
        prob = 0.0
    return prob


def straight(card_list=[]):
    s_string = 'A23456789TJQKA'
    card_number_list = set([c[0] for c in card_list])
    cards_to_deal = 7 - len(card_list)
    prob = 0.0
    miss_one = False
    for i in range(len(s_string) - 4):
        straight_set = set(list(s_string[i:i + 5]))
        miss_card = len(straight_set - card_number_list)
        if miss_card == 0:
            return 1.0
        if miss_card <= cards_to_deal:
            if cards_to_deal == 1:
                # prob += 4 / 46.0
                if miss_one is False:
                    prob += 0.08695652173913043
            else:
                if miss_card == 2:
                    # get two card to become straight
                    # prob += (4 / 47) * (4 / 46) * 2
                    if miss_one is False:
                        prob += 0.014801110083256245
                else:
                    # miss_card == 1
                    # get one card to become straight and any other one card
                    # enter this block, all prob are considered
                    # prob += (1 / 47) + (46 / 47) * (1 / 46)
                    prob = 0.16466234967622573
                    miss_one = True
    return prob


def three_of_a_kind(card_list=[]):
    card_number_list = set([c[0] for c in card_list])
    if len(card_number_list) == 6:
        return 0.0
    number_dict = {}
    for n in card_number_list:
        number_dict[n] = 0
    cards_to_deal = 7 - len(card_list)

    for c in card_list:
        number_dict[c[0]] += 1
        if number_dict[c[0]] == 3:
            return 1.0

    prob = 0.0
    if cards_to_deal == 1:
        # only need to consider with 2 types, 2 1 1 1 1 and 2 2 1 1
        if len(card_number_list) == 4:
            # get one same with the pairs
            # prob = 4 / 47
            prob = 0.0851063829787234
        else:
            # len(card_number_list) == 5
            # get one same with the pair
            # prob = 2 / 47
            prob = 0.0425531914893617
    else:
        # cards_to_deal == 2
        if len(card_number_list) == 5:
            # card type should be 1 1 1 1 1
            # need get two same card with any card in card_list
            # prob = 3 / 47 * 2 / 46 * 5
            prob = 0.013876040703052728
        elif len(card_number_list) == 4:
            # card type should be 2 1 1 1
            # get two same card with single card in card_list or one card same with pair and any other one
            # prob = 3 * (3 / 47 * 2 / 46)
            # prob += (2 / 47 + 45 / 47 * 2 / 46)
            prob = 0.09250693802035152
        else:
            # len(card_number_list) == 3
            # card type should be 2 2 1
            # get two cards same with the single card or
            # any one card same with the pairs
            # prob = 2 / 47 * 1 / 46
            # prob += 4 / 47 + 43 / 47 * 4 / 46
            prob = 0.16558741905642924
    return prob


def two_pairs_j(card_list=[]):
    card_number_list = set([c[0] for c in card_list])
    number_dict = {}
    for n in card_number_list:
        number_dict[n] = 0
    pair_count = 0
    cards_to_deal = 7 - len(card_list)
    big_pair = 0
    bigger_set = set()

    for c in card_list:
        number_dict[c[0]] += 1
        if number_dict[c[0]] == 2:
            pair_count += 1
            if c[0] in HIGHER_J:
                big_pair += 1

    if big_pair > 0 and pair_count > 2:
        # already meet the goal
        return 1.0

    bigger_set = HIGHER_J.intersection(card_number_list)
    prob = 0.0
    # print('number_dict:{}'.format(number_dict))
    # print('target_card:{}'.format(target_card))
    # print('pair_count:{}'.format(pair_count))
    """
    if pair_count == 3:
        # no chance
        prob = 0.0
    """
    if pair_count == 2:
        if cards_to_deal == 1:
            # card type should be 2 2 1 1
            # get one bigger care to become a pair
            prob = len(bigger_set) * 3 / 46.0
        else:
            # card type should be 2 2 1
            if len(bigger_set) == 0:
                # get two same bigger cards
                # prob = (4 * 4 / 47) * (3 / 46)
                prob = 0.022201665124884366
            else:
                # len(bigger_set) == 1
                # get one card same with the bigger card and any one other card or
                # get two same bigger cards
                # prob = (3 / 47) + (44 / 47) * (3 / 46)
                # prob += (3 * 4 / 47) * (3 / 46)
                prob = 0.14153561517113783
    elif pair_count == 1:
        if cards_to_deal == 1:
            # card type should be 2 1 1 1 1
            if len(bigger_set) == 0:
                prob = 0.0
            else:
                if big_pair == 1:
                    # get one more pair same with single
                    # prob = 4 * 3 / 46
                    prob = 0.2608695652173913
                else:
                    # get one more pair same with bigger single
                    prob = 3 * len(bigger_set) / 46.0
        else:
            # cards_to_deal == 2
            # card type should be 2 1 1 1
            if len(bigger_set) == 0:
                # get two same bigger cards
                # prob = (4 * 4 / 47) * (3 / 46)
                prob = 0.022201665124884366
            else:
                if big_pair == 1:
                    # get one single and any other or
                    # get two same other cards
                    # prob = (3 * 3 / 47) + ((38 / 47) * (3 * 3 / 46))
                    # prob += (4 * 9 / 47) * (3 / 46)
                    prob = 0.3996299722479186
                else:
                    # get one card same with bigger single and any other one or
                    # get two same bigger cards not same with bigger single
                    # prob = (3 * len(bigger_set) / 47) + ((47 - 3 * len(bigger_set)) / 47) * (3 * len(bigger_set) / 46)
                    # prob += ((4 * (4 - len(bigger_set))) / 47 ) * (3 / 46)
                    prob = ((267 - 9 * len(bigger_set)) * len(bigger_set) + 48) / 2162.0
    else:
        # pair_count == 0
        if cards_to_deal == 1:
            return 0.0
        else:
            # card type should be 1 1 1 1 1
            # get one bigger single and any other single
            # porb = (3 * len(bigger_set) / 47) * (3 * 4 / 46)
            prob = (36 * len(bigger_set)) / 2162.0
    return prob


def two_pairs(card_list=[]):
    card_number_list = set([c[0] for c in card_list])
    number_dict = {}
    for n in card_number_list:
        number_dict[n] = 0
    pair_count = 0
    cards_to_deal = 7 - len(card_list)

    for c in card_list:
        number_dict[c[0]] += 1
        if number_dict[c[0]] == 2:
            pair_count += 1

    if pair_count > 1:
        return 1.0

    if pair_count == 1:
        # need one more cards
        if cards_to_deal == 1:
            # card type should be 2 1 1 1 1
            # get one from the card already had one(4 kinds card)
            # prob = 3 * 4 / 46.0
            prob = 0.2608695652173913
        else:
            # card type should be 2 1 1 1
            # 1 - prob get two cards without any pair - prob get one same with pair and one other - prob two same with the pair
            # prob = 1 - (4 * 9 / 47) * (4 * 8 / 46)
            # prob -= ((2 / 47) * (9 * 4 / 46) * 2)
            # prob -= (2 / 47) * (1 / 46)
            # prob = 0.39962997224791863
            # get one from single and any other or
            # get two same cards from other
            # prob = (3 * 3 / 47) + (38 / 47) * (3 * 3 / 46)
            # prob += (9 * 4 / 47) * 3 / 46
            prob = 0.3996299722479186
    else:
        # pair_count == 0
        if cards_to_deal == 2:
            # get two different cards from single
            # prob = (3 * 5 / 47) * (3 * 4 / 46) * 2
            prob = 0.16651248843663274
        else:
            prob = 0.0
    return prob


def one_pair_j(card_list=[]):
    card_number_list = set([c[0] for c in card_list])
    number_dict = {}
    bigger_than_J_count = 0
    for n in card_number_list:
        number_dict[n] = 0
        if n in HIGHER_J:
            bigger_than_J_count += 1
    pair_count = 0
    cards_to_deal = 7 - len(card_list)
    target_card = None

    for c in card_list:
        number_dict[c[0]] += 1
        if number_dict[c[0]] == 2:
            pair_count += 1
            if c[0] in HIGHER_J:
                target_card = c[0]
    if target_card is not None:
        # already meet the goal
        return 1.0

    prob = 0.0
    if cards_to_deal == 1:
        if bigger_than_J_count > 0:
            # get an other bigger than J
            prob = 3 * bigger_than_J_count / 46.0
    else:
        if bigger_than_J_count > 0:
            # get one same with the bigger and anyother or
            # get two same cards of other bigger cards
            # prob = 3 * bigger_than_J_count / 47 + ((47  - 3 * bigger_than_J_count) / 47) * (3 * bigger_than_J_count / 46)
            # prob += (4 * (4 - bigger_than_J_count) / 47) * (3 / 46)
            prob = ((267 - 9 * bigger_than_J_count) * bigger_than_J_count + 48) / 2162.0
        else:
            # get two same big cards
            # prob = (4 * 4 / 47) * (3 / 46)
            prob = 0.022201665124884366
    return prob


def one_pair(card_list=[]):
    card_number_list = set([c[0] for c in card_list])
    if len(card_number_list) < len(card_list):
        return 1.0
    cards_to_deal = 7 - len(card_list)

    if cards_to_deal == 1:
        # card type should be 1 1 1 1 1 1
        # get one same with single
        # prob = 3 * 6 / 46
        prob = 0.391304347826087
    else:
        # card type should be 1 1 1 1 1
        # cards_to_deal == 2
        # 1 - prob get one other card and an other card (1 - no pair)
        # prob = 1 - ((4 * (13 - 5) / 47) * (4 * (12 - 5) / 46))
        # prob = 0.5855689176688252
        # get one from single and any other one or
        # two same cards not same with single
        # prob = (3 * 5 / 47) + (8 * 4 / 47) * (3 * 5 / 46)
        # prob += (8 * 4 / 47) * (3 / 46)
        prob = 0.5855689176688251
    return prob


if __name__ == '__main__':
    import sys
    card = []
    for i in range(len(sys.argv) - 1):
        card.append(sys.argv[i + 1])
    print(get_expected_value(card))
