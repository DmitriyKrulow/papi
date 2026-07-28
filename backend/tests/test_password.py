import sys
sys.path.insert(0, '.')

from src.core.value_objects.password_hash import PasswordHash

# The hash from the database
password_hash_str = 'xMpuwbAOEktzyQQFFwhArMBOJYBR2zb4Ge4nIlhWqBY=$100000$j/29PkIkESfZ0BcEQbq2LN1XNCwt2t98yvVUb58CRTI='

# Test with admin123
try:
    password_hash = PasswordHash.from_hash_string(password_hash_str)
    result = password_hash.verify('admin123')
    print(f'Password verification result for "admin123": {result}')
except Exception as e:
    print(f'Error: {e}')

# Test with wrong password
try:
    password_hash = PasswordHash.from_hash_string(password_hash_str)
    result = password_hash.verify('wrongpassword')
    print(f'Password verification result for "wrongpassword": {result}')
except Exception as e:
    print(f'Error: {e}')
