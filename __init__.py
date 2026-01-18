# -*- coding: utf-8 -*-
# Copyright (c) 2017 Benedict Dudel
# Copyright (c) 2023 Max
# Copyright (c) 2023 Pete-Hamlin

import fnmatch
import os

from albert import *

md_iid = "5.0"
md_version = "2.0.1"
md_name = "Pass"
md_description = "Manage passwords in pass"
md_license = "MIT"
md_url = "https://github.com/albertlauncher/albert-plugin-python-pass"
md_authors = ["@benedictdudel", "@maxmil", "@Pete-Hamlin", "@okaestne"]
md_maintainers = ["@maxmil", "@okaestne", "@Pete-Hamlin"]
md_bin_dependencies = ["pass"]

HOME_DIR = os.environ["HOME"]
PASS_DIR = os.environ.get("PASSWORD_STORE_DIR", os.path.join(HOME_DIR, ".password-store/"))


class Plugin(PluginInstance, GeneratorQueryHandler):
    def __init__(self):
        PluginInstance.__init__(self)
        GeneratorQueryHandler.__init__(self)
        self._use_otp = self.readConfig("use_otp", bool) or False
        self._otp_glob = self.readConfig("otp_glob", str) or "*-otp.gpg"

    @staticmethod
    def makeIcon():
        return Icon.theme("dialog-password")

    @property
    def use_otp(self):
        return self._use_otp

    @use_otp.setter
    def use_otp(self, value):
        print(f"Setting _use_otp to {value}")
        self._use_otp = value
        self.writeConfig("use_otp", value)

    @property
    def otp_glob(self):
        return self._otp_glob

    @otp_glob.setter
    def otp_glob(self, value):
        print(f"Setting _otp_glob to {value}")
        self._otp_glob = value
        self.writeConfig("otp_glob", value)

    def defaultTrigger(self):
        return "pass "

    def synopsis(self, query):
        return "<pass-name>"

    def configWidget(self):
        return [
            {"type": "checkbox", "property": "use_otp", "label": "Enable pass OTP extension"},
            {
                "type": "lineedit",
                "property": "otp_glob",
                "label": "Glob pattern for OTP passwords",
                "widget_properties": {"placeholderText": "*-otp.gpg"},
            },
        ]

    def items(self, context: QueryContext):
        q = context.query.strip()

        if q.startswith("generate"):
            yield [self.generatePassword(q)]
        elif q.startswith("otp") and self._use_otp:
            yield self.showOtp(q)
        else:
            yield self.showPasswords(q)

    def generatePassword(self, query) -> Item:
        location = query.strip()[9:]

        return StandardItem(
            id="generate_password",
            icon_factory=Plugin.makeIcon,
            text="Generate a new password",
            subtext="The new password will be located at %s" % location,
            input_action_text="pass %s" % query,
            actions=[
                Action(
                    "generate",
                    "Generate",
                    lambda: runDetachedProcess(["pass", "generate", "--clip", location, "20"]),
                )
            ],
        )

    def showOtp(self, query) -> list[Item]:
        otp_query = query.strip()[4:]
        if otp_query:
            passwords = self.getPasswordsFromSearch(otp_query, otp=True)
        else:
            passwords = self.getPasswords(otp=True)

        results = []
        for password in passwords:
            results.append(
                StandardItem(
                    id=password,
                    icon_factory=Plugin.makeIcon,
                    text=password.split("/")[-1],
                    subtext=password,
                    actions=[
                        Action(
                            "copy",
                            "Copy",
                            lambda pwd=password: runDetachedProcess(["pass", "otp", "--clip", pwd]),
                        ),
                    ],
                ),
            )
        return results

    def showPasswords(self, query) -> list[Item]:
        if query.strip():
            passwords = self.getPasswordsFromSearch(query)
        else:
            passwords = self.getPasswords()

        results = []
        for password in passwords:
            name = password.split("/")[-1]
            results.append(
                StandardItem(
                    id=password,
                    text=name,
                    subtext=password,
                    icon_factory=Plugin.makeIcon,
                    input_action_text="pass %s" % password,
                    actions=[
                        Action(
                            "copy",
                            "Copy",
                            lambda pwd=password: runDetachedProcess(["pass", "--clip", pwd]),
                        ),
                        Action(
                            "edit",
                            "Edit",
                            lambda pwd=password: runDetachedProcess(["pass", "edit", pwd]),
                        ),
                        Action(
                            "remove",
                            "Remove",
                            lambda pwd=password: runDetachedProcess(["pass", "rm", "--force", pwd]),
                        ),
                    ],
                ),
            )

        return results

    def getPasswords(self, otp=False):
        passwords = []
        for root, dirnames, filenames in os.walk(PASS_DIR, followlinks=True):
            for filename in fnmatch.filter(filenames, self._otp_glob if otp else "*.gpg"):
                passwords.append(os.path.join(root, filename.replace(".gpg", "")).replace(PASS_DIR, ""))

        return sorted(passwords, key=lambda s: s.lower())

    def getPasswordsFromSearch(self, otp_query, otp=False):
        passwords = [password for password in self.getPasswords(otp) if otp_query.strip().lower() in password.lower()]
        return passwords
