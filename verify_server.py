from ballot import Ballot
from proof import verify_proof


class VotingServer:
    def __init__(self, board, auth):
        self.board = board
        self.auth = auth

    # -----------------------------
    # Main entry point
    # -----------------------------
    def submit_ballot(self, data):
        """
        data = JSON from frontend:
        {
            "ciphertext": [c1, c2],
            "proof": {...},
            "token": "abc123"
        }
        """

        # -------------------------
        # 1. Basic structure check
        # -------------------------
        if not data:
            print("Rejected: empty payload")
            return False

        if "token" not in data:
            print("Rejected: missing token")
            return False

        if "ciphertext" not in data or "proof" not in data:
            print("Rejected: malformed ballot")
            return False

        token = data["token"]

        # -------------------------
        # 2. Token validation
        # -------------------------
        if not self.auth.validate_token(token):
            print("Rejected: invalid or used token")
            return False

        # -------------------------
        # 3. Proof validation
        # -------------------------
        if not verify_proof(data["proof"]):
            print("Rejected: invalid proof")
            return False

        # -------------------------
        # 4. Construct ballot object
        # -------------------------
        ballot = Ballot(
            ciphertext=tuple(data["ciphertext"]),
            proof=data["proof"],
            voter_token=token
        )

        # -------------------------
        # 5. Store on bulletin board
        # -------------------------
        self.board.post_ballot(ballot)

        print("Accepted ballot:", ballot.hash())
        return True