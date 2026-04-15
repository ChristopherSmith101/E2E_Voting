import hashlib

class Ballot:
    def __init__(self, ciphertext, proof, voter_token):
        self.ciphertext = ciphertext
        self.proof = proof
        self.voter_token = voter_token

    def hash(self):
        return hashlib.sha256(str(self.ciphertext).encode()).hexdigest()