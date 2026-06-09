# -*- coding: utf-8 -*-
import hashlib
import os
import base64
import hmac


def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16)
    else:
        salt = base64.b64decode(salt.encode('ascii'))

    dk = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    salt_b64 = base64.b64encode(salt).decode('ascii')
    hash_b64 = base64.b64encode(dk).decode('ascii')
    return f'pbkdf2_sha256$100000${salt_b64}${hash_b64}'


def verify_password(password, stored_hash):
    if not stored_hash:
        return False

    if stored_hash.startswith('pbkdf2_sha256$'):
        try:
            parts = stored_hash.split('$')
            if len(parts) != 4:
                return False
            algorithm, iterations, salt_b64, hash_b64 = parts
            iterations = int(iterations)
            salt = base64.b64decode(salt_b64.encode('ascii'))
            expected_hash = base64.b64decode(hash_b64.encode('ascii'))

            dk = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt,
                iterations
            )
            return hmac.compare_digest(dk, expected_hash)
        except Exception:
            return False

    import hashlib
    if len(stored_hash) == 32:
        md5_hash = hashlib.md5(password.encode('utf-8')).hexdigest()
        return md5_hash == stored_hash

    return False
