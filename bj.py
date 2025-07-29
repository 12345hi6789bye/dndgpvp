import streamlit as st
from streamlit_autorefresh import st_autorefresh
import random
import json
import os

st_autorefresh(interval=2000, key="datarefresh")

try:
    with open('bj/hands.json', 'r') as jsonfile:
        playerHands = json.load(jsonfile)
except FileNotFoundError:
    playerHands = [[], []]
    with open('bj/hands.json', 'w') as jsonfile:
        json.dump(playerHands, jsonfile, indent=4)

try:
    with open('bj/cards.json', 'r') as jsonfile:
        cards = json.load(jsonfile)
except FileNotFoundError:
    cards = []
    for suit in ['Hearts', 'Diamonds', 'Clubs', 'Spades']:
        numbers = ['Ace'] + list(range(2, 11)) + ['Jack', 'Queen', 'King']
        for number in numbers:
            if number in ['Jack', 'Queen', 'King']:
                value = 10
            elif number == 'Ace':
                value = 11
            else:
                value = number
            cards.append({"name": f"{number} of {suit}", "suit": suit, "value": value})

    with open('bj/cards.json', 'w') as jsonfile:
        json.dump(cards, jsonfile, indent=4)



# Use a shared file for currentPlayer so all users see the same turn
current_player_path = 'bj/current_player.json'
player_status_path = 'bj/state.json'

if not os.path.exists(current_player_path):
    currentPlayer = 1
    with open(current_player_path, 'w') as f:
        json.dump(currentPlayer, f)
else:
    with open(current_player_path, 'r') as f:
        currentPlayer = json.load(f)

# Track whether each player has stood or bust
if not os.path.exists(player_status_path):
    player_status = [False, False]  # False = still playing, True = done
    with open(player_status_path, 'w') as f:
        json.dump(player_status, f)
else:
    with open(player_status_path, 'r') as f:
        player_status = json.load(f)

selectedUser = st.selectbox("Select Player", ["Player 1", "Player 2"])

if selectedUser == "Player 1":
    selectedUserID = 1
else:
    selectedUserID = 2

st.title("DNDG PVP")
col1, col2 = st.columns(2)

# Calculate totals before displaying hands
def get_total(hand):
    total = sum(card['value'] for card in hand)
    aces = sum(1 for card in hand if card['name'].startswith('Ace'))
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total

player_totals = [get_total(hand) for hand in playerHands]




# Show selected player on the left, other on the right
if selectedUser == "Player 1":
    col1.header("Player 1")
    col1.write(f"Total: {player_totals[0]}")
    cards_text_1 = "\n".join([card['name'] for card in playerHands[0]])
    col1.text(cards_text_1 if cards_text_1 else "No cards")

    col2.header("Player 2")
    col2.write(f"Total: {player_totals[1]}")
    cards_text_2 = "\n".join([card['name'] for card in playerHands[1]])
    col2.text(cards_text_2 if cards_text_2 else "No cards")
else:
    col1.header("Player 2")
    col1.write(f"Total: {player_totals[1]}")
    cards_text_2 = "\n".join([card['name'] for card in playerHands[1]])
    col1.text(cards_text_2 if cards_text_2 else "No cards")

    col2.header("Player 1")
    col2.write(f"Total: {player_totals[0]}")
    cards_text_1 = "\n".join([card['name'] for card in playerHands[0]])
    col2.text(cards_text_1 if cards_text_1 else "No cards")



st.write("---")

# Reset button to clear hands and cards and reset turn
if st.button("Reset Game"):
    playerHands = [[], []]
    with open('bj/hands.json', 'w') as jsonfile:
        json.dump(playerHands, jsonfile, indent=4)
    # Rebuild deck
    cards = []
    for suit in ['Hearts', 'Diamonds', 'Clubs', 'Spades']:
        numbers = ['Ace'] + list(range(2, 11)) + ['Jack', 'Queen', 'King']
        for number in numbers:
            if number in ['Jack', 'Queen', 'King']:
                value = 10
            elif number == 'Ace':
                value = 11
            else:
                value = number
            cards.append({"name": f"{number} of {suit}", "suit": suit, "value": value})
    with open('bj/cards.json', 'w') as jsonfile:
        json.dump(cards, jsonfile, indent=4)
    # Reset turn to Player 1
    with open(current_player_path, 'w') as f:
        json.dump(1, f)
    # Reset player_status so both players are marked as not done
    player_status = [False, False]
    with open(player_status_path, 'w') as f:
        json.dump(player_status, f)
    st.rerun()


def get_total(hand):
    total = sum(card['value'] for card in hand)
    aces = sum(1 for card in hand if card['name'].startswith('Ace'))
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total

player_totals = [get_total(hand) for hand in playerHands]

if not all(player_status):
    # Show buttons for the current player if it's their turn and they haven't finished
    if ((selectedUser == "Player 1" and currentPlayer == 1 and not player_status[0]) or
        (selectedUser == "Player 2" and currentPlayer == 2 and not player_status[1])):
        hit = st.button("Hit")
        stand = st.button("Stand")
        bust = player_totals[currentPlayer - 1] > 21

        if hit and not bust:
            if len(cards) > 0:
                card = random.choice(cards)
                playerHands[currentPlayer - 1].append(card)
                cards.remove(card)
                with open('bj/hands.json', 'w') as jsonfile:
                    json.dump(playerHands, jsonfile, indent=4)
                with open('bj/cards.json', 'w') as jsonfile:
                    json.dump(cards, jsonfile, indent=4)
                st.success(f"{selectedUser} drew {card['name']}")
                # Switch turn only if both players are still playing
                if not player_status[1 if currentPlayer == 1 else 0]:
                    # Alternate turn
                    if currentPlayer == 1:
                        currentPlayer = 2
                    else:
                        currentPlayer = 1
                    with open(current_player_path, 'w') as f:
                        json.dump(currentPlayer, f)
                st.rerun()
            else:
                st.error("No more cards left!")
        elif bust:
            st.error(f"{selectedUser} busts!")
            # Mark player as finished
            player_status[currentPlayer - 1] = True
            with open(player_status_path, 'w') as f:
                json.dump(player_status, f)
            # If other player is still playing, switch turn to them
            if not player_status[1 if currentPlayer == 1 else 0]:
                if currentPlayer == 1:
                    currentPlayer = 2
                else:
                    currentPlayer = 1
                with open(current_player_path, 'w') as f:
                    json.dump(currentPlayer, f)
            st.rerun()
        elif stand:
            st.success(f"{selectedUser} stands.")
            # Mark player as finished
            player_status[currentPlayer - 1] = True
            with open(player_status_path, 'w') as f:
                json.dump(player_status, f)
            # If other player is still playing, switch turn to them
            if not player_status[1 if currentPlayer == 1 else 0]:
                if currentPlayer == 1:
                    currentPlayer = 2
                else:
                    currentPlayer = 1
                with open(current_player_path, 'w') as f:
                    json.dump(currentPlayer, f)
            st.rerun()
    # Only show waiting message if it's not your turn
    elif not ((selectedUser == "Player 1" and currentPlayer == 1) or (selectedUser == "Player 2" and currentPlayer == 2)):
        st.info("Waiting for your turn...")
else:
    # Game over, show winner
    p1 = player_totals[0] if player_totals[0] <= 21 else 0
    p2 = player_totals[1] if player_totals[1] <= 21 else 0
    if p1 > p2:
        st.success(f"Game Over! Player 1 wins with {p1}.")
    elif p2 > p1:
        st.success(f"Game Over! Player 2 wins with {p2}.")
    elif p1 == p2 and p1 != 0:
        st.info(f"Game Over! It's a tie at {p1}.")
    elif all(len(hand) > 0 for hand in playerHands) and p1 == 0 and p2 == 0:
        st.info("Game Over! Both players busted.")

