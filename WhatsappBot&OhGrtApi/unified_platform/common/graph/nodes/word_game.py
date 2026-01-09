"""
Word Game Node

Handles the logic for the anagram word game.
"""

from common.graph.state import BotState
from common.tools.word_game import start_word_game, check_word_game_answer

def handle_word_game(state: BotState) -> dict:
    """
    Node function: Manages the word game.

    Args:
        state: Current bot state.

    Returns:
        Updated state with game progress.
    """
    user_guess = state.get("current_query", "").strip()
    game_state = state.get("word_game", {})

    if game_state.get("is_active"):
        # Game is in progress, check the answer
        correct_word = game_state.get("correct_word")
        if not correct_word:
            return {
                "response_text": "Something went wrong with the game. Let's start over.",
                "word_game": {"is_active": False, "correct_word": None},
                "should_fallback": False,
                "intent": "word_game",
            }

        if check_word_game_answer(user_guess, correct_word):
            return {
                "response_text": f"Correct! The word was *{correct_word}*. Well done!\n\nType 'word game' to play again.",
                "word_game": {"is_active": False, "correct_word": None},
                "should_fallback": False,
                "intent": "word_game",
            }
        else:
            return {
                "response_text": "Not quite, try again!",
                "should_fallback": False,
                "intent": "word_game",
            }
    else:
        # Start a new game
        game_data = start_word_game()
        new_game_state = {"is_active": True, "correct_word": game_data["word"]}

        return {
            "response_text": f"Let's play a word game!  unscramble this word:\n\n*{game_data['anagram']}*",
            "word_game": new_game_state,
            "should_fallback": False,
            "intent": "word_game",
        }
