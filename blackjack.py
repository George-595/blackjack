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
        # Player state now tracks multiple hands per player
        # Outer list: Players, Inner list: Hands for that player
        self.player_hands: List[List[List[Card]]] = [[[]] for _ in range(num_players)]
        self.player_balances: List[int] = [50] * num_players
        self.dealer_balance: int = 10000
        self.player_bets: List[List[int]] = [[5] for _ in range(num_players)] # Bet per hand
        self.player_stand_flags: List[List[bool]] = [[False] for _ in range(num_players)] # Stand flag per hand
        self.player_bust_flags: List[List[bool]] = [[False] for _ in range(num_players)] # Bust flag per hand
        self.current_player_index: int = 0
        self.current_hand_indices: List[int] = [0] * num_players # Tracks active hand index for each player
        self.player_split_flags: List[bool] = [False] * num_players # Tracks if player has split this round
        self.player_messages: List[str] = [""] * num_players # Overall message per player for now
        self.game_over: bool = True
        self.dealer_turn_active: bool = False
        # Insurance state (remains per player)
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
        # Read the bets placed before dealing
        initial_bets = [st.session_state.game.player_bets[i][0] for i in range(self.num_players)]
        
        # Ensure deck has enough cards
        min_cards_needed = self.num_players * 2 + 2 + 10 # Players + Dealer + Buffer
        if len(self.deck.cards) < min_cards_needed:
            st.warning("Reshuffling shoe before new deal...")
            time.sleep(1)
            self.deck.reset_deck()

        # Reset player hand structures for the new round
        self.player_hands = [[[]] for _ in range(self.num_players)]
        self.player_bets = [[bet] for bet in initial_bets] # Use the bets placed
        self.player_stand_flags = [[False] for _ in range(self.num_players)]
        self.player_bust_flags = [[False] for _ in range(self.num_players)]
        self.current_hand_indices = [0] * self.num_players # Start at the first hand
        self.player_split_flags = [False] * self.num_players # Reset split status
        self.player_messages = [""] * self.num_players # Clear previous messages

        # Deal cards
        self.dealer_hand = [self.deck.deal(), self.deck.deal()]
        for i in range(self.num_players):
            self.player_hands[i][0] = [self.deck.deal(), self.deck.deal()]
            
        self.current_player_index = 0
        self.game_over = False
        self.dealer_turn_active = False
        
        # Reset insurance state for new hand
        self.insurance_offered = False
        self.player_insurance_bets = [0] * self.num_players
        self.player_made_insurance_decision = [False] * self.num_players

        # Check dealer upcard for insurance offer condition
        dealer_upcard = self.dealer_hand[0] # The visible card
        offer_insurance_on_ace = dealer_upcard.value == 'A'

        if offer_insurance_on_ace: # Only offer insurance if dealer shows Ace
             self.insurance_offered = True
             st.toast(f"Dealer showing Ace. Insurance offered!", icon="❓")
             self.current_player_index = 0 # Start insurance decisions from player 0
        else:
             # No insurance offered, check player BJs (on their initial hand) and set the first turn
             self.check_player_blackjacks() # Checks hand [0]
             
             if not self.game_over: 
                  # Find the first player who needs to play (hasn't stood/busted/got BJ on hand 0)
                  first_playable_player = -1
                  for i in range(self.num_players):
                       # Check flags for the first hand
                       if not self.player_stand_flags[i][0] and not self.player_bust_flags[i][0]:
                           first_playable_player = i
                           break 
                  
                  if first_playable_player != -1:
                      self.current_player_index = first_playable_player
                  else:
                      # All players finished immediately (e.g., all got Blackjack on hand 0)
                      all_players_finished = all(self.player_stand_flags[i][0] or self.player_bust_flags[i][0] for i in range(self.num_players))
                      if all_players_finished:
                          any_player_active = any(not self.player_bust_flags[i][0] for i in range(self.num_players))
                          if any_player_active:
                              st.toast("Dealer's turn!", icon="🤖")
                              self.dealer_turn_active = True
                          else:
                              if not self.game_over: 
                                   st.toast("All players finished.", icon="🏁") 
                                   self.game_over = True

    def check_player_blackjacks(self):
        """Checks for player Blackjacks ONLY. Assumes dealer does NOT have BJ.
           Called after insurance is declined/resolved negatively, or if insurance wasn't offered.
        """
        all_players_done = True
        for i in range(self.num_players):
            if self.player_stand_flags[i][0] or self.player_bust_flags[i][0]:
                continue # Skip players already finished (e.g., from split if implemented)
                
            player_total_str = self.get_hand_display_value(self.player_hands[i][0])
            if player_total_str == "Blackjack!":
                self.player_stand_flags[i][0] = True # Player with BJ stands automatically
                # Since we assume dealer doesn't have BJ here, player BJ wins
                win_amount = int(self.player_bets[i][0] * 1.5)
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
        """Moves to the next playable hand for the current player, or to the next player, or triggers the dealer's turn."""
        player_idx = self.current_player_index
        current_hand_idx = self.current_hand_indices[player_idx]

        # 1. Check if the current player has more hands to play
        next_hand_idx = current_hand_idx + 1
        if next_hand_idx < len(self.player_hands[player_idx]):
            # Move to the next hand for the current player
            self.current_hand_indices[player_idx] = next_hand_idx
            st.toast(f"Player {player_idx + 1}: Now playing Hand {next_hand_idx + 1}", icon="✋")
            # Rerun needed to update UI for the next hand of the same player
            # The button click that triggered advance_turn should handle the rerun
            return # Stay on the same player

        # 2. Current player is finished with all hands. Find the next player.
        next_player_idx = player_idx + 1
        found_next_player = False
        while next_player_idx < self.num_players:
            # Check if this next player has any hands that still need playing
            next_player_has_playable_hand = False
            first_playable_hand_idx = -1
            for hand_i in range(len(self.player_hands[next_player_idx])):
                if not self.player_stand_flags[next_player_idx][hand_i] and not self.player_bust_flags[next_player_idx][hand_i]:
                    next_player_has_playable_hand = True
                    first_playable_hand_idx = hand_i
                    break # Found a playable hand for this player
            
            if next_player_has_playable_hand:
                self.current_player_index = next_player_idx
                self.current_hand_indices[next_player_idx] = first_playable_hand_idx
                st.toast(f"Player {self.current_player_index + 1}'s turn (Hand {first_playable_hand_idx + 1}).", icon="👤")
                found_next_player = True
                # Rerun needed for UI update
                return # Moved to the next player
            
            # If this player had no playable hands, check the next one
            next_player_idx += 1 

        # 3. No subsequent player found with playable hands.
        if not found_next_player and check_dealer_turn:
            # Check if *any* hand across *any* player is still active (not busted)
            # If so, it's the dealer's turn. Otherwise, the game might be over.
            all_hands_finished = True
            any_hand_active_not_busted = False
            for p_idx in range(self.num_players):
                for h_idx in range(len(self.player_hands[p_idx])):
                    is_busted = self.player_bust_flags[p_idx][h_idx]
                    is_stood = self.player_stand_flags[p_idx][h_idx]
                    if not is_busted and not is_stood: # Found a hand that's still playing (shouldn't happen if logic is correct)
                        all_hands_finished = False
                        # This case indicates an error in state transition, potentially log it.
                        # For robustness, maybe try to find this player/hand again? Or force dealer turn? Let's assume it won't happen for now.
                        break 
                    if not is_busted: # Found a hand that finished without busting
                        any_hand_active_not_busted = True
                if not all_hands_finished: break # Optimization
            
            if not all_hands_finished:
                 # This should ideally not be reached if hit/stand/split logic is correct
                 st.error("Error: Found unfinished hand when advancing turn. Forcing dealer turn.")
                 self.dealer_turn_active = True
            elif any_hand_active_not_busted:
                 # At least one player hand finished without busting, dealer needs to play
                 st.toast("All players done. Dealer's turn!", icon="🤖")
                 self.dealer_turn_active = True # Signal dealer turn in main loop
            else:
                 # All player hands busted out
                 st.toast("All players busted!", icon="💥")
                 self.game_over = True # Evaluate happens naturally via evaluate_winner if needed, or just game over
                 self.dealer_turn_active = False
            
            # Rerun needed for UI update (dealer turn or game over)

    def hit(self):
        player_idx = self.current_player_index
        hand_idx = self.current_hand_indices[player_idx]
        
        # Check if player is allowed to hit this hand
        if self.player_stand_flags[player_idx][hand_idx] or self.player_bust_flags[player_idx][hand_idx]:
             st.warning(f"Player {player_idx + 1} Hand {hand_idx + 1} cannot hit now.")
             return

        new_card = self.deck.deal()
        self.player_hands[player_idx][hand_idx].append(new_card)
        
        st.toast(f"Player {player_idx + 1} Hand {hand_idx + 1} draws: {new_card}", icon="🃏") 
        time.sleep(1.0) 

        values, is_valid = self.calculate_hand_value(self.player_hands[player_idx][hand_idx])
        
        if not is_valid: # Player busts on this hand
            bust_value = min(values)
            # Update message for this specific hand? For now, keep general player message.
            self.player_messages[player_idx] = f"Player {player_idx + 1} Hand {hand_idx + 1}: Busts with {bust_value}!"
            self.player_bust_flags[player_idx][hand_idx] = True
            self.player_stand_flags[player_idx][hand_idx] = True # Busting means they are done with this hand
            # Adjust balances immediately on bust
            self.dealer_balance += self.player_bets[player_idx][hand_idx]
            self.player_balances[player_idx] -= self.player_bets[player_idx][hand_idx]
            self.advance_turn() # Move to next hand/player
            
    def stand(self):
        player_idx = self.current_player_index
        hand_idx = self.current_hand_indices[player_idx]

        # Check if player is allowed to stand this hand
        if self.player_stand_flags[player_idx][hand_idx] or self.player_bust_flags[player_idx][hand_idx]:
             st.warning(f"Player {player_idx + 1} Hand {hand_idx + 1} cannot stand now.")
             return
             
        st.toast(f"Player {player_idx + 1} Hand {hand_idx + 1} stands.", icon="🛑")
        self.player_stand_flags[player_idx][hand_idx] = True
        self.advance_turn() # Move to next hand/player
                
    def double_down(self):
        player_idx = self.current_player_index
        hand_idx = self.current_hand_indices[player_idx]
        current_hand = self.player_hands[player_idx][hand_idx]
        current_bet = self.player_bets[player_idx][hand_idx]

        # Check conditions for this hand
        can_double = (
            len(current_hand) == 2 and
            # Can only double down on first two cards of any hand (split or initial)
            self.player_balances[player_idx] >= current_bet and # Need enough balance to double the bet for THIS hand
            not self.player_stand_flags[player_idx][hand_idx] and 
            not self.player_bust_flags[player_idx][hand_idx] and
            not self.player_split_flags[player_idx] # Common rule: No double down after split? Let's enforce this for simplicity.
            # Alternatively, allow double after split: remove the above line.
        )

        if can_double:
            st.toast(f"Player {player_idx + 1} Hand {hand_idx + 1} doubles down!", icon="💰")
            # Double the bet for this specific hand
            self.player_bets[player_idx][hand_idx] *= 2
            # Deduct the additional bet amount
            self.player_balances[player_idx] -= current_bet 
            
            # Hit happens automatically
            new_card = self.deck.deal()
            self.player_hands[player_idx][hand_idx].append(new_card)
            st.toast(f"Player {player_idx + 1} Hand {hand_idx + 1} draws: {new_card}", icon="🃏") 
            time.sleep(1.0) # Pause after double down hit

            values, is_valid = self.calculate_hand_value(self.player_hands[player_idx][hand_idx])
            self.player_stand_flags[player_idx][hand_idx] = True # Player is done with this hand after double down

            if not is_valid: # Player busts on double down
                bust_value = min(values)
                self.player_messages[player_idx] = f"Player {player_idx + 1} Hand {hand_idx + 1}: Busts with {bust_value} on double down!"
                self.player_bust_flags[player_idx][hand_idx] = True
                # Balance was already adjusted for the doubled bet. Loss is implicit.
                # Need to ensure dealer gets the doubled bet if player busts here.
                self.dealer_balance += self.player_bets[player_idx][hand_idx] # Dealer collects the full doubled bet
                # self.player_balances already reduced by original bet amount above.
            else:
                # Display final hand value? Let UI handle it.
                 pass 
            
            self.advance_turn() # Move to next hand/player
        else:
             # Give more specific feedback
            reason = ""
            if len(current_hand) != 2: reason = "Can only double on first two cards."
            elif self.player_balances[player_idx] < current_bet: reason = f"Need £{current_bet} more to double."
            elif self.player_stand_flags[player_idx][hand_idx] or self.player_bust_flags[player_idx][hand_idx]: reason = "Hand finished."
            elif self.player_split_flags[player_idx]: reason = "Cannot double down after splitting."
            else: reason = "Double down not allowed now."
            st.warning(f"Player {player_idx + 1} Hand {hand_idx + 1}: Cannot double down. {reason}")

    def split(self):
        player_idx = self.current_player_index
        hand_idx = self.current_hand_indices[player_idx]
        
        # --- Validity Checks ---
        current_hand = self.player_hands[player_idx][hand_idx]
        original_bet = self.player_bets[player_idx][hand_idx]
        player_balance = self.player_balances[player_idx]
        is_initial_hand = (hand_idx == 0) # Can only split the first hand dealt
        has_split_already = self.player_split_flags[player_idx] # Simplification: No re-splitting allowed
        can_afford = player_balance >= original_bet
        correct_num_cards = len(current_hand) == 2
        already_finished = self.player_stand_flags[player_idx][hand_idx] or self.player_bust_flags[player_idx][hand_idx]
        
        cards_match = False
        if correct_num_cards:
            cards_match = current_hand[0].get_value() == current_hand[1].get_value()
 
        can_split = (is_initial_hand and 
                       not has_split_already and 
                       can_afford and 
                       correct_num_cards and 
                       cards_match and
                       not already_finished)
 
        if not can_split:
            # Provide more specific feedback if possible
            if not is_initial_hand: reason = "Can only split the initial hand."
            elif has_split_already: reason = "Cannot re-split."
            elif not correct_num_cards: reason = "Can only split a 2-card hand."
            elif not cards_match: reason = "Cards must have the same value to split."
            elif not can_afford: reason = f"Need £{original_bet} more to split."
            elif already_finished: reason = "Cannot split a finished hand."
            else: reason = "Split not allowed."
            st.warning(f"Player {player_idx + 1}: Cannot split. {reason}")
            return
 
        # --- Perform Split --- 
        st.toast(f"Player {player_idx + 1} splits!", icon="✂️")
        self.player_split_flags[player_idx] = True # Mark that player has split
        self.player_balances[player_idx] -= original_bet # Deduct bet for new hand
 
        # Get the cards
        card1 = current_hand[0]
        card2 = current_hand[1]
 
        # Add structures for the new hand
        self.player_hands[player_idx].append([card2]) # New hand starts with card2
        self.player_bets[player_idx].append(original_bet)
        self.player_stand_flags[player_idx].append(False)
        self.player_bust_flags[player_idx].append(False)
        new_hand_idx = len(self.player_hands[player_idx]) - 1 # Index of the newly added hand
 
        # Modify the original hand
        self.player_hands[player_idx][hand_idx] = [card1] 
 
        # Deal one card to each new hand
        st.toast("Dealing to split hands...", icon="🃏")
        time.sleep(0.5)
        new_card_1 = self.deck.deal()
        self.player_hands[player_idx][hand_idx].append(new_card_1)
        st.toast(f"Player {player_idx+1} Hand {hand_idx+1} gets: {new_card_1}", icon="🃏")
        time.sleep(0.8)
         
        new_card_2 = self.deck.deal()
        self.player_hands[player_idx][new_hand_idx].append(new_card_2)
        st.toast(f"Player {player_idx+1} Hand {new_hand_idx+1} gets: {new_card_2}", icon="🃏")
        time.sleep(0.8)
         
        # --- Handle Special Cases (Aces / Blackjacks) --- 
        is_ace_split = (card1.value == 'A')
 
        if is_ace_split:
            st.toast("Splitting Aces! Each hand gets one card and stands.", icon="⚠️")
            self.player_stand_flags[player_idx][hand_idx] = True
            self.player_stand_flags[player_idx][new_hand_idx] = True
            # Player's turn on this hand might be technically over, advance_turn will handle moving
            # to the next hand or player after the rerun.
        else:
            # Check for Blackjack on first hand (not possible on Ace split)
            if self.get_hand_display_value(self.player_hands[player_idx][hand_idx]) == "Blackjack!":
                st.success(f"Player {player_idx + 1} Hand {hand_idx + 1}: Blackjack!")
                self.player_stand_flags[player_idx][hand_idx] = True
             
            # Check for Blackjack on second hand
            if self.get_hand_display_value(self.player_hands[player_idx][new_hand_idx]) == "Blackjack!":
                st.success(f"Player {player_idx + 1} Hand {new_hand_idx + 1}: Blackjack!")
                self.player_stand_flags[player_idx][new_hand_idx] = True
         
        # Keep current_hand_indices[player_idx] at the current hand (hand_idx). 
        # The player will play this hand first. advance_turn needs modification
        # to handle moving to the next hand (new_hand_idx) for this player.
        # For now, just rerun to update UI. The next action will be on hand 1.
        # st.rerun() # Rerun will be handled by the button press in the UI section

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
        is_dealer_busted = not dealer_valid
        if dealer_valid:
            dealer_value = dealer_values[-1]
        elif dealer_values: 
             dealer_value = min(dealer_values)
             dealer_display_value = f"Bust ({dealer_value})" # Ensure display shows bust
        else: 
             dealer_value = 99 # Bust value fallback
             dealer_display_value = "Bust (Error)"

        # Reset player messages to build results for this round
        self.player_messages = [""] * self.num_players

        # Evaluate each hand for each player vs dealer
        for player_idx in range(self.num_players):
            player_round_message = f"Player {player_idx + 1} Results: "
            num_hands = len(self.player_hands[player_idx])
            
            for hand_idx in range(num_hands):
                hand_message = f"Hand {hand_idx + 1}: "
                bet = self.player_bets[player_idx][hand_idx]
                player_hand = self.player_hands[player_idx][hand_idx]
                is_busted = self.player_bust_flags[player_idx][hand_idx]

                if is_busted:
                    # Message was set when busted, balance adjusted. Just note it here.
                    # Player already lost `bet` when they busted.
                    hand_message += f"Busted (-£{bet}). " 
                    player_round_message += hand_message
                    continue # Evaluate next hand

                # Hand is not busted, get its value
                player_values, player_valid = self.calculate_hand_value(player_hand)
                # Ensure valid calculation (should always be valid if not busted)
                player_value = player_values[-1] if player_valid else 0 
                player_display = self.get_hand_display_value(player_hand)
                # is_player_bj = player_display == "Blackjack!" # Use numeric value comparison primarily

                # --- Compare hand against dealer --- 
                if is_dealer_busted:
                    # Player wins unless busted (handled above)
                    hand_message += f"Wins £{bet}! (Dealer busts). "
                    self.player_balances[player_idx] += bet
                    self.dealer_balance -= bet
                elif player_value > dealer_value:
                    hand_message += f"Wins £{bet}! ({player_display} vs {dealer_display_value}). "
                    self.player_balances[player_idx] += bet
                    self.dealer_balance -= bet
                elif dealer_value > player_value:
                    hand_message += f"Loses £{bet}. ({player_display} vs {dealer_display_value}). "
                    # Only adjust balance here if player didn't bust (loss already applied on bust)
                    self.dealer_balance += bet
                    self.player_balances[player_idx] -= bet
                else: # Push (player_value == dealer_value)
                    # Handle Blackjack push specifically? Standard push is no balance change.
                    # If player BJ vs dealer BJ, it's a push. If player 21 vs dealer 21, it's a push.
                    hand_message += f"Push! ({player_display} vs {dealer_display_value}). "
                    # No balance change

                player_round_message += hand_message
            
            # Store the combined result message for the player
            self.player_messages[player_idx] = player_round_message.strip()

        self.game_over = True
        self.dealer_turn_active = False 
        # Don't rerun here, let the main loop handle the final display update

    def take_insurance(self):
        player_idx = self.current_player_index
        if not self.insurance_offered or self.player_made_insurance_decision[player_idx]:
            return # Should not happen via UI, but safe check

        insurance_cost = self.player_bets[player_idx][0] // 2 # Integer division
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
            # --- Logic for Dealer having Blackjack --- 
            st.warning("Dealer Blackjack!") 
            # Reveal dealer's hand in the UI by marking turn potentially active or game over
            # The hand display logic already shows full hand on game_over
            # self.dealer_turn_active = True # Setting game_over is sufficient

            for i in range(self.num_players):
                insurance_bet = self.player_insurance_bets[i]
                player_bet = self.player_bets[i][0]
                player_bj = self.get_hand_display_value(self.player_hands[i][0]) == "Blackjack!"
                message = f"Player {i+1}: "
                
                # Settle insurance bet (should be 0 if declined, but handle payout if taken)
                if insurance_bet > 0:
                     payout = insurance_bet * 2
                     self.player_balances[i] += payout 
                     self.dealer_balance -= payout
                     message += f"Wins £{payout} insurance. "
                elif self.player_made_insurance_decision[i]: # Only mention insurance loss if decision was made
                     # No message needed for declined, only if they took and lost (handled in else block)
                     # We don't need an explicit message for declining here as the outcome
                     # depends on the main bet vs dealer BJ.
                     pass

                # Settle original bet (vs Dealer BJ)
                if player_bj:
                    message += "Pushes original bet (both Blackjack)."
                    # No change to balance for original bet
                else:
                    message += f"Loses original bet (£{player_bet}) vs Dealer Blackjack."
                    # Apply loss only if player didn't have BJ
                    self.player_balances[i] -= player_bet
                    self.dealer_balance += player_bet
                
                self.player_messages[i] = message
                self.player_stand_flags[i][0] = True # Hand is over for everyone
            
            self.game_over = True
            self.insurance_offered = False # Insurance phase is done
            self.dealer_turn_active = False # Game is over, no more dealer turn
            # No need to call check_player_blackjacks or advance_turn here
            # The rerun from the button press will show the game over state

        else: # Dealer does NOT have Blackjack
             st.info("Dealer does not have Blackjack.")
             losing_insurance_total = 0
             for i in range(self.num_players):
                 insurance_bet = self.player_insurance_bets[i]
                 if insurance_bet > 0:
                     self.player_balances[i] -= insurance_bet
                     self.dealer_balance += insurance_bet
                     losing_insurance_total += insurance_bet
                     st.error(f"Player {i+1} loses £{insurance_bet} insurance bet.", icon="💸") 
             
             self.insurance_offered = False # Insurance phase over
             # Now proceed with checking for player Blackjacks (since dealer didn't have one)
             self.check_player_blackjacks() # This updates stand/bust flags for BJ players
             
             # If game didn't end due to all players having BJ, set up the first player's turn
             if not self.game_over:
                 # Find the first player who hasn't stood or busted (usually player 0 unless they had BJ)
                 first_playable_player = -1
                 for i in range(self.num_players):
                     if not self.player_stand_flags[i][0] and not self.player_bust_flags[i][0]:
                         first_playable_player = i
                         break
                 
                 if first_playable_player != -1:
                     self.current_player_index = first_playable_player
                     # Toast is optional here, UI update will show active player
                     # st.toast(f"Player {self.current_player_index + 1}'s turn.", icon="👤") 
                 else:
                     # All players finished (e.g., all got Blackjack). Check if dealer needs to play.
                     all_players_finished_after_bj_check = all(self.player_stand_flags[i][0] or self.player_bust_flags[i][0] for i in range(self.num_players))
                     if all_players_finished_after_bj_check:
                         any_player_active = any(not self.player_bust_flags[i][0] for i in range(self.num_players))
                         if any_player_active:
                              st.toast("Dealer's turn!", icon="🤖")
                              self.dealer_turn_active = True # Signal dealer turn in main loop
                         else:
                              st.toast("All players finished (BJ/Bust).", icon="🏁")
                              self.game_over = True # Ensure game over if all busted/BJ after insurance
                              
                 # We DO NOT call advance_turn here anymore.
                 # The rerun triggered by the insurance button press will update the UI 
                 # based on the now-corrected current_player_index or game_over/dealer_turn_active state.
                 # self.advance_turn(check_dealer_turn=False) # REMOVED THIS LINE

    def reset_game_state(self):
        """Resets the entire game state to initial values, including balances and deck."""
        st.toast("Resetting game state...", icon="🔄")
        self.deck = Deck() # Reset and reshuffle the deck
        self.dealer_hand: List[Card] = []
        # Reset player state for multiple hands
        self.player_hands: List[List[List[Card]]] = [[[]] for _ in range(self.num_players)]
        self.player_balances: List[int] = [50] * self.num_players
        self.dealer_balance: int = 10000
        self.player_bets: List[List[int]] = [[5] for _ in range(self.num_players)] # Reset to single bet
        self.player_stand_flags: List[List[bool]] = [[False] for _ in range(self.num_players)] # Reset to single hand state
        self.player_bust_flags: List[List[bool]] = [[False] for _ in range(self.num_players)] # Reset to single hand state
        self.current_player_index: int = 0
        self.current_hand_indices: List[int] = [0] * self.num_players # Reset active hand index
        self.player_split_flags: List[bool] = [False] * self.num_players # Reset split status
        self.player_messages: List[str] = [""] * self.num_players
        self.game_over: bool = True # Game is over after reset, ready for new deal
        self.dealer_turn_active: bool = False
        # Reset insurance state
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
        player_balance = st.session_state.game.player_balances[i]
        dealer_balance = st.session_state.game.dealer_balance
        # Read the bet value intended before this round started
        current_bet = st.session_state.game.player_bets[i][0]

        st.write(f"**Player {i+1}**") # Display player number regardless

        # Condition 1: Player doesn't have minimum balance
        if player_balance < min_bet:
            # Ensure bet is 0 if they cannot afford minimum
            if not betting_disabled:
                 st.session_state.game.player_bets[i][0] = 0
            st.caption(f"Insufficient balance (£{player_balance}) for min bet (£{min_bet}).")
            # Display the current bet (which is 0) as static text if disabled
            if betting_disabled:
                 st.write(f"Bet: £{st.session_state.game.player_bets[i][0]}")
            continue # Skip slider for this player

        # Calculate potential max bet based on balances and game cap
        max_bet_possible = min(player_balance, dealer_balance, 100)

        # Condition 2: Max possible bet is less than min bet (e.g., dealer low balance)
        if max_bet_possible < min_bet:
            # Ensure bet is 0 if the minimum cannot be placed
            if not betting_disabled:
                 st.session_state.game.player_bets[i][0] = 0
            st.caption(f"Cannot place min bet (£{min_bet}). Max possible is £{max_bet_possible} (check balances).")
            # Display the current bet (which is 0) as static text if disabled
            if betting_disabled:
                 st.write(f"Bet: £{st.session_state.game.player_bets[i][0]}")
            continue # Skip slider for this player

        # --- Slider Rendering ---
        # If we reach here, a valid bet between min_bet and max_bet_possible can be placed.

        # Ensure the value displayed/used by the slider is within the valid range [min_bet, max_bet_possible]
        # Clamp the potentially stale 'current_bet' from state to the valid range
        clamped_value_for_slider = max(min_bet, min(current_bet, max_bet_possible))

        # Store the potentially clamped value back into state *if* betting is currently allowed
        # This corrects the state if the previous value was invalid due to balance changes
        if not betting_disabled:
             st.session_state.game.player_bets[i][0] = clamped_value_for_slider

        # Display the slider - parameters are now guaranteed to be valid
        new_bet = st.slider(f"Bet", # Simplified label
                            min_value=min_bet,
                            max_value=max_bet_possible,
                            value=clamped_value_for_slider,
                            step=5,
                            key=f"bet_slider_{i}",
                            disabled=betting_disabled)

        # Update the bet in session state ONLY if the user changed the slider value
        # and betting is not disabled. Compare slider output 'new_bet' with the value
        # it was initialized with 'clamped_value_for_slider'.
        if not betting_disabled and new_bet != clamped_value_for_slider:
            st.session_state.game.player_bets[i][0] = new_bet
            # Note: No st.rerun() here, the 'Deal' button will use the latest bet value

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
    for i in range(game.num_players):
        with game_cols[i + 1]: # Start from the second column (index 1)
            st.markdown(f"##### Player {i+1}") # Main player title

            # --- Loop through hands for this player ---
            for h in range(len(game.player_hands[i])):
                current_hand = game.player_hands[i][h]
                current_bet = game.player_bets[i][h]
                is_stood = game.player_stand_flags[i][h]
                is_busted = game.player_bust_flags[i][h]
                is_active_hand = (i == current_player_idx and h == game.current_hand_indices[i] and not is_stood and not is_busted)
                is_active_player_insurance_turn = (i == current_player_idx and game.insurance_offered and not game.player_made_insurance_decision[i])
                
                # Determine highlighting: Highlight based on active hand during play, or active player during insurance
                is_highlighted = False
                if game.insurance_offered:
                    is_highlighted = is_active_player_insurance_turn # Highlight player deciding insurance
                elif not game.dealer_turn_active and not game.game_over:
                    is_highlighted = is_active_hand # Highlight the specific hand being played

                border_style = "border: 3px solid #007bff; border-radius: 10px; padding: 10px; margin-bottom: 10px;" if is_highlighted else "border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin-bottom: 10px;"
                st.markdown(f'<div style="{border_style}">', unsafe_allow_html=True)
                
                st.markdown(f"**Hand {h + 1}** (Bet: £{current_bet})")

                # Display Hand Cards
                player_cards_html = '<div class="hand-container">'
                if not current_hand: # Handle case where hand might be empty initially (e.g., during reset/deal error)
                    player_cards_html += "(No cards)"
                else:
                    for card in current_hand:
                        player_cards_html += f'<div class="card {card.get_color()}">{card.value}<br>{card.get_symbol()}</div>'
                player_cards_html += '</div>'
                st.markdown(player_cards_html, unsafe_allow_html=True)
                
                # Display Hand Total (only if cards exist)
                if current_hand:
                    st.markdown(f'<div class="hand-total">Total: {game.get_hand_display_value(current_hand)}</div>', unsafe_allow_html=True)

                # Display Hand Status (Busted/Stood/Blackjack)
                if is_busted:
                    st.error("BUSTED")
                elif is_stood:
                     # Check for Blackjack specifically on stand? evaluate_winner handles results.
                     # Let's just show "Finished" if stood.
                     hand_val_str = game.get_hand_display_value(current_hand)
                     if hand_val_str == "Blackjack!":
                          st.success("BLACKJACK!") # Indicate BJ status clearly
                     else: 
                          st.info("Finished") # More neutral term than STOOD

                # --- Action Buttons Logic --- 
                # Show buttons only if it's this specific hand's turn OR this player's insurance turn
                if is_highlighted: # Use the highlighting flag
                    # Display whose turn it is (player level)
                    if game.num_players > 1 or len(game.player_hands[i]) > 1:
                        st.markdown(f"**Player {i+1} Active Hand {h+1}**" if not game.insurance_offered else f"**Player {i+1} Insurance?**")
                    else:
                         st.markdown("**Your Go**" if not game.insurance_offered else "**Insurance?**")

                    # === Insurance Phase Buttons (Show once per player) ===
                    if game.insurance_offered and h == 0: # Show insurance options only once, with the first hand display
                        max_insurance = game.player_bets[i][0] // 2 # Insurance based on original bet
                        can_afford_insurance = game.player_balances[i] >= max_insurance
                        
                        ins_cols = st.columns(2)
                        with ins_cols[0]:
                            if st.button(f"Take (£{max_insurance})", use_container_width=True, disabled=not can_afford_insurance, key=f"ins_take_{i}"): # Key per player
                                game.take_insurance()
                                st.rerun()
                        with ins_cols[1]:
                            if st.button("Decline", use_container_width=True, key=f"ins_decline_{i}"): # Key per player
                                game.decline_insurance()
                                st.rerun()
                        if not can_afford_insurance and max_insurance > 0:
                            st.caption(f"(Needs £{max_insurance})", help=f"Balance: £{game.player_balances[i]}")
                        elif max_insurance <= 0:
                            st.caption("(Min bet needed)", help="Insurance requires a base bet.")
                    
                    # === Regular Play Phase Buttons (Show per active hand) ===
                    elif not game.insurance_offered and not game.dealer_turn_active and not game.game_over:
                        action_cols = st.columns(4) # Add column for Split
                        player_balance = game.player_balances[i]

                        # Check conditions for this specific hand
                        can_hit_stand = not is_stood and not is_busted
                        # Double down condition (check original bet amount for cost)
                        can_double = (can_hit_stand and 
                                      len(current_hand) == 2 and 
                                      player_balance >= current_bet and # Balance >= Bet for THIS hand
                                      not game.player_split_flags[i]) # No double after split rule
                        # Split condition
                        can_split = (can_hit_stand and
                                     h == 0 and # Can only split initial hand
                                     not game.player_split_flags[i] and # Cannot re-split
                                     len(current_hand) == 2 and
                                     current_hand[0].get_value() == current_hand[1].get_value() and
                                     player_balance >= current_bet) # Check balance vs bet of hand 0

                        with action_cols[0]:
                            if st.button("Hit", use_container_width=True, disabled=not can_hit_stand, key=f"hit_{i}_{h}"): # Unique key
                                game.hit()
                                st.rerun() 
                        with action_cols[1]:
                            if st.button("Stand", use_container_width=True, disabled=not can_hit_stand, key=f"stand_{i}_{h}"): # Unique key
                                game.stand() 
                                st.rerun() 
                        with action_cols[2]:
                            if st.button("Double Down", use_container_width=True, disabled=not can_double, key=f"double_{i}_{h}"): # Unique key
                                # Double down cost is the bet amount for this hand again
                                if game.player_balances[i] < current_bet:
                                    st.warning(f"Need £{current_bet} more to double.") # Check vs current_bet
                                else:
                                    game.double_down()
                                    st.rerun() 
                        with action_cols[3]:
                           if st.button("Split", use_container_width=True, disabled=not can_split, key=f"split_{i}_{h}"): # Unique key
                               # Check affordability again just before action
                               if game.player_balances[i] < current_bet:
                                    st.warning(f"Need £{current_bet} more to split.")
                               else:
                                    game.split()
                                    st.rerun()
                                
                st.markdown('</div>' , unsafe_allow_html=True) # Close hand highlight div

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
