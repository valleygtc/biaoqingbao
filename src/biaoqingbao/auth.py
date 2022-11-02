import jwt

from .configs import configs


def generate_token(json_data: dict) -> str:
    return jwt.encode(
        json_data,
        configs.SECRET_KEY,
        algorithm="HS256",
    )


def decode_token(token: str) -> dict:
    return jwt.decode(token, configs.SECRET_KEY, algorithms=["HS256"])
