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
    def __init__(self):
        self.deck = Deck()
        self.dealer_hand = []
        self.player_hands = [[]]  # List of hands (for splits)
        self.current_hand_index = 0
        self.player_balance = 50
        self.dealer_balance = 50
        self.current_bet = 5
        self.game_over = False
        self.message = "" # Keep for potential internal logic, but UI uses toasts
        self.dealer_turn_active = False # Track if it's dealer's turn for UI updates
        
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
            return [min(possible_values)], False
            
        return valid_values, True
    
    def get_hand_display_value(self, hand: List[Card]) -> str:
        values, is_valid = self.calculate_hand_value(hand)
        if not is_valid:
            return f"Bust ({values[0]})"
        if len(values) > 1:
            return f"Soft {values[0]}/{values[-1]}"
        return str(values[0])
    
    def deal_initial_cards(self):
        self.dealer_hand = [self.deck.deal(), self.deck.deal()]
        self.player_hands = [[self.deck.deal(), self.deck.deal()]]
        self.current_hand_index = 0
        self.game_over = False
        self.message = ""
        
    def hit(self):
        new_card = self.deck.deal()
        self.player_hands[self.current_hand_index].append(new_card)
        
        st.toast(f"Player draws: {new_card}", icon="🃏") # Show drawn card
        time.sleep(0.5) # Small delay

        values, is_valid = self.calculate_hand_value(self.player_hands[self.current_hand_index])
        
        # Use the minimum value for bust checking
        if min(values) > 21:
            self.message = f"Player busts with {min(values)}!"
            self.dealer_balance += self.current_bet
            self.player_balance -= self.current_bet
            self.game_over = True # End game immediately on bust
            
    def stand(self):
        # Old logic: 
        # self.dealer_play()
        # self.evaluate_winner()
        # New logic: Just signal that it's the dealer's turn
        self.dealer_turn_active = True
        # Rerun will be handled by the button callback

    def double_down(self):
        if len(self.player_hands[self.current_hand_index]) == 2:
            self.current_bet *= 2
            self.hit() # Player takes one card
            if not self.game_over: # Check if player busted
                # Don't call stand directly. Signal dealer's turn.
                # self.stand() # Automatically stands after hitting in double down
                self.dealer_turn_active = True 
                # Rerun will be handled by the button callback
                
    def split(self):
        if (len(self.player_hands[self.current_hand_index]) == 2 and 
            self.player_hands[self.current_hand_index][0].value == self.player_hands[self.current_hand_index][1].value):
            # Create new hand
            new_hand = [self.player_hands[self.current_hand_index].pop()]
            self.player_hands.append(new_hand)
            # Deal one card to each hand
            self.player_hands[self.current_hand_index].append(self.deck.deal())
            self.player_hands[-1].append(self.deck.deal())
            
    def dealer_play(self):
        # REMOVED: Indicate dealer's turn starts for UI update
        # self.dealer_turn_active = True
        # REMOVED: Rerun to show the revealed card immediately
        # st.rerun() 
        # REMOVED: Short pause AFTER rerun 
        # time.sleep(1)

        # --- Dealer hitting logic remains the same ---
        while True:
            values, is_valid = self.calculate_hand_value(self.dealer_hand)
            value_to_check = max(values) if is_valid else min(values)

            # Stand condition: valid value >= 17 OR already busted
            if not is_valid or value_to_check >= 17:
                if is_valid:
                    st.toast("Dealer stands.", icon="🛑")
                # Bust message will be handled by evaluate_winner or shown by total display
                break # Exit loop

            # Hit condition
            st.toast("Dealer hits...", icon="🃏")
            # Remove delay before drawing as UI won't update mid-loop
            # time.sleep(1) # Pause before drawing
            new_card = self.deck.deal()
            self.dealer_hand.append(new_card)
            st.toast(f"Dealer draws: {new_card}", icon="🃏") # Still show toast for info
            # REMOVE RERUN FROM INSIDE THE LOOP
            # st.rerun() # Rerun to update the UI with the new card
            # REMOVE SLEEP FROM INSIDE THE LOOP
            # time.sleep(1) # Pause after showing the new card and total

            # Check if dealer busted with the new card
            new_values, new_is_valid = self.calculate_hand_value(self.dealer_hand)
            if not new_is_valid:
                # Bust is implicitly shown by the total changing to "Bust (value)"
                # evaluate_winner will set the final game message
                break # Stop playing if dealer busts

        # Ensure dealer turn is marked as over AFTER playing is complete
        # This flag is now checked in the main script loop
        self.dealer_turn_active = False 
        # No need to rerun here, main script loop handles it via evaluate_winner

    def evaluate_winner(self):
        # Remove the check/call to dealer_play here - it happens before this now
        # if not self.game_over:
        #     pass 

        player_values, player_valid = self.calculate_hand_value(self.player_hands[self.current_hand_index])
        dealer_values, dealer_valid = self.calculate_hand_value(self.dealer_hand)

        player_value = max(player_values) if player_valid else min(player_values)
        dealer_value = max(dealer_values) if dealer_valid else min(dealer_values)

        result_message = ""
        # result_icon = "🏁" # Icon no longer needed for persistent message

        # Use message generated during player hit() if player busted
        if "busts" in self.message:
            result_message = self.message # Already set during hit()
            # result_icon = "💥"
            # Balance already adjusted in hit()
        elif not dealer_valid:
            result_message = f"Dealer busts with {dealer_value}! Player wins!"
            self.player_balance += self.current_bet
            self.dealer_balance -= self.current_bet
            # result_icon = "🎉"
        elif not player_valid: # Check again in case hit() logic changes
             result_message = f"Player busts with {player_value}! Dealer wins!"
             # Balance already adjusted in hit() if it happened there
             # If somehow bust happened without hit(), adjust here (less likely)
             if not self.game_over: # Avoid double adjustment
                 self.dealer_balance += self.current_bet
                 self.player_balance -= self.current_bet
             # result_icon = "👎"
        elif player_value > dealer_value:
            result_message = "Player wins!"
            self.player_balance += self.current_bet
            self.dealer_balance -= self.current_bet
            # result_icon = "🎉"
        elif dealer_value > player_value:
            result_message = "Dealer wins!"
            self.dealer_balance += self.current_bet
            self.player_balance -= self.current_bet
            # result_icon = "👎"
        else:
            result_message = "Push!"
            # result_icon = "🤝" # Icon no longer needed

        self.message = result_message # Update internal message state
        self.game_over = True
        self.dealer_turn_active = False # Ensure dealer turn is marked as over

        # REMOVE toast for result message
        # st.toast(result_message, icon=result_icon)
        st.rerun() # Rerun AFTER evaluation to update balances and trigger persistent message display

# Initialize session state
if 'game' not in st.session_state:
    st.session_state.game = BlackjackGame()
if 'player_count' not in st.session_state:
    st.session_state.player_count = 1
# Add dealer_turn_active initialization if game object is recreated
if not hasattr(st.session_state.game, 'dealer_turn_active'):
     st.session_state.game.dealer_turn_active = False

# Streamlit UI
st.title("Blackjack")

# Player count selection
player_count = st.radio("Number of Players", [1, 2], horizontal=True)
if player_count != st.session_state.player_count:
    st.session_state.player_count = player_count
    st.session_state.game = BlackjackGame()

# Display balances in styled containers
st.markdown('<div class="game-container">', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    st.markdown(f'<div class="balance-display">Player Balance: £{st.session_state.game.player_balance}</div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="balance-display">Dealer Balance: £{st.session_state.game.dealer_balance}</div>', unsafe_allow_html=True)

# Betting
bet = st.slider("Bet Amount", min_value=5, max_value=min(st.session_state.game.player_balance, st.session_state.game.dealer_balance), step=5)
st.session_state.game.current_bet = bet

# --- Display Persistent Game Result Message --- 
if st.session_state.game.game_over and st.session_state.game.message:
    message = st.session_state.game.message
    if "Player wins" in message or "Dealer busts" in message:
        st.success(message)
    elif "Dealer wins" in message or "Player busts" in message:
        st.error(message)
    else: # Push
        st.info(message)

# Game controls
if st.button("Deal New Hand", use_container_width=True):
    st.session_state.game.deal_initial_cards()
    st.session_state.game.game_over = False
    st.session_state.game.dealer_turn_active = False # Reset dealer turn state
    st.session_state.game.message = "" # Clear previous result message
    st.rerun() # Rerun to show the new hand and clear the message

# Display hands side-by-side
if st.session_state.game.dealer_hand: # Only display if a hand has been dealt
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Dealer's Hand")
        dealer_cards_html = '<div class="hand-container">'
        # Show only the first card unless game is over OR it's the dealer's turn
        show_dealer_full_hand = st.session_state.game.game_over or st.session_state.game.dealer_turn_active
        for i, card in enumerate(st.session_state.game.dealer_hand):
            if i == 0: # Always show the first card
                dealer_cards_html += f'<div class="card {card.get_color()}">{card.value}<br>{card.get_symbol()}</div>'
            elif show_dealer_full_hand: # Show the second card if game over or dealer's turn
                dealer_cards_html += f'<div class="card {card.get_color()}">{card.value}<br>{card.get_symbol()}</div>'
            else: # Otherwise, show a hidden card placeholder
                dealer_cards_html += f'<div class="card" style="background-color: grey; color: grey; display: flex; align-items: center; justify-content: center;">HIDDEN</div>'
        dealer_cards_html += '</div>'
        st.markdown(dealer_cards_html, unsafe_allow_html=True)
        
        # Display dealer total only if game is over or it's the dealer's turn
        if show_dealer_full_hand:
            st.markdown(f'<div class="hand-total">Dealer Total: {st.session_state.game.get_hand_display_value(st.session_state.game.dealer_hand)}</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("#### Player's Hand")
        player_cards_html = '<div class="hand-container">'
        for card in st.session_state.game.player_hands[st.session_state.game.current_hand_index]:
            player_cards_html += f'<div class="card {card.get_color()}">{card.value}<br>{card.get_symbol()}</div>'
        player_cards_html += '</div>'
        st.markdown(player_cards_html, unsafe_allow_html=True)
        st.markdown(f'<div class="hand-total">Player Total: {st.session_state.game.get_hand_display_value(st.session_state.game.player_hands[st.session_state.game.current_hand_index])}</div>', unsafe_allow_html=True)

    # Separator before action buttons
    st.markdown("---") 

    # Game actions (kept below the hands)
    if not st.session_state.game.game_over:
        cols_actions = st.columns(4)
        # Disable buttons if player cannot perform action
        can_hit_stand = not st.session_state.game.game_over
        can_double = can_hit_stand and len(st.session_state.game.player_hands[st.session_state.game.current_hand_index]) == 2 and st.session_state.game.player_balance >= st.session_state.game.current_bet * 2
        can_split = can_hit_stand and len(st.session_state.game.player_hands[st.session_state.game.current_hand_index]) == 2 and st.session_state.game.player_hands[st.session_state.game.current_hand_index][0].value == st.session_state.game.player_hands[st.session_state.game.current_hand_index][1].value and st.session_state.game.player_balance >= st.session_state.game.current_bet * 2 # Add balance check for split too

        with cols_actions[0]:
            if st.button("Hit", use_container_width=True, disabled=not can_hit_stand):
                st.session_state.game.hit()
                st.rerun() # Rerun to update UI immediately after hit/bust
        with cols_actions[1]:
            if st.button("Stand", use_container_width=True, disabled=not can_hit_stand):
                st.session_state.game.stand() # Calls the modified stand method
                st.rerun() # Rerun after setting the flag in stand()
        with cols_actions[2]:
            if st.button("Double Down", use_container_width=True, disabled=not can_double):
                st.session_state.game.double_down()
                st.rerun() # Rerun after setting the flag in double_down()
        with cols_actions[3]:
             # Note: Split functionality is basic
            if st.button("Split", use_container_width=True, disabled=not can_split):
                st.session_state.game.split()
                st.warning("Split logic is basic. Playing multiple hands is not fully implemented.")
                st.rerun()

# === Add Dealer Turn Logic Here ===
# Check if it's time for the dealer to play (triggered by Stand/Double Down + rerun)
if st.session_state.game.dealer_turn_active and not st.session_state.game.game_over:
    # Reveal dealer's hidden card visually BEFORE playing starts
    # This requires the UI to have access to dealer_turn_active state
    # which it already does. The initial rerun in stand()/double_down() handles showing the card.
    # Add a small pause after the reveal before the dealer hits rapidly.
    st.toast("Dealer reveals hidden card...", icon="👀")
    time.sleep(1.5) # Slightly longer pause for reveal

    st.session_state.game.dealer_play() # Dealer plays their hand fully
    # dealer_play now sets dealer_turn_active = False
    st.session_state.game.evaluate_winner() # Evaluate outcome immediately after
    # evaluate_winner handles the final rerun to show results

st.markdown('</div>', unsafe_allow_html=True) # Close game-container 
