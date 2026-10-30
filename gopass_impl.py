import subprocess

from pass_backend import PasswordStoreBackend


class GoPassBackend(PasswordStoreBackend):
    def passwords(self, otp=False, otp_glob="*-otp.gpg"):
        # GoPass stores OTP data inside each encrypted secret, so it cannot
        # enumerate OTP entries using the pass *-otp.gpg convention.
        if otp:
            return []
        completed = subprocess.run(
            self.command("ls", "--flat"), capture_output=True, text=True, check=True
        )
        return sorted(
            (line.strip().removesuffix("/") for line in completed.stdout.splitlines() if line.strip()),
            key=str.lower,
        )
