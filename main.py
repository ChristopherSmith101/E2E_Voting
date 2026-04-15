from crypto import keygen
from bulletin_board import BulletinBoard
from auth import AuthServer
from verify_server import VotingServer
from client import create_ballot
from tally import tally


def main():
    # Setup
    sk, pk = keygen()
    board = BulletinBoard()
    auth = AuthServer()
    server = VotingServer(board, auth)
    
	# Voter gets token
    token = auth.issue_token()

    # Voter creates ballot
    ballot, randomness = create_ballot(pk, vote=1, token=token)

    # Submit ballot
    server.submit_ballot(ballot)

    # Tally
    result = tally(board.list_ballots(), sk)
    print("Final tally:", result)
    
if __name__ == "__main__":
	main()