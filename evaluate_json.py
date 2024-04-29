import random, json, time, os
from plot_scores import *
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import traceback

# Print game logs
print_logs = False

# Number of sessions and games to play
sessions = 10
games = 10000

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

# Integer representation of each suit
suit_integers = {
    "Yellow": 1,
    "Purple": 2,
    "Green": 3,
    "Black": 4,
}

# Initialize q-table
with open('decision.json', 'r') as file:
    q_table = json.load(file)

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
        if print_logs:
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
                            if print_logs:
                                print("Invalid choice. You cannot play this card if you have a card of the leading suit!")
                    else:
                        if print_logs:
                            print("Invalid choice. Please select a valid card.")
                except ValueError:
                    if print_logs:
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
                    if print_logs:
                        print("Invalid choice. Please enter 'Pirate' or 'Escape'.")
        else:
            return random.choice(['Pirate', 'Escape'])

    def play_card(self, players, trick, leading_suit=None):
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
        self.bid = len([card for card in self.hand if card.rank is not None and card.rank > 10])
        self.bid += len([card for card in self.hand if card.special == "Tigress" or card.special == "Pirate" or card.special == "Skull King"])
        # hand_str = [f"{card}" for card in self.hand]
        # print(f"Bid is {self.bid} for hand of {hand_str}")
        return self.bid


class TrainedAIAgent(AIAgent):
    def __init__(self, name):
        super().__init__(name)

    def get_state(self, trick=[]):
        # hand should already be in a sorted state, this is good because order of cards in hand does not matter
        # Combining all the features into one state representation, each element should be normalized
        state = {
            "Hand": [card_integers[f"{card}"] / len(card_integers) for card in
                     self.get_legal_hand(determine_leading_suit(trick))],
            # Needs normalized representation, would require assigning a unique integer to each unique card
            "Winning Card": [card_integers[f"{determine_winner(trick)[1]}"] / len(card_integers) if trick else 0],
            "Tricks to Bid": [
                1 if self.bid - self.tricks_taken > 0 else 0.5 if self.bid - self.tricks_taken == 0 else 0]
        }

        return state


    def get_legal_hand(self, leading_suit=None):
        legal_hand = []
        if leading_suit:
            for card in self.hand:
                if self.determine_legality(card, leading_suit):
                    legal_hand.append(card)
        else:
            legal_hand = self.hand

        return legal_hand


    def play_card(self, players, trick, leading_suit=None):
        state_str = json.dumps(self.get_state(trick), sort_keys=True)

        # Retrieve the list of legal actions for the current state.
        legal_hand = self.get_legal_hand(leading_suit)
        legal_actions = len(legal_hand)
        for card in legal_hand:
            if card.special == "Tigress":
                legal_actions += 1

        if state_str not in q_table:
            # Select a random legal actions
            action = random.randint(0, legal_actions-1)
        else:
            # Find the max Q-value among legal actions for the current state
            max_q_value = max([q_table[state_str][f"{i}"] for i in range(legal_actions)])
            max_actions = [i for i in range(legal_actions) if q_table[state_str][f"{i}"] == max_q_value]

            # Randomly select one of the max actions
            action = random.choice(max_actions)

        # check if tigress was played as a pirate or escape, and edit the corresponding card accordingly
        card_to_play = None
        if action == len(legal_hand):
            for card in legal_hand:
                if card.special == "Tigress":
                    card.played_as = "Escape"
                    card_to_play = card
        elif legal_hand[action].special == "Tigress":
            legal_hand[action].played_as = "Pirate"
            card_to_play = legal_hand[action]
        else:
            card_to_play = legal_hand[action]

        self.hand.remove(card_to_play)

        return card_to_play


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
    colors = ["Yellow", "Purple", "Green", "Black"]
    specials = [("Escape", 5), ("Pirate", 5), ("Tigress", 1), ("Skull King", 1)]
    deck = [Card(color, rank) for color in colors for rank in range(1, 15)] + [Card(None, None, special) for special, count in specials for _ in range(count)]
    if print_logs:
        print("\nDeck assembled!")
    random.shuffle(deck)
    if print_logs:
        print("Deck Shuffled!")

    # Deal cards and keep hands sorted
    for i in range(round_number):
        for player in players:
            player.hand.append(deck.pop())

    # Sort each player's hand using the custom sort function
    for player in players:
        player.hand.sort(key=sort_hand)
    if print_logs:
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
                        if print_logs:
                            print(f"Invalid bid. Please enter a number between 0 and {round_number}.")
                except ValueError:  # handle non-integer inputs
                    if print_logs:
                        print("Invalid input. Please enter a number.")
        bids[player.name] = player.bid

    # Announce all bids after they have been placed
    bid_message = "\n"
    for player_name, bid in bids.items():
        bid_message += f"{player_name} bids {bid}\n"
    if print_logs:
        print(bid_message)


def play_tricks(players, round_number):
    for _ in range(round_number):
        current_trick = []

        for player in players:
            player.is_trick_leader = False
            leading_suit = determine_leading_suit(current_trick)
            card_played = player.play_card(players, current_trick, leading_suit if leading_suit else None)
            current_trick.append((player, card_played))
            if print_logs:
                print(f"{player.name} plays {card_played}")

        # Determine the winner of the trick
        winner = determine_winner(current_trick)
        bonus_points = determine_bonus_points(current_trick)
        winner[0].tricks_taken += 1
        winner[0].bonus_points += bonus_points
        winner[0].is_trick_leader = True
        players = determine_turn_order(players)
        if print_logs:
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
        if print_logs:
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
    scores = []
    winners = []
    winner_str = "No one"
    # Collect scores and reset player scores
    for player in players:
        scores.append((player.name, player.score))
        player.score = 0

    # Determine the highest score
    if scores:
        max_score = max(scores, key=lambda x: x[1])[1]  # Extract the highest score using max() + lambda function
        winners = [name for name, score in scores if score == max_score]  # List all players who have the highest score

    for i, winner in enumerate(winners):
        if i==0:
            winner_str = winner
        if i>0:
            winner_str = f"{winner_str} and {winner}"

    if print_logs:
        print(f"The winner(s) is/are {winner_str}!")
    return winners


def load_data(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    else:
        return []


def append_scores(file_path, new_scores):
    data = load_data(file_path)
    data.append(new_scores)
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)


# Save (or reset) JSON data to a file
def save_data(filepath, data):
    with open(filepath, 'w') as file:
        json.dump(data, file)


def run_session(players, session_number, games):
    try:
        games_won = {player.name: 0 for player in players}
        for i in range(games):
            for round_number in range(1, 11):
                play_round(players, round_number)
            winners = determine_final_winner(players)
            for winner in winners:
                games_won[winner] += 1
        return games_won
    except Exception as e:
        print(f"Exception in session {session_number}: {e}")
        traceback.print_exc()
        raise


def run_sessions(players, sessions=10, games=10000):
    print(f"Running sessions for {', '.join(player.name for player in players)}...")
    session_results = []

    with ProcessPoolExecutor() as executor:
        # Submit all sessions to the executor
        future_to_session = {executor.submit(run_session, players, session, games): session for session in
                             range(1, sessions + 1)}

        for future in as_completed(future_to_session):
            session_number = future_to_session[future]
            try:
                result = future.result()
                print(f"Session {session_number} completed with results: {result}")
                session_results.append(result)
            except Exception as exc:
                print(f"Session {session_number} generated an exception: {exc}")

    # Combine results from all sessions
    final_results = {player.name: 0 for player in players}
    for result in session_results:
        for name, wins in result.items():
            final_results[name] += wins
    for name in final_results:
        final_results[name] /= sessions

    # Operations after all sessions
    file_path = 'scores.json'
    append_scores(file_path, final_results)
    plot_scores()
    save_data(file_path, [])  # Reset the JSON file after plotting

if __name__ == "__main__":
    start_time = time.perf_counter()

    multiprocessing.set_start_method('spawn')

    # players = [AIAgent("AI1"), AIAgent("AI2"), AIAgent("AI3"), AIAgent("AI4")]
    # run_sessions(players, sessions, games)
    #
    players = [AIAgent("AI1"), AIAgent("AI2"), AIAgent("AI3"), TrainedAIAgent("TAI")]
    run_sessions(players, sessions, games)

    players = [AIAgent("AI1"), AIAgent("AI2"), TrainedAIAgent("TAI"), AIAgent("AI4")]
    run_sessions(players, sessions, games)

    players = [AIAgent("AI1"), TrainedAIAgent("TAI"), AIAgent("AI3"), AIAgent("AI4")]
    run_sessions(players, sessions, games)

    players = [TrainedAIAgent("TAI"), AIAgent("AI2"), AIAgent("AI3"), AIAgent("AI4")]
    run_sessions(players, sessions, games)

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time} seconds")
