import hmac
from hashlib import sha256


ENCODING = 'utf-8'
DIGEST_MODE = sha256
SECRET = 'secret'


def create_hash(password: str):
    password = password.encode(ENCODING)
    secret = SECRET.encode(ENCODING)
    return hmac.new(key=secret, msg=password, digestmod=DIGEST_MODE).hexdigest()


def validate_password(password: str, password_hash: str):
    test_hash = create_hash(password)
    return hmac.compare_digest(test_hash, password_hash)

