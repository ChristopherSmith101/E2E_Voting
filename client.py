from crypto import encrypt
from ballot import Ballot
from proof import generate_proof


def create_ballot(pk, vote, token):
    ciphertext, randomness = encrypt(pk, vote)
    proof = generate_proof(vote)
    ballot = Ballot(ciphertext, proof, token)
    return ballot, randomness
