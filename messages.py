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

    ServerStatus: str =          "Server is Online, has {} player(s) and replied in {} ms."

    StatusConnectionError =      "Server is offline."

    IPNotBound =                 "IP Address not bound. See mc!help"

    PathNotBound =               "Jar path not bound. See mc!help"


ErrorMessages: dict[(type(BaseException), str), str] = {
    (IndexError, "setpath"): Messages.InvalidPathSyntax.value,
    (IndexError, "setip"): Messages.InvalidIPSyntax.value,
    (AssertionError, "setpath"): Messages.PathAssertionError.value,
    (AssertionError, "setip"): Messages.IPAssertionError.value,
    (PermissionError, "setpath"): Messages.ConfigPermissionError.value,
    (PermissionError, "setip"): Messages.ConfigPermissionError.value,
    (ConnectionRefusedError, "status"): Messages.StatusConnectionError.value,
    (TimeoutError, "status"): Messages.StatusConnectionError.value,
    (KeyError, "status"): Messages.IPNotBound.value,
    (KeyError, "launch"): Messages.PathNotBound.value,
}

