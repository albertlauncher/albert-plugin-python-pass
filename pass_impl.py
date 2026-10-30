import fnmatch
import os

from pass_backend import PasswordStoreBackend


class PassBackend(PasswordStoreBackend):
    def passwords(self, otp=False, otp_glob="*-otp.gpg"):
        store = os.environ.get(
            "PASSWORD_STORE_DIR", os.path.join(os.environ["HOME"], ".password-store")
        )
        pattern = otp_glob if otp else "*.gpg"
        result = []
        for root, _, filenames in os.walk(store, followlinks=True):
            for filename in fnmatch.filter(filenames, pattern):
                path = os.path.join(root, filename)
                result.append(os.path.relpath(path[:-4], store))
        return sorted(result, key=str.lower)
