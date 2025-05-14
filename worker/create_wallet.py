from eth_account import Account
import secrets

# Generate a random 32-byte hex private key
private_key = "0x" + secrets.token_hex(32)
acct = Account.from_key(private_key)

print("Private Key:", private_key)
print("Address:", acct.address)