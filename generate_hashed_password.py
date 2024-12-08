import bcrypt

# 生成固定哈希值
username = "admin"
password = "mysecurepassword"
hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print(f"Username: {username}")
print(f"Hashed Password: {hashed_password.decode()}")
