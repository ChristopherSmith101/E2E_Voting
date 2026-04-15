def generate_proof(vote):
    # TODO: replace with real ZK proof
    return {"valid": vote in [0, 1]}


def verify_proof(proof):
    return proof.get("valid", False)