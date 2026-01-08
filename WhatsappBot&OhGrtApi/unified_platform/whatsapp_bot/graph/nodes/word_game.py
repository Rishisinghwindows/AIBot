"""
Word Game Node

Handles the logic for the anagram word game.
Supports multilingual responses (11+ Indian languages).
"""

from whatsapp_bot.state import BotState
from common.tools.word_game import start_word_game, check_word_game_answer
from common.i18n.responses import get_word_game_label


def handle_word_game(state: BotState) -> dict:
    """
    Node function: Manages the word game.
    Returns response in user's detected language.

    Args:
        state: Current bot state.

    Returns:
        Updated state with game progress.
    """
    user_guess = state.get("current_query", "").strip()
    game_state = state.get("word_game", {})
    detected_lang = state.get("detected_language", "en")

    if game_state.get("is_active"):
        # Game is in progress, check the answer
        correct_word = game_state.get("correct_word")
        if not correct_word:
            error_msg = get_word_game_label("error", detected_lang)
            return {
                "response_text": error_msg,
                "word_game": {"is_active": False, "correct_word": None},
                "should_fallback": False,
                "intent": "word_game",
            }

        if check_word_game_answer(user_guess, correct_word):
            correct_msg = get_word_game_label("correct", detected_lang, word=correct_word)
            play_again_msg = get_word_game_label("play_again", detected_lang)
            return {
                "response_text": f"{correct_msg}\n\n{play_again_msg}",
                "word_game": {"is_active": False, "correct_word": None},
                "should_fallback": False,
                "intent": "word_game",
            }
        else:
            wrong_msg = get_word_game_label("wrong", detected_lang)
            return {
                "response_text": wrong_msg,
                "should_fallback": False,
                "intent": "word_game",
            }
    else:
        # Start a new game
        game_data = start_word_game()
        new_game_state = {"is_active": True, "correct_word": game_data["word"]}
        start_msg = get_word_game_label("start", detected_lang)

        return {
            "response_text": f"{start_msg}\n\n*{game_data['anagram']}*",
            "word_game": new_game_state,
            "should_fallback": False,
            "intent": "word_game",
        }
