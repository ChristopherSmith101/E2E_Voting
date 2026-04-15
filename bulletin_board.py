class BulletinBoard:
    def __init__(self):
        self.ballots = []

    def post_ballot(self, ballot):
        self.ballots.append(ballot)

    def list_ballots(self):
        return self.ballots