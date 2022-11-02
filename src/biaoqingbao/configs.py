from pydantic import BaseSettings, Field, PostgresDsn


class Configs(BaseSettings):
    # DEBUG = True if os.getenv('DEBUG') in ('True', 'true', '1') else False
    # SQLALCHEMY_ECHO = True

    # TESTING = True if os.getenv('TESTING') in ('True', 'true', '1') else False

    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_DATABASE_URI: PostgresDsn = Field(..., env="DATABASE_URI")
    SECRET_KEY: str

    EMAIL_HOST: str = "smtpdm.aliyun.com"
    EMAIL_USERNAME: str = "admin@notice.bqb.plus"
    EMAIL_PASSWORD: str


configs = Configs()
