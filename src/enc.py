from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Random import get_random_bytes

SECRET = b"Pepsi tastes better than Coke."

privkey = RSA.generate(1024)
pubkey = privkey.public_key()
aeskey = get_random_bytes(16)

# encrypt AES key with RSA public key
cipher_rsa = PKCS1_OAEP.new(pubkey)
enc_aeskey = cipher_rsa.encrypt(aeskey)

# encrypt secret with AES key
cipher = AES.new(aeskey, AES.MODE_EAX)
nonce = cipher.nonce
ciphertext, tag = cipher.encrypt_and_digest(SECRET)

# decrypt AES key with RSA private key
dec_cipher = PKCS1_OAEP.new(privkey)
dec_aeskey = dec_cipher.decrypt(enc_aeskey)

#print(dec_aeskey)

# decrypt secret with AES key
cipher_aes = AES.new(dec_aeskey, AES.MODE_EAX, nonce)
dec_secret = cipher_aes.decrypt_and_verify(ciphertext, tag)

#print(dec_secret)