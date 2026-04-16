import uuid
import hashlib

class AuthServer:
    def __init__(self):
        self.tokens = set()

    def hash_token(self, token):
        return hashlib.sha256(token.encode()).hexdigest()
    
    def issue_token(self):
        token = str(uuid.uuid4())
        self.tokens.add(token)
        return token

    def validate_token(self, token):
        if token in self.tokens:
            self.tokens.remove(token)
            return True
        return False
    
	# def validate_token(self, token):
	# 	print("VALIDATING TOKEN:", token)
	# 	print("CURRENT TOKENS:", self.tokens)

	# 	if token in self.tokens:
	# 		self.tokens.remove(token)
	# 		print("TOKEN ACCEPTED AND REMOVED")
	# 		return True

	# 	print("TOKEN REJECTED")
	# 	return False