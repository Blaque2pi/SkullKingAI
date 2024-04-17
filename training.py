import random, json

# Number of training games
games = 1

# Initialize q-table
with open('decision.json', 'r') as file:
    q_table = json.load(file)

# Integer representation of each unique card
card_integers = {
    "Escape": 1,
    "Tigress as Escape": 2,
    "1 of Yellow": 3,
    "2 of Yellow": 4,
    "3 of Yellow": 5,
    "4 of Yellow": 6,
    "5 of Yellow": 7,
    "6 of Yellow": 8,
    "7 of Yellow": 9,
    "8 of Yellow": 10,
    "9 of Yellow": 11,
    "10 of Yellow": 12,
    "11 of Yellow": 13,
    "12 of Yellow": 14,
    "13 of Yellow": 15,
    "14 of Yellow": 16,
    "1 of Purple": 17,
    "2 of Purple": 18,
    "3 of Purple": 19,
    "4 of Purple": 20,
    "5 of Purple": 21,
    "6 of Purple": 22,
    "7 of Purple": 23,
    "8 of Purple": 24,
    "9 of Purple": 25,
    "10 of Purple": 26,
    "11 of Purple": 27,
    "12 of Purple": 28,
    "13 of Purple": 29,
    "14 of Purple": 30,
    "1 of Green": 31,
    "2 of Green": 32,
    "3 of Green": 33,
    "4 of Green": 34,
    "5 of Green": 35,
    "6 of Green": 36,
    "7 of Green": 37,
    "8 of Green": 38,
    "9 of Green": 39,
    "10 of Green": 40,
    "11 of Green": 41,
    "12 of Green": 42,
    "13 of Green": 43,
    "14 of Green": 44,
    "1 of Black": 45,
    "2 of Black": 46,
    "3 of Black": 47,
    "4 of Black": 48,
    "5 of Black": 49,
    "6 of Black": 50,
    "7 of Black": 51,
    "8 of Black": 52,
    "9 of Black": 53,
    "10 of Black": 54,
    "11 of Black": 55,
    "12 of Black": 56,
    "13 of Black": 57,
    "14 of Black": 58,
    "Pirate": 59,
    "Tigress as Pirate": 60,
    "Tigress": 61,
    "Skull King": 62,
}

# Hyperparameters
ALPHA = 0.1
GAMMA = 0.9
EPSILON = 0.1


class Card:
    def __init__(self, suit=None, rank=None, special=None):
        self.suit = suit
        self.rank = rank
        self.special = special
        self.played_as = None  # Attribute for determining Tigress mode

    def __str__(self):
        if self.special:
            if not self.played_as:
                return self.special
            else:
                return f"{self.special} as {self.played_as}"
        return f"{self.rank} of {self.suit}"


class Player:
    def __init__(self, name, is_human=False):
        self.name = name
        self.hand = []
        self.bid = 0
        self.tricks_taken = 0
        self.bonus_points = 0
        self.score = 0
        self.is_human = is_human
        self.is_trick_leader = False
        self.round_number = 0


    def determine_legality(self, chosen_card, leading_suit=None):

        if not leading_suit:
            return True  # If there's no leading suit, any card can be played

        # Check if chosen card matches the leading suit
        if chosen_card.suit == leading_suit:
            return True

        # Check if chosen card is a special card
        if chosen_card.special:
            return True

        # Check if the player has any card of the leading suit or any special card
        has_leading_suit = any(card.suit == leading_suit for card in self.hand)

        # If player doesn't have the leading suit, they can play any card
        if not has_leading_suit:
            return True

        return False


class AIAgent(Player):
    def __init__(self, name):
        super().__init__(name)
        self.old_state = {}  # Save old state temporarily for determining reward
        self.old_state_action = 0  # Save old action temporarily for determining reward
        self.new_state = {}  # Save new state temporarily for determining reward

    def get_state(self, players, trick=[]):
        # hand should already be in a sorted state, this is good because order of cards in hand does not matter
        # Combining all the features into one state representation, each element should be normalized
        state = {
            "Hand": [card_integers[f"{self.hand[i]}"]/len(card_integers) for i in range(len(self.hand))],  # Needs normalized representation, would require assigning a unique integer to each unique card
            "Leading Suit": [determine_leading_suit(trick)],  # Normalized representation
            "Tricks to Bid": [(player.bid - player.tricks_taken)/self.round_number for player in players],  # Normalize over round number (i.e. maxmimum allowable bid for round)
        }

        return state

    def get_legal_actions(self, leading_suit=None):
        legal_indices = []
        contains_tigress = None

        for card in self.hand:
            if card.special == "Tigress":
                contains_tigress = True

        for index, card in enumerate(self.hand):
            if self.determine_legality(card, leading_suit):
                legal_indices.append(index)

        if contains_tigress:
            legal_indices.append(len(self.hand))

        return legal_indices

    def make_bid(self):
        # This can be further refined
        self.bid = len([card for card in self.hand if card.rank and card.rank >= 10])
        return self.bid

    def play_card(self, players, trick, leading_suit=None):
        state_str = json.dumps(self.get_state(players, trick), sort_keys=True)
        if state_str not in q_table:
            num_actions = len(self.hand)
            for card in self.hand:
                if f"{card}" == "Tigress":
                    num_actions += 1
            q_table[state_str] = {f"{i}": 0 for i in range(num_actions)}

        # Retrieve the list of legal actions for the current state.
        legal_actions = self.get_legal_actions(leading_suit)

        # Epsilon-greedy strategy
        if random.uniform(0, 1) < EPSILON:
            # Select a random action from the set of legal actions
            action = random.choice(legal_actions)
        else:
            # Find the max Q-value among legal actions for the current state
            max_q_value = max([q_table[state_str][f"{action}"] for action in legal_actions])
            max_actions = [action for action in legal_actions if q_table[state_str][f"{action}"] == max_q_value]

            # Randomly select one of the max actions
            action = random.choice(max_actions)

        # check if tigress was played as a pirate or escape, and edit the corresponding card accordingly
        card_to_play = None
        if action == len(self.hand):
            for card in self.hand:
                if card.special == "Tigress":
                    card.played_as = "Escape"
                    card_to_play = card
        elif self.hand[action].special == "Tigress":
            self.hand[action].played_as = "Pirate"
            card_to_play = self.hand[action]
        else:
            card_to_play = self.hand[action]

        self.hand.remove(card_to_play)
        self.old_state = state_str
        self.old_state_action = action

        return card_to_play

    def update_q_value(self, reward):
        # Check turn order after trick resolution to determine how many cards will be played before next decision
        # Iterate through potential tricks that may be played before next decision and gather maximum q from those scenarios
        relevant_states = []
        current_hand_normalized = [card_integers[f"{self.hand[i]}"]/len(card_integers) for i in range(len(self.hand))]
        for state_str in q_table:
            state = json.loads(state_str)
            state_hand = state["Hand"]
            if state_hand == current_hand_normalized:
                relevant_states.extend(q_table[state_str].values())

        max_future_q = max(relevant_states) if relevant_states else 0

        current_q = q_table[self.old_state][f"{self.old_state_action}"]

        # Q-learning formula
        new_q = (1 - ALPHA) * current_q + ALPHA * (reward + GAMMA * max_future_q)
        q_table[self.old_state][f"{self.old_state_action}"] = new_q


def sort_hand(card):
    # Define an order for colors and specials
    color_order = {"Yellow": 0, "Purple": 1, "Green": 2, "Black": 3}
    special_order = ["Escape", "Pirate", "Tigress", "Skull King"]

    # Assign a sort key based on color or special
    if card.special:
        return (4, special_order.index(card.special))
    return (color_order[card.suit], card.rank)


def deal_cards(players, round_number):
    # All cards including suits and specials
    colors = ["Black", "Yellow", "Purple", "Green"]
    specials = [("Escape", 5), ("Pirate", 5), ("Tigress", 1), ("Skull King", 1)]
    deck = [Card(color, rank) for color in colors for rank in range(1, 15)] + [Card(None, None, special) for special, count in specials for _ in range(count)]
    random.shuffle(deck)

    # Deal cards and keep hands sorted
    for i in range(round_number):
        for player in players:
            player.hand.append(deck.pop())

    # Sort each player's hand using the custom sort function
    for player in players:
        player.hand.sort(key=sort_hand)
        player.round_number = round_number


def gather_bids(players, round_number):
    bids = {}
    for player in players:
        player.bid = player.make_bid()  # The AI's bidding logic
        bids[player.name] = player.bid


def play_tricks(players, round_number):
    for _ in range(round_number):
        current_trick = []

        for player in players:
            player.is_trick_leader = False
            leading_suit = determine_leading_suit(current_trick)
            card_played = player.play_card(players, current_trick, leading_suit)
            current_trick.append((player, card_played))

        # Determine the winner of the trick
        winner = determine_winner(current_trick)
        bonus_points = determine_bonus_points(current_trick)
        if winner[0].tricks_taken < winner[0].bid:
            winner[0].update_q_value(5)
        if winner[0].tricks_taken == winner[0].bid and winner[0].bid == 0:
            winner[0].update_q_value(-5)
        if winner[0].tricks_taken >= winner[0].bid and winner[0].bid > 0:
            winner[0].update_q_value(-5)
        winner[0].tricks_taken += 1
        winner[0].bonus_points += bonus_points
        winner[0].is_trick_leader = True
        if bonus_points:
            winner[0].update_q_value(bonus_points/10)
        players = determine_turn_order(players)


def determine_leading_suit(trick):
    leading_suit = None
    for player, card in trick:
        if not card.special or (card.special != "Escape" and card.suit is not None):  # Ignore Escapes and special cards without suits
            leading_suit = card.suit
            break
    return leading_suit


def determine_bonus_points(trick):
    bonus_points = 0
    king_played = None
    pirates_captured_by_king = 0

    for player, card in trick:
        if card.special == "Skull King":
            king_played = player

    if king_played:
        for player, card in trick:
            if card.special == "Pirate":
                pirates_captured_by_king += 1
            elif card.special == "Tigress" and card.played_as == "Pirate":
                pirates_captured_by_king += 1
        bonus_points += pirates_captured_by_king * 30  # For each pirate captured by the king

    for player, card in trick:
        if card.rank == 14:
            if card.suit != "Black":
                bonus_points += 10
            else:
                bonus_points += 20

    return bonus_points


def determine_winner(trick):
    special_ranks = {
        "Skull King": 3,
        "Pirate": 2,
        "Escape": 1,
    }
    leading_suit = determine_leading_suit(trick)
    highest_special = None
    highest_suit_card = None

    only_escapes = all((card.special == 'Escape' or card.played_as == 'Escape') for player, card in trick)

    for player, card in trick:
        if card.special:
            # If the card is a Tigress, use its played_as attribute to determine its rank
            rank = special_ranks[card.played_as] if card.special == 'Tigress' else special_ranks[card.special]
            if not highest_special or rank > special_ranks[highest_special[1].played_as if highest_special[1].special == 'Tigress' else highest_special[1].special]:
                highest_special = (player, card)
        elif card.suit == leading_suit:
            if not highest_suit_card or card.rank > highest_suit_card[1].rank:
                highest_suit_card = (player, card)
        elif card.suit == "Black" and highest_suit_card[1].suit != "Black":
            highest_suit_card = (player, card)
            leading_suit = card.suit

    if highest_special:
        if (highest_special[1].special == 'Escape' or highest_special[1].played_as == 'Escape') and not only_escapes:
            return highest_suit_card or highest_special
    return highest_special or highest_suit_card


def score_round(players, round_number):
    for player in players:
        if player.bid == 0:
            if player.bid == player.tricks_taken:
                player.score += 10 * round_number
                player.score += player.bonus_points
                player.update_q_value(10)
            else:
                player.score -= 10 * round_number
                player.update_q_value(-10)
        else:
            if player.bid == player.tricks_taken:
                player.score += 20 * player.bid
                player.score += player.bonus_points
                player.update_q_value(10)
            else:
                player.score -= 10 * abs(player.bid - player.tricks_taken)
                player.update_q_value(-5)
        player.tricks_taken = 0
        player.bonus_points = 0


def determine_turn_order(players, round_number=None):
    # Determine the index of the player who has the flag
    if round_number:
        leader_index = (round_number % len(players)) - 1
    else:
        leader_index = next((i for i, player in enumerate(players) if player.is_trick_leader), None)

    if leader_index is not None:
        # Rearrange the list so the player with the flag is the first player
        players = players[leader_index:] + players[:leader_index]

    return players


def play_round(players, round_number):
    default_players = players
    deal_cards(players, round_number)
    gather_bids(players, round_number)
    players = determine_turn_order(players, round_number)
    play_tricks(players, round_number)
    players = default_players
    score_round(players, round_number)


# No need to determine winner for Q-table
# Log time of game, cache hits based on hand size, size of dictionary at end of each game (how many entries gained in each game)
for i in range(games):
    print(f"starting game {i+1}")
    players = [AIAgent("AI1"), AIAgent("AI2"), AIAgent("AI3"), AIAgent("AI4")]
    for round_number in range(1, 11):
        play_round(players, round_number)

with open('decision.json', 'w') as file:
    json.dump(q_table, file, indent=4)
