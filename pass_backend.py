"""Password-store command adapters used by the Pass plugin."""

class PasswordStoreBackend:
    def __init__(self, executable):
        self.executable = executable

    def command(self, *args):
        return [self.executable, *args]

    def passwords(self, otp=False, otp_glob="*-otp.gpg"):
        raise NotImplementedError

    def copy_command(self, password):
        return self.command("--clip", password)

    def edit_command(self, password):
        return self.command("edit", password)

    def remove_command(self, password):
        return self.command("rm", "--force", password)

    def otp_command(self, password):
        return self.command("otp", "--clip", password)

    def generate_command(self, location):
        return self.command("generate", "--clip", location, "20")
