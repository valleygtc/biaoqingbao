from string import digits
from random import choice


def generate_passcode():
    return ''.join(choice(digits) for i in range(4))
