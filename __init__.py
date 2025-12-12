# -*- coding: utf-8 -*-
# Copyright (c) 2017 Benedict Dudel
# Copyright (c) 2023 Max
# Copyright (c) 2023 Pete-Hamlin
# Copyright (c) 2025 poettig

import fnmatch
import os
import shutil
import subprocess
from pathlib import Path

from albert import *

md_iid = "4.0"
md_version = "2.0.1"
md_name = "Pass"
md_description = "Manage passwords in pass"
md_license = "BSD-3"
md_url = "https://github.com/albertlauncher/albert-plugin-python-pass"
md_authors = ["@benedictdudel", "@maxmil", "@Pete-Hamlin", "@okaestne", "@poettig"]
md_maintainers = ["@maxmil", "@okaestne", "@Pete-Hamlin"]

HOME_DIR = os.environ["HOME"]
PASS_DIR = os.environ.get("PASSWORD_STORE_DIR", os.path.join(HOME_DIR, ".password-store/"))


class Plugin(PluginInstance, TriggerQueryHandler):
    def __init__(self):
        PluginInstance.__init__(self)
        TriggerQueryHandler.__init__(self)
        self._use_gopass = self.readConfig("use_gopass", bool) or False
        self._use_otp = self.readConfig("use_otp", bool) or False
        self._otp_glob = self.readConfig("otp_glob", str) or "*-otp.gpg"
        self._pass_executable = "gopass" if self._use_gopass else "pass"

    def makeIcon(self):
        if self._use_gopass:
            return makeImageIcon(Path(__file__).parent / "gopass.png")
        else:
            return makeThemeIcon("dialog-password")

    @property
    def use_gopass(self) -> str:
        return self._use_gopass

    @use_gopass.setter
    def use_gopass(self, value) -> None:
        print(f"Setting _use_gopass to {value}")
        self._use_gopass = value
        self.writeConfig("use_gopass", value)

        pass_executable = "gopass" if self._use_gopass else "pass"
        print(f"Setting _pass_executable to {pass_executable}")
        self._pass_executable = pass_executable

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
            {
                "type": "checkbox",
                "property": "use_gopass",
                "label": "Use GoPass instead of pass",
            },
            {"type": "checkbox", "property": "use_otp", "label": "Enable pass OTP extension"},
            {
                "type": "lineedit",
                "property": "otp_glob",
                "label": "Glob pattern for OTP passwords",
                "widget_properties": {"placeholderText": "*-otp.gpg"},
            },
        ]

    def handleTriggerQuery(self, query):
        if not shutil.which(self._pass_executable):
            query.add(
                StandardItem(
                    id="executable_not_found",
                    icon_factory=lambda: Plugin.makeIcon(self),
                    text=f"{self._pass_executable} not found in $PATH",
                    subtext=f"Please check if {self._pass_executable} is properly installed."
                )
            )
        elif query.string.strip().startswith("generate"):
            self.generatePassword(query)
        elif query.string.strip().startswith("otp") and self._use_otp:
            self.showOtp(query)
        else:
            self.showPasswords(query)

    def generatePassword(self, query):
        location = query.string.strip()[9:]

        query.add(
            StandardItem(
                id="generate_password",
                icon_factory=lambda: Plugin.makeIcon(self),
                text="Generate a new password",
                subtext="The new password will be located at %s" % location,
                input_action_text="pass %s" % query.string,
                actions=[
                    Action(
                        "generate",
                        "Generate",
                        lambda: runDetachedProcess([self._pass_executable, "generate", "--clip", location, "20"]),
                    )
                ],
            )
        )

    def showOtp(self, query):
        otp_query = query.string.strip()[4:]
        passwords = []
        if otp_query:
            passwords = self.getPasswordsFromSearch(otp_query, otp=True)
        else:
            passwords = self.getPasswords(otp=True)

        results = []
        for password in passwords:
            results.append(
                StandardItem(
                    id=password,
                    icon_factory=lambda: Plugin.makeIcon(self),
                    text=password.split("/")[-1],
                    subtext=password,
                    actions=[
                        Action(
                            "copy",
                            "Copy",
                            lambda pwd=password: runDetachedProcess([self._pass_executable, "otp", "--clip", pwd]),
                        ),
                    ],
                ),
            )
        query.add(results)

    def showPasswords(self, query):
        if query.string.strip():
            passwords = self.getPasswordsFromSearch(query.string)
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
                    icon_factory=lambda: Plugin.makeIcon(self),
                    input_action_text="pass %s" % password,
                    actions=[
                        Action(
                            "copy",
                            "Copy",
                            lambda pwd=password: runDetachedProcess([self._pass_executable, "--clip", pwd]),
                        ),
                        Action(
                            "edit",
                            "Edit",
                            lambda pwd=password: runDetachedProcess([self._pass_executable, "edit", pwd]),
                        ),
                        Action(
                            "remove",
                            "Remove",
                            lambda pwd=password: runDetachedProcess([self._pass_executable, "rm", "--force", pwd]),
                        ),
                    ],
                ),
            )

        query.add(results)

    def getPasswordsFromGoPass(self) -> list:
        p = subprocess.run([self._pass_executable, "list", "--flat"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, encoding="utf-8")
        return p.stdout.splitlines()

    def getPasswordsFromPass(self, otp=False) -> list:
        passwords = []
        for root, dirnames, filenames in os.walk(PASS_DIR, followlinks=True):
            for filename in fnmatch.filter(filenames, self._otp_glob if otp else "*.gpg"):
                passwords.append(os.path.join(root, filename.replace(".gpg", "")).replace(PASS_DIR, ""))

        return passwords

    def getPasswords(self, otp=False):
        if self.use_gopass:
            passwords = self.getPasswordsFromGoPass()
        else:
            passwords = self.getPasswordsFromPass(otp)

        return sorted(passwords, key=lambda s: s.lower())

    def getPasswordsFromSearch(self, otp_query, otp=False):
        passwords = [password for password in self.getPasswords(otp) if otp_query.strip().lower() in password.lower()]
        return passwords
