from random import choice
from string import digits


def generate_passcode():
    return "".join(choice(digits) for i in range(4))
