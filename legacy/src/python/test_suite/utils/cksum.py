import hashlib

def get_cksum(path, cksum_type):
    func = getattr(hashlib, cksum_type.lower())  # hashlib.md5 or hashlib.sha256
    h = func()
    f = open(path)
    while True:
        data = f.read(10240)
        if not data:
            break
        h.update(data)
    f.close()
    return h.hexdigest()

