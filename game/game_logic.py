import json
import random
from pathlib import Path

class LetterStatus:
    EMPTY = "empty"
    FILLED = "filled"
    CORRECT = "correct"
    PRESENT = "present"
    ABSENT = "absent"

class GameLogic:
    WORD_LENGTH = 5
    MAX_ATTEMPTS = 6

    def __init__(self):
        self.words = self.load_words()

        self.current_word = None
        self.current_word_id = None

        self.attempts = []
        self.current_guess = ""

        self.game_over = False
        self.won = False

        self.new_game()

    def load_words(self):
        words_path = Path(__file__).parent / "assets/words.json"

        with open(words_path, "r", encoding="utf-8") as file:
            words = json.load(file)

        return [
            word.lower()
            for word in words
            if len(word) == self.WORD_LENGTH
        ]

    def new_game(self):
        index = random.randrange(len(self.words))
        return self.start_word(index)

    def get_word_by_id(self, word_id):
        index = word_id - 1

        if not (0 <= index < len(self.words)):
            return None

        return self.start_word(index)

    def start_word(self, index):
        self.current_word = self.words[index]
        self.current_word_id = index + 1

        self.attempts = []
        self.current_guess = ""

        self.game_over = False
        self.won = False

        return self.current_word, self.current_word_id

    @property
    def current_row(self):
        return len(self.attempts)

    @property
    def current_column(self):
        return len(self.current_guess)

    def can_accept_input(self):
        return (
            not self.game_over
            and self.current_row < self.MAX_ATTEMPTS
        )

    def add_letter(self, letter):
        if not self.can_accept_input():
            return False

        if len(self.current_guess) >= self.WORD_LENGTH:
            return False

        letter = letter.lower()

        if len(letter) != 1 or not letter.isalpha():
            return False

        self.current_guess += letter

        return True

    def delete_letter(self):
        if not self.can_accept_input():
            return False

        if not self.current_guess:
            return False

        self.current_guess = self.current_guess[:-1]

        return True

    def submit_guess(self):
        if not self.can_accept_input():
            return None

        if len(self.current_guess) != self.WORD_LENGTH:
            return None

        if self.current_guess not in self.words:
            return None

        statuses = self.evaluate_guess(self.current_guess)

        self.attempts.append((self.current_guess, statuses))

        if self.current_guess == self.current_word:
            self.won = True
            self.game_over = True

        elif self.current_row >= self.MAX_ATTEMPTS:
            self.game_over = True

        self.current_guess = ""

        return statuses

    def get_letter_statuses(self):
        priority = {
            LetterStatus.ABSENT: 0,
            LetterStatus.PRESENT: 1,
            LetterStatus.CORRECT: 2,
        }

        statuses = {}

        for guess, guess_statuses in self.attempts:
            for letter, status in zip(guess, guess_statuses):
                current_best = statuses.get(letter)

                if current_best is None or priority[status] > priority[current_best]:
                    statuses[letter] = status

        return statuses

    def evaluate_guess(self, guess):
        statuses = [LetterStatus.ABSENT] * self.WORD_LENGTH
        remaining_letters = list(self.current_word)

        self.mark_correct_letters(guess, statuses, remaining_letters)
        self.mark_present_letters(guess, statuses, remaining_letters)

        return statuses

    def mark_correct_letters(self, guess, statuses, remaining_letters):
        for index, (guess_letter, word_letter) in enumerate(
            zip(guess, self.current_word)
        ):
            if guess_letter == word_letter:
                statuses[index] = LetterStatus.CORRECT
                remaining_letters[index] = None

    def mark_present_letters(self, guess, statuses, remaining_letters):
        for index, letter in enumerate(guess):
            if self.is_present_letter(letter, index, statuses, remaining_letters):
                statuses[index] = LetterStatus.PRESENT
                self.remove_letter(letter, remaining_letters)

    def is_present_letter(self, letter, index, statuses, remaining_letters):
        return (
            statuses[index] != LetterStatus.CORRECT
            and letter in remaining_letters
        )

    def remove_letter(self, letter, remaining_letters):
        index = remaining_letters.index(letter)
        remaining_letters[index] = None