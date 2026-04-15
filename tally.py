from crypto import decrypt


def tally(ballots, sk):
    total = 0
    for ballot in ballots:
        vote = decrypt(sk, ballot.ciphertext)
        total += vote
    return total