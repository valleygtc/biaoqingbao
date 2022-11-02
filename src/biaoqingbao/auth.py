import jwt

from .configs import SECRET_KEY


def generate_token(json_data: dict) -> str:
    return jwt.encode(
        json_data,
        SECRET_KEY,
        algorithm="HS256",
    )


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
