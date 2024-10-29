import json
import os
import subprocess
from socket import inet_aton, inet_pton, AF_INET, error
from queue import Queue, Empty
from threading import Thread, Event

ROOT_DIR: str = os.path.abspath(os.path.dirname(__file__))


def is_valid_ipv4_address(address: str) -> bool:
    """
    :param address: String of the address
    :return: True if IP address is a valid IPV4, False otherwise
    >>> is_valid_ipv4_address("127.0.0.1")
    True
    >>> is_valid_ipv4_address("IP")
    False
    """
    try:
        inet_pton(AF_INET, address)
    except AttributeError:  # no inet_pton here, sorry
        try:
            inet_aton(address)
        except error:
            return False
        return address.count('.') == 3
    except error:  # not a valid address
        return False
    return True


def get_ip() -> str:
    """
    Returns the IP address bound by the user. Throws exception if unbound.
    >>> get_ip()
    127.0.0.1
    """
    cfg_path: str = os.path.join(ROOT_DIR, "config.json")
    with open(cfg_path, 'r') as cfg:
        try:
            cfg_json: dict = json.load(cfg)
            return cfg_json["ip_address"]
        except (json.decoder.JSONDecodeError, KeyError):
            raise KeyError("IP Address not bound. See mc!help")


def get_path() -> str:
    """
    Returns the jar path bound by the user. Throws exception if unbound.
    >>> get_path()
    C:\\Users\\user\\server\\minecraft_server.jar
    """
    cfg_path: str = os.path.join(ROOT_DIR, "config.json")
    with open(cfg_path, 'r') as cfg:
        try:
            cfg_json: dict = json.load(cfg)
            return cfg_json["jar_path"]
        except (json.decoder.JSONDecodeError, KeyError):
            raise KeyError("Jar path not bound. See mc!help")


def get_mem() -> int:
    """
    Returns default memory from config. If absent, returns 1024.
    :return:
    """
    cfg_path: str = os.path.join(ROOT_DIR, "config.json")
    with open(cfg_path, 'r') as cfg:
        try:
            cfg_json: dict = json.load(cfg)
            return int(cfg_json["mem_alloc"])
        except (json.decoder.JSONDecodeError, KeyError):
            return 1024


def write_to_config(key: str, value: str) -> None:
    """
    Opens config.json and writes new data
    :param key:  Any string key
    :param value: Any string Value
    >>> write_to_config("ip_address", "127.0.0.1")
    Will attempt to open config.json in local dir and write new key and value.
    """
    cfg_path: str = os.path.join(ROOT_DIR, "config.json")
    with open(cfg_path, 'r') as cfg:
        try:
            cfg_json: dict = json.load(cfg)
        except json.decoder.JSONDecodeError:
            cfg_json: dict = {}
        cfg_json[key] = value
    with open(cfg_path, 'w') as cfg:
        json.dump(cfg_json, cfg, indent=6)



def proc_readall(proc: subprocess.Popen) -> str:
    """
    Using a queue and a thread, we create a non-blocking stdout.readline(). Read until dry.
    :param proc: Any subprocess Popen with a stdout attribute.
    :return: String of all the lines printed.
    >>> proc_readall(proc)
    "Seed: 214890214080412 \n vorkuta_: Hello!"
    """
    # timeout border in seconds
    TIMEOUT: float = 1.0

    def enqueue_output(out, queue):
        for line in iter(out.readline, b''):
            if finish_event.is_set():
                return
            queue.put(line)
        out.close()

    output: str = ""
    stdout_read_queue: Queue = Queue()
    stdout_read_thread: Thread = Thread(target=enqueue_output, args=(proc.stdout, stdout_read_queue))
    stdout_read_thread.start()
    finish_event: Event = Event()

    while True:
        try:
            batch: bytes = stdout_read_queue.get(timeout=TIMEOUT)
            output += batch.decode().strip() + "\n"
        except Empty:
            return output
