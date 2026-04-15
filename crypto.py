import random

p = 23  # placeholder prime (use large safe prime in real system)
g = 5   # generator


def keygen():
    sk = random.randint(1, p-2)
    pk = pow(g, sk, p)
    return sk, pk


def encrypt(pk, m):
    r = random.randint(1, p-2)
    c1 = pow(g, r, p)
    c2 = (m * pow(pk, r, p)) % p
    return (c1, c2), r


def decrypt(sk, ciphertext):
    c1, c2 = ciphertext
    s = pow(c1, sk, p)
    s_inv = pow(s, -1, p)
    return (c2 * s_inv) % p