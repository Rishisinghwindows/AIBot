"""
Word Game Tool

A simple anagram game.
"""

import random

WORD_LIST = [
    "python", "gemini", "chainlit", "langchain", "chatbot", "developer", "interface"
]

def start_word_game():
    """
    Starts a new anagram game.

    Returns:
        A dictionary with the original word and its anagram.
    """
    word = random.choice(WORD_LIST)
    anagram = "".join(random.sample(word, len(word)))
    return {"word": word, "anagram": anagram}

def check_word_game_answer(guess: str, correct_word: str) -> bool:
    """
    Checks if the user's guess is correct.

    Args:
        guess: The user's guess.
        correct_word: The correct word.

    Returns:
        True if the guess is correct, False otherwise.
    """
    return guess.lower() == correct_word.lower()
