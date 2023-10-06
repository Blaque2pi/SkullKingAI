import random


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

    def display_hand(self):
        hand_message = f"\n{self.name}'s hand contains:\n"
        for index, card in enumerate(self.hand):
            hand_message += f"{index + 1}. {card}\n"  # Assuming the card object has a __str__ method to display it
        print(hand_message)

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

    def choose_card(self, leading_suit=None):
        """
        Choose a card to play.
        If human, allow them to select a card.
        Otherwise, play a card of the leading suit if available,
        or any random card.
        """
        if self.is_human:
            self.display_hand()
            while True:
                try:
                    choice = int(input(f"{self.name}, choose a card to play by entering the number: ")) - 1
                    if 0 <= choice < len(self.hand):
                        chosen_card = self.hand[choice]
                        is_legal = self.determine_legality(chosen_card, leading_suit)
                        if is_legal:
                            break
                        else:
                            print("Invalid choice. You cannot play this card if you have a card of the leading suit!")
                    else:
                        print("Invalid choice. Please select a valid card.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
        else:
            same_suit_cards = [card for card in self.hand if card.suit == leading_suit]
            special_cards = [card for card in self.hand if card.special]
            legal_cards = same_suit_cards + special_cards
            chosen_card = random.choice(legal_cards) if legal_cards else random.choice(self.hand)

        self.hand.remove(chosen_card)
        return chosen_card

    def choose_tigress_type(self):
        """
        Decide how to play the Tigress card.
        If human, allow them to choose.
        Otherwise, randomly choose between Pirate or Escape.
        """
        if self.is_human:
            while True:
                choice = input(
                    f"{self.name}, do you want to play the Tigress as a Pirate or Escape? (Enter 'Pirate' or 'Escape'): ")
                if choice in ['Pirate', 'Escape']:
                    return choice
                else:
                    print("Invalid choice. Please enter 'Pirate' or 'Escape'.")
        else:
            return random.choice(['Pirate', 'Escape'])

    def play_card(self, leading_suit=None):
        """
        Play a card from hand.
        If the chosen card is Tigress, decide how to play it.
        """
        card = self.choose_card(leading_suit)

        # If the chosen card is the Tigress, decide how to play it and set the played_as attribute
        if card.special == 'Tigress':
            card.played_as = self.choose_tigress_type()

        return card


class AIAgent(Player):
    def __init__(self, name):
        super().__init__(name)
        self.q_table = {}

    def get_state(self):
        # A simple state representation for illustrative purposes
        # In a real scenario, this will be more complex
        hand_ranks = tuple(card.rank for card in sorted(self.hand, key=lambda c: c.rank if c.rank else 0))
        return hand_ranks

    def make_bid(self):
        # This can be further refined
        self.bid = len([card for card in self.hand if card.rank and card.rank >= 10])
        return self.bid

    def play_card(self, leading_suit=None):
        state = self.get_state()
        if state not in self.q_table:
            self.q_table[state] = {i: 0 for i in range(len(self.hand))}

        # Epsilon-greedy strategy
        if random.uniform(0, 1) < EPSILON:
            action = random.choice(range(len(self.hand)))
        else:
            action = max(self.q_table[state], key=self.q_table[state].get)

        card_to_play = self.hand[action]
        self.hand.remove(card_to_play)
        return card_to_play

    def update_q_value(self, old_state, action, reward, new_state):
        max_future_q = max(self.q_table[new_state].values())
        current_q = self.q_table[old_state][action]

        # Q-learning formula
        new_q = (1 - ALPHA) * current_q + ALPHA * (reward + GAMMA * max_future_q)
        self.q_table[old_state][action] = new_q

    def take_reward(self, reward):
        # After the agent receives a reward, update Q-values
        new_state = self.get_state()
        # You need to keep track of the old state and action
        # This is a simplified representation
        old_state = new_state  # This is a placeholder, you'd typically store the previous state
        action = 0  # Placeholder, you'd typically store the previous action

        self.update_q_value(old_state, action, reward, new_state)


def deal_cards(players, round_number):
    # All cards including suits and specials
    colors = ["Black", "Yellow", "Blue", "Red"]
    specials = [("Escape", 5), ("Pirate", 5), ("Tigress", 1), ("Skull King", 1)]
    deck = [Card(color, rank) for color in colors for rank in range(1, 15)] + [Card(None, None, special) for special, count in specials for _ in range(count)]
    print("\nDeck assembled!")
    random.shuffle(deck)
    print("Deck Shuffled!")

    # Deal cards
    for i in range(round_number):
        for player in players:
            player.hand.append(deck.pop())
    print("Hands Dealt!")


def gather_bids(players, round_number):
    bids = {}
    for player in players:
        if isinstance(player, AIAgent):
            player.bid = player.make_bid()  # The AI's bidding logic
        else:
            while True:  # keep asking for bid until a valid input is given
                try:
                    # Asking bid from human players
                    player.display_hand()
                    bid = int(input(f"{player.name}, enter your bid (0 to {round_number}): "))
                    if 0 <= bid <= round_number:
                        player.bid = bid
                        break  # exit the loop if a valid bid is given
                    else:
                        print(f"Invalid bid. Please enter a number between 0 and {round_number}.")
                except ValueError:  # handle non-integer inputs
                    print("Invalid input. Please enter a number.")
        bids[player.name] = player.bid

    # Announce all bids after they have been placed
    bid_message = "\n"
    for player_name, bid in bids.items():
        bid_message += f"{player_name} bids {bid}\n"
    print(bid_message)


def play_tricks(players, round_number):
    for _ in range(round_number):
        current_trick = []

        for player in players:
            player.is_trick_leader = False
            leading_suit = determine_leading_suit(current_trick)
            card_played = player.play_card(leading_suit if leading_suit else None)
            current_trick.append((player, card_played))
            print(f"{player.name} plays {card_played}")

        # Determine the winner of the trick
        winner = determine_winner(current_trick)
        bonus_points = determine_bonus_points(current_trick)
        winner[0].tricks_taken += 1
        winner[0].bonus_points += bonus_points
        winner[0].is_trick_leader = True
        players = determine_turn_order(players)
        print(f"\n{winner[0].name} wins the trick!\n")


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
            else:
                player.score -= 10 * round_number
        else:
            if player.bid == player.tricks_taken:
                player.score += 20 * player.bid
                player.score += player.bonus_points
            else:
                player.score -= 10 * abs(player.bid - player.tricks_taken)
        print(f"{player.name}'s Score: {player.score}")
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


def determine_final_winner(players):
    winning_score = -550
    winner = "no one"
    for player in players:
        if player.score > winning_score:
            winning_score = player.score
            winner = player.name
        elif player.score == winning_score:
            winner = f"{winner} and {player.name}"
    print(f"The winner is {winner}!")


def main():
    players = [AIAgent("AI1"), AIAgent("AI2"), AIAgent("AI3"), AIAgent("AI4")]
    for round_number in range(1, 11):
        play_round(players, round_number)
    determine_final_winner(players)


if __name__ == "__main__":
    main()
