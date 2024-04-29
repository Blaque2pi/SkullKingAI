import random, json, time, sys, sqlite3
import matplotlib.pyplot as plt
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import traceback

# Initialize q-table name and number of training games
db_name = sys.argv[2] if len(sys.argv) > 2 else "q_table"
games = int(sys.argv[1]) if len(sys.argv) > 1 else 100

# Initialize q-table path
db_path = f'{db_name}.db'

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
        self.max_future_q = None
        self.added_states = 0

    def get_state(self, players, trick=[]):
        # hand should already be in a sorted state, this is good because order of cards in hand does not matter
        # Combining all the features into one state representation, each element should be normalized
        state = {
            "Hand": [card_integers[f"{self.hand[i]}"]/len(card_integers) for i in range(len(self.hand))],  # Needs normalized representation, would require assigning a unique integer to each unique card
            "Leading Suit": [suit_integers[determine_leading_suit(trick)]/len(suit_integers) if determine_leading_suit(trick) else 0],  # Normalized representation
            "Winning Card": [card_integers[f"{determine_winner(trick)[1]}"]/len(card_integers) if trick else 0],
            "Tricks to Bid": [(self.bid - self.tricks_taken + 10)/20],  # Normalize over round number (i.e. maxmimum allowable bid for round)
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
        self.bid = len([card for card in self.hand if card.rank is not None and card.rank > 10])
        self.bid += len([card for card in self.hand if card.special == "Tigress" or card.special == "Pirate" or card.special == "Skull King"])
        # hand_str = [f"{card}" for card in self.hand]
        # print(f"Bid is {self.bid} for hand of {hand_str}")
        return self.bid

    def play_card(self, players, trick, leading_suit=None, db_path='q_table.db'):
        state_str = json.dumps(self.get_state(players, trick), sort_keys=True)
        num_actions = len(self.hand) + sum(1 for card in self.hand if card == "Tigress")
        ensure_state_exists(db_path, state_str, num_actions)

        # Retrieve the list of legal actions for the current state.
        legal_actions = self.get_legal_actions(leading_suit)
        action_values = fetch_q_values_for_actions(db_path, state_str, legal_actions)

        # Epsilon-greedy strategy
        if random.uniform(0, 1) < EPSILON:
            # Select a random action from the set of legal actions
            action = random.choice(legal_actions)
        else:
            # Find the max Q-value among legal actions for the current state
            max_q_value = max(action_values.values())
            max_actions = [action for action in action_values if action_values[action] == max_q_value]
            action = int(random.choice(max_actions))


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

    def update_q_value(self, reward, db_path='q_table.db'):
        # Check turn order after trick resolution to determine how many cards will be played before next decision
        # Iterate through potential tricks that may be played before next decision and gather maximum q from those scenarios
        if self.max_future_q is None:
            current_hand_normalized = [card_integers[f"{self.hand[i]}"]/len(card_integers) for i in range(len(self.hand))]
            with sqlite3.connect(db_path) as conn:
                cur = conn.cursor()

                relevant_states_values = []

                for i in range(len(suit_integers)+1):
                    for j in range(len(card_integers)+1):
                        for k in range(21):
                            potential_state = {
                                "Hand": current_hand_normalized,
                                "Leading Suit": [i/len(suit_integers)],
                                "Winning Card": [j/len(card_integers)],
                                "Tricks to Bid": [k/20],
                            }
                            potential_state_str = json.dumps(potential_state, sort_keys=True)
                            cur.execute("SELECT value FROM QTable WHERE state=?", (potential_state_str,))
                            fetched = cur.fetchall()
                            relevant_states_values.extend([val[0] for val in fetched])  # Extract values from fetched tuples

                self.max_future_q = max(relevant_states_values) if relevant_states_values else 0

                # Fetch the current Q-value
                cur.execute("SELECT value FROM QTable WHERE state=? AND action=?",
                            (self.old_state, str(self.old_state_action)))
                current_q_result = cur.fetchone()
                current_q = current_q_result[0] if current_q_result else 0  # Assume 0 if not found

                # Calculate the new Q-value
                new_q = (1 - ALPHA) * current_q + ALPHA * (reward + GAMMA * self.max_future_q)

                # Update the Q-value in the database
                cur.execute("INSERT OR REPLACE INTO QTable (state, action, value) VALUES (?, ?, ?)",
                            (self.old_state, str(self.old_state_action), new_q))
                conn.commit()


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


def gather_bids(players):
    for player in players:
        player.bid = player.make_bid()  # The AI's bidding logic


def play_tricks(players, round_number, db_path='q_table.db'):
    for _ in range(round_number):
        current_trick = []

        for player in players:
            player.is_trick_leader = False
            leading_suit = determine_leading_suit(current_trick)
            card_played = player.play_card(players, current_trick, leading_suit, db_path)
            current_trick.append((player, card_played))

        # Determine the winner of the trick
        winner = determine_winner(current_trick)
        bonus_points = determine_bonus_points(current_trick)
        if winner[0].tricks_taken < winner[0].bid:
            winner[0].update_q_value(5)
        if winner[0].tricks_taken == winner[0].bid and winner[0].bid == 0:
            winner[0].update_q_value(-10)
        if winner[0].tricks_taken >= winner[0].bid and winner[0].bid > 0:
            winner[0].update_q_value(-2)
        if bonus_points:
            winner[0].update_q_value(bonus_points/10)
        winner[0].tricks_taken += 1
        winner[0].bonus_points += bonus_points
        winner[0].is_trick_leader = True
        players = determine_turn_order(players)

        for player in players:
            player.max_future_q = None


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


def score_round(players, round_number, db_path='q_table'):
    for player in players:
        player.max_future_q = 0
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
        player.max_future_q = None


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


def play_round(players, round_number, db_path='q_table.db'):
    default_players = players
    deal_cards(players, round_number)
    gather_bids(players)
    players = determine_turn_order(players, round_number)
    play_tricks(players, round_number, db_path=db_path)
    players = default_players
    score_round(players, round_number)


# Function to plot data and a line of best fit
def plot_data_with_fit(data, title, degree=2):
    # Unzip the data into separate lists
    games, times = zip(*data)

    # Convert lists into numpy arrays for numerical operations
    games = np.array(games)
    times = np.array(times)

    # Create a scatter plot
    plt.figure(figsize=(10, 5))
    plt.scatter(games, times, color='b', label='Data Points')

    # Fit a line to the data
    p = np.poly1d(np.polyfit(games, times, 1))  # Polynomial of degree 1 (linear)

    # Plot the line of best fit
    plt.plot(games, p(games), 'r-', label=f'Line of Best Fit: {p}')

    # Add titles and labels
    plt.title(title)
    plt.xlabel('Game Number')
    plt.ylabel(title)
    plt.legend()

    # Save the plot to a file
    plt.savefig(f"{title}.png", format='png', dpi=300)  # Save as PNG with 300 DPI

    # Show the plot
    plt.show()


def run_game(players, game_number, db_path='q_table.db'):
    try:
        start_time = time.perf_counter()
        game_added_states = 0
        print(f'Game {game_number} has started')
        for round_number in range(1, 11):
            play_round(players, round_number, db_path=db_path)
        for player in players:
            game_added_states += player.added_states
        end_time = time.perf_counter()
        game_elapsed_time = end_time - start_time
        print(f"Game {game_number} took {game_elapsed_time} seconds and resulted in {game_added_states} new table entries")
        return [game_elapsed_time, game_added_states]

    except Exception as e:
        print(f"Exception in game {game_number}: {e}")
        traceback.print_exc()
        raise


def create_database(db_path='q_table.db'):
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    # Create a cursor object using the cursor() method
    cur = conn.cursor()
    # Create the table if it doesn't exist with the correct columns
    cur.execute('''
    CREATE TABLE IF NOT EXISTS QTable (
        state TEXT,
        action TEXT,
        value REAL,
        PRIMARY KEY (state, action)
    )
    ''')
    conn.commit()
    conn.close()


def initialize_database(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("PRAGMA journal_mode=WAL;")
    c.execute("PRAGMA synchronous=NORMAL;")  # NORMAL for faster execution, consider FULL for more data safety
    conn.commit()
    conn.close()


def ensure_state_exists(db_path, state_str, num_actions):
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        for i in range(num_actions):
            cur.execute('''
                INSERT OR IGNORE INTO QTable (state, action, value)
                VALUES (?, ?, 0)
            ''', (state_str, str(i),))
        conn.commit()


def fetch_q_values_for_actions(db_path, state_str, legal_actions):
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT action, value FROM QTable WHERE state=? AND action IN ({})
        '''.format(','.join('?'*len(legal_actions))), (state_str, *legal_actions))
        return {action: value for action, value in cur.fetchall()}


def upsert_qtable(state, action, value, db_path='q_table.db'):
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute('''
        INSERT OR REPLACE INTO QTable (state, action, value)
        VALUES (?, ?, ?)
        ''', (state, action, value))
        conn.commit()


# No need to determine winner for Q-table

if __name__ == "__main__":
    # Log time of game, cache hits based on hand size, size of dictionary at end of each game (how many entries gained in each game)
    game_elapsed_times = []
    game_new_states = []
    multiprocessing.set_start_method('spawn')
    create_database(db_path)
    initialize_database(db_path)
    players = [AIAgent("AI1"), AIAgent("AI2"), AIAgent("AI3"), AIAgent("AI4")]
    with ProcessPoolExecutor() as executor:
        # Submit all games to the executor
        future_to_session = {executor.submit(run_game, players, game, db_path): game for game in
                             range(1, games + 1)}

        for future in as_completed(future_to_session):
            game_number = future_to_session[future]
            try:
                result = future.result()
                # Adding a new tuple to each array
                game_elapsed_times.append((game_number, result[0]))
                game_new_states.append((game_number, result[1]))
            except Exception as exc:
                print(f"Game {game_number} generated an exception: {exc}")


    # Plotting the data
    plot_data_with_fit(game_elapsed_times, 'Elapsed Time')
    plot_data_with_fit(game_new_states, 'New States')
