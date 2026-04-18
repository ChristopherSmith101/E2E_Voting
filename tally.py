from crypto import decrypt

def tally(ballots, sk):
    """Count YES votes from decrypted ballots"""
    yes_count = 0
    for ballot in ballots:
        vote = decrypt(sk, ballot.ciphertext)
        # YES is encrypted as 1, NO as 0
        if vote == 1:
            yes_count += 1
    return yes_count