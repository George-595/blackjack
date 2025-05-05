import streamlit as st
import random
from typing import List, Tuple, Dict
import time

# Custom CSS for styling
st.markdown("""
<style>
.card {
    background-color: white;
    border: 2px solid #ddd;
    border-radius: 10px;
    padding: 10px;
    margin: 5px;
    display: inline-block;
    width: 80px;
    height: 120px;
    text-align: center;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    transition: transform 0.3s ease-in-out; /* Animation for card reveal */
}
.card:hover {
    transform: scale(1.05);
}
.card.red {
    color: red;
}
.card.black {
    color: black;
}
.hand-container {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin: 10px 0;
    min-height: 140px; /* Ensure space for cards */
}
.game-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}
.balance-display {
    background-color: #f0f2f6;
    padding: 10px;
    border-radius: 5px;
    margin: 10px 0;
}
.hand-total {
    font-size: 1.2em;
    font-weight: bold;
    margin: 10px 0;
    padding: 5px 10px;
    background-color: #e9ecef;
    border-radius: 5px;
    display: inline-block;
}
</style>
""", unsafe_allow_html=True)

# Card class to represent individual cards
class Card:
    def __init__(self, suit: str, value: str):
        self.suit = suit
        self.value = value
        
    def __str__(self) -> str:
        return f"{self.value} of {self.suit}"
    
    def get_value(self) -> int:
        if self.value in ['J', 'Q', 'K']:
            return 10
        elif self.value == 'A':
            return 11
        else:
            return int(self.value)
            
    def get_color(self) -> str:
        return "red" if self.suit in ['Hearts', 'Diamonds'] else "black"
        
    def get_symbol(self) -> str:
        symbols = {
            'Hearts': '♥',
            'Diamonds': '♦',
            'Spades': '♠',
            'Clubs': '♣'
        }
        return symbols[self.suit]

# Deck class to manage the cards
class Deck:
    def __init__(self):
        self.suits = ['Hearts', 'Diamonds', 'Spades', 'Clubs']
        self.values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        self.num_decks = 6 # Define the number of decks
        self.cards = []
        self.reset_deck()
        
    def reset_deck(self):
        # Create cards for the specified number of decks
        self.cards = [Card(suit, value) for _ in range(self.num_decks) for suit in self.suits for value in self.values]
        self.shuffle()
        
    def shuffle(self):
        random.shuffle(self.cards)
        
    def deal(self) -> Card:
        if not self.cards:
            st.warning("Reshuffling the shoe...") # Inform user about reshuffle
            time.sleep(1) # Short pause for the message
            self.reset_deck()
        return self.cards.pop()

# Game class to manage the game state
class BlackjackGame:
    def __init__(self, num_players=1):
        self.num_players = num_players
        self.deck = Deck()
        self.dealer_hand: List[Card] = []
        self.player_hands: List[List[Card]] = [[] for _ in range(num_players)]
        self.player_balances: List[int] = [50] * num_players
        self.dealer_balance: int = 10000 # Give dealer a bit more starting balance
        self.player_bets: List[int] = [5] * num_players
        self.current_player_index: int = 0
        self.player_stand_flags: List[bool] = [False] * num_players
        self.player_bust_flags: List[bool] = [False] * num_players
        self.player_messages: List[str] = [""] * num_players
        self.game_over: bool = True # Start as game over until first deal
        self.dealer_turn_active: bool = False
        # Insurance state
        self.insurance_offered: bool = False
        self.player_insurance_bets: List[int] = [0] * num_players
        self.player_made_insurance_decision: List[bool] = [False] * num_players

    def calculate_hand_value(self, hand: List[Card]) -> Tuple[List[int], bool]:
        value = 0
        aces = 0
        
        # First pass: count aces and add up non-ace cards
        for card in hand:
            if card.value == 'A':
                aces += 1
            else:
                value += card.get_value()
        
        # Calculate all possible values
        possible_values = []
        if aces == 0:
            possible_values = [value]
        else:
            # Add all possible combinations of aces
            for i in range(aces + 1):
                possible_values.append(value + (i * 11) + ((aces - i) * 1))
        
        # Filter out values over 21 and sort
        valid_values = sorted([v for v in possible_values if v <= 21])
        
        if not valid_values:
            # Return the smallest value over 21 if busted
            return [min(possible_values)], False
            
        return valid_values, True

    def get_hand_display_value(self, hand: List[Card]) -> str:
        values, is_valid = self.calculate_hand_value(hand)
        if not is_valid:
            return f"Bust ({values[0]})"
        # Check for Blackjack (Ace + 10-value card on initial deal)
        if len(hand) == 2 and values[-1] == 21:
             # Check if it's truly an Ace and a 10-value card
             has_ace = any(c.value == 'A' for c in hand)
             has_ten = any(c.get_value() == 10 for c in hand)
             if has_ace and has_ten:
                 return "Blackjack!"
        # Soft total display (if highest value is <= 21 and uses Ace as 11)
        if len(values) > 1 and values[-1] <= 21 and any(c.value == 'A' for c in hand):
             # Check if using Ace as 1 makes it different
             non_soft_total = sum(c.get_value() if c.value != 'A' else 1 for c in hand)
             if values[-1] != non_soft_total: # Only show soft if Ace as 11 is used
                 return f"Soft {values[-1]}"
        # Default: show highest valid value or single value
        return str(values[-1] if values else "Error") # Should always have a value

    def deal_initial_cards(self):
        # Ensure deck has enough cards
        min_cards_needed = self.num_players * 2 + 2 + 10 # Players + Dealer + Buffer
        if len(self.deck.cards) < min_cards_needed:
            st.warning("Reshuffling shoe before new deal...")
            time.sleep(1)
            self.deck.reset_deck()
            
        self.dealer_hand = [self.deck.deal(), self.deck.deal()]
        self.player_hands = [[self.deck.deal(), self.deck.deal()] for _ in range(self.num_players)]
        self.current_player_index = 0
        self.player_stand_flags = [False] * self.num_players
        self.player_bust_flags = [False] * self.num_players
        self.player_messages = [""] * self.num_players
        self.game_over = False
        self.dealer_turn_active = False
        
        # Reset insurance state for new hand
        self.insurance_offered = False
        self.player_insurance_bets = [0] * self.num_players
        self.player_made_insurance_decision = [False] * self.num_players

        # Check dealer upcard for insurance offer condition
        dealer_upcard = self.dealer_hand[0] # The visible card
        offer_insurance_on_ace = dealer_upcard.value == 'A'
        offer_insurance_on_ten = dealer_upcard.get_value() == 10

        if offer_insurance_on_ace or offer_insurance_on_ten:
             self.insurance_offered = True
             st.toast(f"Dealer showing {dealer_upcard.value}. Insurance offered!", icon="❓")
             # Pause game flow - UI will show insurance options for player 0
             # Resolution will happen after player(s) choose
        else:
             # No insurance offered, proceed to check player BJs and advance turn
             self.check_player_blackjacks() # Check for player BJs vs non-BJ dealer
             if not self.game_over: # Only advance if BJ didn't end game
                  self.advance_turn(check_dealer_turn=False) # Start player 0 turn if no BJs

    def check_player_blackjacks(self):
        """Checks for player Blackjacks ONLY. Assumes dealer does NOT have BJ.
           Called after insurance is declined/resolved negatively, or if insurance wasn't offered.
        """
        all_players_done = True
        for i in range(self.num_players):
            if self.player_stand_flags[i] or self.player_bust_flags[i]:
                continue # Skip players already finished (e.g., from split if implemented)
                
            player_total_str = self.get_hand_display_value(self.player_hands[i])
            if player_total_str == "Blackjack!":
                self.player_stand_flags[i] = True # Player with BJ stands automatically
                # Since we assume dealer doesn't have BJ here, player BJ wins
                win_amount = int(self.player_bets[i] * 1.5)
                self.player_messages[i] = f"Player {i+1}: Blackjack! Wins £{win_amount}!"
                self.player_balances[i] += win_amount
                self.dealer_balance -= win_amount
                st.success(self.player_messages[i]) # Show immediate BJ win message
            else:
                all_players_done = False # At least one player needs to play

        # If all players had Blackjack, the game is over
        if all_players_done:
            self.game_over = True
            self.dealer_turn_active = False # No dealer turn needed

    def advance_turn(self, check_dealer_turn=True):
        """Moves to the next player or triggers the dealer's turn."""
        
        # Find the next player index who hasn't stood or busted
        next_player = self.current_player_index + 1
        while next_player < self.num_players and (self.player_stand_flags[next_player] or self.player_bust_flags[next_player]):
            next_player += 1

        if next_player < self.num_players:
            self.current_player_index = next_player
            st.toast(f"Player {self.current_player_index + 1}'s turn.", icon="👤")
        elif check_dealer_turn:
            # All players are done (stood or busted), check if dealer needs to play
            all_players_finished = all(self.player_stand_flags[i] or self.player_bust_flags[i] for i in range(self.num_players))
            if all_players_finished:
                any_player_active = any(not self.player_bust_flags[i] for i in range(self.num_players))
                if any_player_active:
                     st.toast("All players done. Dealer's turn!", icon="🤖")
                     self.dealer_turn_active = True # Signal dealer turn in main loop
                     # The main loop will handle the rerun and calling dealer_play
                else:
                     st.toast("All players busted!", icon="💥")
                     self.game_over = True # Evaluate happens naturally on rerun if all busted
                     # No need to call evaluate_winner here explicitly, state update is enough

    def hit(self):
        player_idx = self.current_player_index
        # Check if player is allowed to hit (shouldn't happen if UI is correct, but good practice)
        if self.player_stand_flags[player_idx] or self.player_bust_flags[player_idx]:
             st.warning(f"Player {player_idx + 1} cannot hit now.")
             return

        new_card = self.deck.deal()
        self.player_hands[player_idx].append(new_card)
        
        st.toast(f"Player {player_idx + 1} draws: {new_card}", icon="🃏") 
        # No sleep needed here, rerun will update UI
        time.sleep(1.0) # Add a pause to see the card drawn

        values, is_valid = self.calculate_hand_value(self.player_hands[player_idx])
        
        if not is_valid: # Player busts
            bust_value = min(values)
            self.player_messages[player_idx] = f"Player {player_idx + 1}: Busts with {bust_value}!"
            self.player_bust_flags[player_idx] = True
            self.player_stand_flags[player_idx] = True # Busting means they are done
            # Adjust balances immediately on bust
            self.dealer_balance += self.player_bets[player_idx]
            self.player_balances[player_idx] -= self.player_bets[player_idx]
            # Persistent message shown by main UI loop based on message
            self.advance_turn() # Move to next player or dealer
            
    def stand(self):
        player_idx = self.current_player_index
        # Check if player is allowed to stand
        if self.player_stand_flags[player_idx] or self.player_bust_flags[player_idx]:
             st.warning(f"Player {player_idx + 1} cannot stand now.")
             return
             
        st.toast(f"Player {player_idx + 1} stands.", icon="🛑")
        self.player_stand_flags[player_idx] = True
        self.advance_turn()
                
    def double_down(self):
        player_idx = self.current_player_index
        # Check conditions
        can_double = (
            len(self.player_hands[player_idx]) == 2 and
            self.player_balances[player_idx] >= self.player_bets[player_idx] * 2 and
            not self.player_stand_flags[player_idx] and 
            not self.player_bust_flags[player_idx]
        )

        if can_double:
            st.toast(f"Player {player_idx + 1} doubles down!", icon="💰")
            self.player_bets[player_idx] *= 2
            
            # Hit happens automatically
            new_card = self.deck.deal()
            self.player_hands[player_idx].append(new_card)
            st.toast(f"Player {player_idx + 1} draws: {new_card}", icon="🃏") 
            time.sleep(1.0) # Pause after double down hit

            values, is_valid = self.calculate_hand_value(self.player_hands[player_idx])
            self.player_stand_flags[player_idx] = True # Player is done after double down

            if not is_valid: # Player busts on double down
                bust_value = min(values)
                self.player_messages[player_idx] = f"Player {player_idx + 1}: Busts with {bust_value} on double down!"
                self.player_bust_flags[player_idx] = True
                # Adjust balances immediately
                self.dealer_balance += self.player_bets[player_idx]
                self.player_balances[player_idx] -= self.player_bets[player_idx]
                # Persistent message shown by main UI loop
            else:
                # Display final hand value via toast or rely on main UI update
                pass # st.toast(f"Player {player_idx + 1}'s final hand: {self.get_hand_display_value(self.player_hands[player_idx])}", icon="✅")
            
            self.advance_turn() # Move to next player or dealer
        else:
             st.warning(f"Player {player_idx + 1} cannot double down now.")
                
    def split(self):
        # SPLIT LOGIC NEEDS SIGNIFICANT REWORK FOR MULTIPLAYER & MULTI-HANDS PER PLAYER
        st.warning("Split functionality is complex and not implemented yet.")
            
    def dealer_play(self):
        # (No changes needed in the core hitting logic itself)
        # --- Dealer hitting logic remains the same ---
        while True:
            values, is_valid = self.calculate_hand_value(self.dealer_hand)
            
            # Determine the value to check (highest valid, or minimum if bust)
            value_to_check = 0
            if is_valid:
                 value_to_check = values[-1] # Highest valid value
            else:
                 value_to_check = min(values) # Minimum bust value
            
            # Dealer stand conditions: hard 17+, soft 18+, or bust
            is_soft = len(values) > 1 and values[-1] <= 21 # Check if current total is soft
            
            # Stand on soft 18 or higher, hard 17 or higher, or if busted
            if not is_valid or value_to_check >= 18 or (value_to_check == 17 and not is_soft): 
                if is_valid:
                    st.toast(f"Dealer stands on {self.get_hand_display_value(self.dealer_hand)}.", icon="🛑")
                # Bust message handled by evaluate_winner or total display
                break # Exit loop

            # Hit condition (soft 17 or less)
            st.toast("Dealer hits...", icon="🃏")
            # time.sleep(1) # Optional short delay between dealer hits
            new_card = self.deck.deal()
            self.dealer_hand.append(new_card)
            st.toast(f"Dealer draws: {new_card}", icon="🃏") # Still show toast for info
            time.sleep(1.0) # Pause after dealer draws

            # Check if dealer busted with the new card - loop condition handles this
            new_values, new_is_valid = self.calculate_hand_value(self.dealer_hand)
            if not new_is_valid:
                # Bust is implicitly shown by the total changing to "Bust (value)"
                # evaluate_winner will set the final game message
                break # Stop playing if dealer busts

        # Don't set dealer_turn_active = False here, evaluate_winner does it.
        # No need to rerun here, main script loop handles it via evaluate_winner

    def evaluate_winner(self):
        # Dealer should have finished playing before this is called
        
        dealer_values, dealer_valid = self.calculate_hand_value(self.dealer_hand)
        dealer_value = 0
        dealer_display_value = self.get_hand_display_value(self.dealer_hand) # Get final string representation
        if dealer_valid:
            dealer_value = dealer_values[-1]
        elif dealer_values: # Check if list is not empty even if not valid
             dealer_value = min(dealer_values)
        else: # Should not happen with dealer logic, but fallback
             dealer_value = 99 # Bust value

        # Evaluate each player vs dealer
        for player_idx in range(self.num_players):
            # Skip players who already busted (message/balance handled previously)
            if self.player_bust_flags[player_idx]:
                continue
                
            # Skip players who got Blackjack (already paid)
            if "Blackjack!" in self.player_messages[player_idx]:
                 continue

            player_values, player_valid = self.calculate_hand_value(self.player_hands[player_idx])
            # Player should be valid if not busted, get highest value
            player_value = player_values[-1] if player_valid else 0 # Should be > 0 if valid

            bet = self.player_bets[player_idx]
            result_message = f"Player {player_idx + 1}: "
            player_display = self.get_hand_display_value(self.player_hands[player_idx])

            if not dealer_valid:
                result_message += f"Wins £{bet}! Dealer busts ({dealer_display_value})."
                self.player_balances[player_idx] += bet
                self.dealer_balance -= bet
            elif player_value > dealer_value:
                result_message += f"Wins £{bet}! ({player_display} vs {dealer_display_value})"
                self.player_balances[player_idx] += bet
                self.dealer_balance -= bet
            elif dealer_value > player_value:
                result_message += f"Loses £{bet}. ({player_display} vs {dealer_display_value})"
                self.dealer_balance += bet
                self.player_balances[player_idx] -= bet
            else: # Push
                result_message += f"Push! ({player_display})"
                # No balance change

            self.player_messages[player_idx] = result_message

        self.game_over = True
        self.dealer_turn_active = False 
        # Don't rerun here, let the main loop handle the final display update
        # st.rerun() 

    def take_insurance(self):
        player_idx = self.current_player_index
        if not self.insurance_offered or self.player_made_insurance_decision[player_idx]:
            return # Should not happen via UI, but safe check

        insurance_cost = self.player_bets[player_idx] // 2 # Integer division
        if self.player_balances[player_idx] < insurance_cost:
             st.warning(f"Player {player_idx + 1}: Not enough balance (£{self.player_balances[player_idx]}) for insurance (£{insurance_cost}).")
             # Automatically decline if insufficient funds?
             self.decline_insurance()
             return
        
        self.player_insurance_bets[player_idx] = insurance_cost
        self.player_made_insurance_decision[player_idx] = True
        st.toast(f"Player {player_idx + 1} takes insurance (£{insurance_cost}).", icon="🛡️")
        self.advance_insurance_decision()

    def decline_insurance(self):
        player_idx = self.current_player_index
        if not self.insurance_offered or self.player_made_insurance_decision[player_idx]:
            return
        
        self.player_insurance_bets[player_idx] = 0
        self.player_made_insurance_decision[player_idx] = True
        st.toast(f"Player {player_idx + 1} declines insurance.", icon="❌")
        self.advance_insurance_decision()

    def advance_insurance_decision(self):
        """Moves to the next player needing to decide on insurance, or resolves insurance if all decided."""
        next_player_needs_decision = -1
        for i in range(self.current_player_index + 1, self.num_players):
            if not self.player_made_insurance_decision[i]:
                 next_player_needs_decision = i
                 break
        
        if next_player_needs_decision != -1:
             self.current_player_index = next_player_needs_decision
             st.toast(f"Player {self.current_player_index + 1}: Take or decline insurance?", icon="❓")
             # UI needs to update for this player
        else:
            # All players have made their insurance decision
            st.toast("All insurance decisions made. Checking dealer's hole card...", icon="👀")
            time.sleep(1) # Pause for effect
            self.resolve_insurance()

    def resolve_insurance(self):
        """Checks dealer BJ and settles insurance bets. Then proceeds with game."""
        dealer_has_blackjack = self.get_hand_display_value(self.dealer_hand) == "Blackjack!"

        if dealer_has_blackjack:
            st.warning("Dealer Blackjack!")
            self.dealer_turn_active = True # Reveal dealer's hand
            for i in range(self.num_players):
                insurance_bet = self.player_insurance_bets[i]
                player_bet = self.player_bets[i]
                player_bj = self.get_hand_display_value(self.player_hands[i]) == "Blackjack!"
                message = f"Player {i+1}: "
                
                # Settle insurance bet
                if insurance_bet > 0:
                     payout = insurance_bet * 2
                     self.player_balances[i] += payout 
                     self.dealer_balance -= payout
                     message += f"Wins £{payout} insurance. "
                
                # Settle original bet (vs Dealer BJ)
                if player_bj:
                    message += "Pushes original bet (both Blackjack)."
                    # No change to balance for original bet
                else:
                    message += f"Loses original bet (£{player_bet})."
                    self.player_balances[i] -= player_bet
                    self.dealer_balance += player_bet
                
                self.player_messages[i] = message
                self.player_stand_flags[i] = True # Hand is over
            
            self.game_over = True
            self.insurance_offered = False # Insurance phase is done

        else: # Dealer does NOT have Blackjack
             st.info("Dealer does not have Blackjack.")
             losing_insurance_total = 0
             for i in range(self.num_players):
                 insurance_bet = self.player_insurance_bets[i]
                 if insurance_bet > 0:
                     self.player_balances[i] -= insurance_bet
                     self.dealer_balance += insurance_bet
                     losing_insurance_total += insurance_bet
                     # Add note to message or use toast?
                     st.error(f"Player {i+1} loses £{insurance_bet} insurance bet.", icon="💸") # Use error toast for losing money
             
             self.insurance_offered = False # Insurance phase over
             # Now proceed with checking for player Blackjacks (since dealer didn't have one)
             self.check_player_blackjacks()
             # If game didn't end due to all players having BJ, advance turn normally
             if not self.game_over:
                 self.advance_turn(check_dealer_turn=False)

    def reset_game_state(self):
        """Resets the entire game state to initial values, including balances and deck."""
        st.toast("Resetting game state...", icon="🔄")
        self.deck = Deck() # Reset and reshuffle the deck
        self.dealer_hand: List[Card] = []
        self.player_hands: List[List[Card]] = [[] for _ in range(self.num_players)]
        self.player_balances: List[int] = [50] * self.num_players
        self.dealer_balance: int = 10000
        self.player_bets: List[int] = [5] * self.num_players
        self.current_player_index: int = 0
        self.player_stand_flags: List[bool] = [False] * self.num_players
        self.player_bust_flags: List[bool] = [False] * self.num_players
        self.player_messages: List[str] = [""] * self.num_players
        self.game_over: bool = True # Game is over after reset, ready for new deal
        self.dealer_turn_active: bool = False
        self.insurance_offered: bool = False
        self.player_insurance_bets: List[int] = [0] * self.num_players
        self.player_made_insurance_decision: List[bool] = [False] * self.num_players
        # Give a small delay for the toast message to be seen
        time.sleep(0.5)

# Initialize session state
if 'game' not in st.session_state:
    # Initialize with default player count (will be updated by radio button)
    st.session_state.game = BlackjackGame(num_players=st.session_state.get('player_count', 1))
if 'player_count' not in st.session_state:
    st.session_state.player_count = 1

# Ensure game object matches selected player count 
# This runs every time the script reruns
if st.session_state.game.num_players != st.session_state.player_count:
    # Only recreate if the game isn't currently in progress or just finished
    # Avoid resetting mid-hand if player count is accidentally changed
    if st.session_state.game.game_over:
        st.session_state.game = BlackjackGame(num_players=st.session_state.player_count)
        st.info(f"Game ready for {st.session_state.player_count} players.")
        # Force rerun to ensure UI elements use the new game object correctly
        st.rerun() 
    else:
        # If game is in progress, revert the player_count selection to match the game
        st.session_state.player_count = st.session_state.game.num_players
        st.warning("Cannot change player count during an active game.")

# Streamlit UI
st.title("Blackjack")

# Player count selection
# Use a key to help preserve state across reruns
player_count_selection = st.radio(
    "Number of Players", 
    [1, 2], 
    index=st.session_state.player_count - 1, 
    horizontal=True, 
    key="player_count_selector",
    disabled=not st.session_state.game.game_over # Disable if game is active
)

# Update player count in state ONLY if it changed AND the game is over
if player_count_selection != st.session_state.player_count and st.session_state.game.game_over:
    st.session_state.player_count = player_count_selection
    # The logic at the start of the UI section will handle recreating the game object on the next rerun
    st.rerun() # Rerun immediately to update game object and UI

st.markdown('<div class="game-container">', unsafe_allow_html=True)

# --- Player Balances Row ---
st.subheader("Balances")
num_balance_cols = st.session_state.player_count + 1 # Players + Dealer
balance_cols = st.columns(num_balance_cols)
for i in range(st.session_state.player_count):
    with balance_cols[i]:
        st.markdown(f'<div class="balance-display">Player {i+1}: £{st.session_state.game.player_balances[i]}</div>', unsafe_allow_html=True)
with balance_cols[st.session_state.player_count]:
    st.markdown(f'<div class="balance-display">Dealer: £{st.session_state.game.dealer_balance}</div>', unsafe_allow_html=True)

# --- Betting Section --- 
st.subheader("Place Your Bets")
# Disable betting if game is in progress OR insurance phase is active
betting_disabled = not st.session_state.game.game_over or st.session_state.game.insurance_offered

# Use columns for betting sliders
bet_cols = st.columns(st.session_state.player_count)

for i in range(st.session_state.player_count):
    with bet_cols[i]:
        min_bet = 5
        # Ensure max_bet doesn't exceed player balance or dealer balance (simplified ceiling)
        max_bet_possible = min(st.session_state.game.player_balances[i], st.session_state.game.dealer_balance, 100) # Cap max bet reasonably
        
        # Display bet amount or message if unable to bet
        if st.session_state.game.player_balances[i] < min_bet:
             st.session_state.game.player_bets[i] = 0 # Player can't bet
             st.write(f"**Player {i+1}**")
             st.caption(f"Insufficient balance (£{st.session_state.game.player_balances[i]}) for min bet (£{min_bet}).")
        else:
             # Ensure the default/current value is within allowed range
             current_bet_value = st.session_state.game.player_bets[i]
             clamped_bet_value = max(min_bet, min(current_bet_value, max_bet_possible))
             
             # Store clamped value back if betting is enabled, otherwise just display stored value
             if not betting_disabled:
                 st.session_state.game.player_bets[i] = clamped_bet_value

             new_bet = st.slider(f"Player {i+1} Bet", 
                                 min_value=min_bet, 
                                 max_value=max_bet_possible, 
                                 value=clamped_bet_value,
                                 step=5, 
                                 key=f"bet_slider_{i}",
                                 disabled=betting_disabled)
             # Update the bet in session state if slider is changed and not disabled
             if not betting_disabled and new_bet != clamped_bet_value:
                 st.session_state.game.player_bets[i] = new_bet
                 # No rerun needed here, value updates on next script run

# --- Display Persistent Game Result Messages --- 
# Show messages only when game is over and not in insurance phase
if st.session_state.game.game_over and not st.session_state.game.insurance_offered:
    result_cols = st.columns(st.session_state.player_count)
    for i in range(st.session_state.player_count):
         with result_cols[i]:
             message = st.session_state.game.player_messages[i]
             if message:
                 if "Wins" in message or "Dealer busts" in message or "insurance" in message: # Include insurance wins
                     st.success(message)
                 elif "Loses" in message or "busts" in message:
                     st.error(message)
                 elif "Push" in message:
                     st.info(message)
                 else: # Fallback for other messages if any
                     st.write(message)

# --- Game Control Buttons --- 

# Create columns for Deal and Reset buttons
control_cols = st.columns(2)

with control_cols[0]:
    # Deal New Hand Button (only visible when game is over)
    if st.session_state.game.game_over and not st.session_state.game.insurance_offered:
        # Check if any player cannot afford the minimum bet
        can_any_player_bet = any(st.session_state.game.player_balances[i] >= 5 for i in range(st.session_state.player_count))
        can_dealer_afford = st.session_state.game.dealer_balance >= 5
        deal_enabled = can_any_player_bet and can_dealer_afford

        if st.button("Deal New Hand", use_container_width=True, disabled=not deal_enabled, key="deal_button"):
            # Bets are already set by sliders, deal_initial_cards will use them
            st.session_state.game.deal_initial_cards()
            st.rerun() # Rerun to show the new hand / insurance phase

        if not deal_enabled and st.session_state.game.game_over:
            st.warning("Cannot deal. Check player/dealer min balances.")

with control_cols[1]:
    # Reset Game Button (Always visible? Or only when game over? Let's make it always visible for now)
    if st.button("Reset Game", use_container_width=True, key="reset_button"):
        st.session_state.game.reset_game_state()
        st.rerun()

# --- Hand Display Area (Shows after first deal) ---
# Display this section if cards have been dealt (dealer hand exists)
if st.session_state.game.dealer_hand:
    
    game = st.session_state.game # Alias for shorter access
    num_game_cols = game.num_players + 1 # One for dealer, one for each player
    game_cols = st.columns(num_game_cols)
    current_player_idx = game.current_player_index
    
    # --- Dealer Hand (in the first column) ---
    with game_cols[0]:
        st.markdown("#### Dealer's Hand")
        dealer_cards_html = '<div class="hand-container">'
        # Show full hand if the game is over OR the dealer's turn is active
        show_dealer_full_hand = game.game_over or game.dealer_turn_active
        # (Insurance resolution implicitly sets game_over if dealer has BJ, or allows play to continue)

        for i, card in enumerate(game.dealer_hand):
            if i == 0: # Always show the first card
                dealer_cards_html += f'<div class="card {card.get_color()}">{card.value}<br>{card.get_symbol()}</div>'
            elif show_dealer_full_hand: # Show the second card if needed
                dealer_cards_html += f'<div class="card {card.get_color()}">{card.value}<br>{card.get_symbol()}</div>'
            else: # Otherwise, show a hidden card placeholder
                dealer_cards_html += f'<div class="card" style="background-color: grey; color: grey; display: flex; align-items: center; justify-content: center;">HIDDEN</div>'
        dealer_cards_html += '</div>'
        st.markdown(dealer_cards_html, unsafe_allow_html=True)
        
        # Display dealer total only if hole card should be shown
        if show_dealer_full_hand:
            st.markdown(f'<div class="hand-total">Dealer Total: {game.get_hand_display_value(game.dealer_hand)}</div>', unsafe_allow_html=True)

    # st.markdown("---") # Separator - Remove this as columns handle separation

    # --- Player Hands & Actions (in subsequent columns) --- 
    # player_cols = st.columns(st.session_state.player_count) # Remove this, use game_cols
    # current_player_idx = st.session_state.game.current_player_index # Already defined
    # game = st.session_state.game # Already defined

    for i in range(game.num_players):
        with game_cols[i + 1]: # Start from the second column (index 1)
            # Highlight current player during play phase OR during insurance phase
            is_player_active = (not game.player_stand_flags[i] and not game.player_bust_flags[i])
            is_regular_turn = (i == current_player_idx and is_player_active and not game.dealer_turn_active and not game.insurance_offered)
            is_insurance_decision_turn = (i == current_player_idx and is_player_active and game.insurance_offered and not game.player_made_insurance_decision[i])
            
            is_current_turn = is_regular_turn or is_insurance_decision_turn
                                 
            border_style = "border: 3px solid #007bff; border-radius: 10px; padding: 10px; margin-bottom: 10px;" if is_current_turn else "border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin-bottom: 10px;"
            st.markdown(f'<div style="{border_style}">', unsafe_allow_html=True) # Corrected markdown start tag
            st.markdown(f"##### Player {i+1} (Bet: £{game.player_bets[i]})")

            # Display Hand
            player_cards_html = '<div class="hand-container">'
            for card in game.player_hands[i]:
                player_cards_html += f'<div class="card {card.get_color()}">{card.value}<br>{card.get_symbol()}</div>'
            player_cards_html += '</div>'
            st.markdown(player_cards_html, unsafe_allow_html=True)
            st.markdown(f'<div class="hand-total">Total: {game.get_hand_display_value(game.player_hands[i])}</div>', unsafe_allow_html=True)

            # Display Player Status (Busted/Stood/Blackjack)
            if game.player_bust_flags[i]:
                st.error("BUSTED")
            elif "Blackjack!" in game.player_messages[i] and "Push" not in game.player_messages[i]: # Check if message indicates BJ win
                 st.success("BLACKJACK!")
            elif game.player_stand_flags[i]: # Includes players who stood or got non-winning BJ
                st.info("Finished") # More neutral term than STOOD

            # --- Action Buttons Logic ---
            # Buttons are only shown for the player whose turn it is
            if is_current_turn:
                # Display whose turn it is
                if game.num_players == 1:
                    st.markdown("**Your Go**")
                else:
                    st.markdown(f"**Player {i+1}'s Turn**")

                # === Insurance Phase Buttons ===
                if game.insurance_offered and not game.player_made_insurance_decision[i]:
                    st.markdown("**Insurance?**")
                    max_insurance = game.player_bets[i] // 2
                    can_afford_insurance = game.player_balances[i] >= max_insurance
                    
                    # Use columns for insurance buttons for better layout
                    ins_cols = st.columns(2)
                    with ins_cols[0]:
                        if st.button(f"Take (£{max_insurance})", use_container_width=True, disabled=not can_afford_insurance, key=f"ins_take_{i}"):
                            game.take_insurance()
                            st.rerun()
                    with ins_cols[1]:
                         if st.button("Decline", use_container_width=True, key=f"ins_decline_{i}"):
                             game.decline_insurance()
                             st.rerun()
                    if not can_afford_insurance and max_insurance > 0:
                         st.caption(f"(Needs £{max_insurance})", help=f"Balance: £{game.player_balances[i]}")
                    elif max_insurance <= 0:
                         st.caption("(Min bet needed)", help="Insurance requires a base bet.")
                
                # === Regular Play Phase Buttons ===
                elif not game.insurance_offered: # Only show play buttons if insurance wasn't offered or is resolved
                    action_cols = st.columns(4)
                    current_hand = game.player_hands[i]
                    current_balance = game.player_balances[i]
                    current_bet = game.player_bets[i] # Original bet before double

                    # Check conditions based on current state
                    can_hit_stand = not game.player_stand_flags[i] and not game.player_bust_flags[i]
                    can_double = can_hit_stand and len(current_hand) == 2 and current_balance >= current_bet # Check balance vs original bet for doubling cost
                    can_split = False # Disabled for now
                    # can_split = (can_hit_stand and len(current_hand) == 2 and 
                    #              current_hand[0].value == current_hand[1].value and 
                    #              current_balance >= current_bet) # Check balance vs original bet

                    with action_cols[0]:
                        if st.button("Hit", use_container_width=True, disabled=not can_hit_stand, key=f"hit_{i}"):
                            game.hit()
                            st.rerun() 
                    with action_cols[1]:
                        if st.button("Stand", use_container_width=True, disabled=not can_hit_stand, key=f"stand_{i}"):
                            game.stand() 
                            st.rerun() 
                    with action_cols[2]:
                        if st.button("Double Down", use_container_width=True, disabled=not can_double, key=f"double_{i}"):
                            # Double down cost is the original bet amount again
                            if game.player_balances[i] < game.player_bets[i]:
                                 st.warning(f"Need £{game.player_bets[i]} more to double.")
                            else:
                                 game.double_down()
                                 st.rerun() 
                    with action_cols[3]:
                        if st.button("Split", use_container_width=True, disabled=True, key=f"split_{i}"):
                            # game.split() # Call commented out
                            st.warning("Split not implemented.")
                            # st.rerun() # No rerun needed if action does nothing
                            
            st.markdown('</div>' , unsafe_allow_html=True) # Close player highlight div

# --- Dealer Turn Logic (Keep at the end) --- 
# Check if it's time for the dealer to play (flag set by advance_turn)
if st.session_state.game.dealer_turn_active and not st.session_state.game.game_over:
    # Add a small delay for user experience
    st.toast("Dealer playing...", icon="🤖")
    time.sleep(1.5) 

    st.session_state.game.dealer_play() # Dealer plays their hand fully
    # Dealer play might bust, evaluate_winner handles all outcomes
    st.session_state.game.evaluate_winner() # Evaluate outcome immediately after dealer plays
    st.rerun() # Rerun to show final results and game over state

st.markdown('</div>', unsafe_allow_html=True) # Close game-container 
