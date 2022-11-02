from random import choice
from string import digits


def generate_passcode() -> str:
    return "".join(choice(digits) for i in range(4))
