from enum import Enum


class Messages(Enum):
    InvalidPathSyntax: str =     "Invalid syntax. Example: " \
                                 "mc!setpath C:\\Users\\User\\Server\\minecraft_server.jar",

    InvalidIPSyntax: str =       "Invalid syntax. Example: " \
                                 "mc!setip 127.0.0.1"

    PathAssertionError: str =    "Provided path does not exist."

    IPAssertionError: str =      "Invalid IP address. Example : 127.0.0.1"

    ConfigPermissionError: str = "Permission error: Couldn't create/write to config file." \
                                 "Try Launching in Administrator Mode or with more privileges."

    IPSaveSuccess: str =         "IP is successfully saved."

    PathSaveSuccess: str =       "Path is successfully saved."

    UnhandledException: str =    "Unhandled error has occurred."


ErrorMessages: dict[(type(BaseException), str), str] = {
    (IndexError, "setpath"): Messages.InvalidPathSyntax,

    (IndexError, "setip"): Messages.InvalidIPSyntax,

    (AssertionError, "setpath"): Messages.PathAssertionError,

    (AssertionError, "setip"): Messages.IPAssertionError,

    (PermissionError, "setpath"): Messages.ConfigPermissionError,

    (PermissionError, "setip"): Messages.PathAssertionError,

}
