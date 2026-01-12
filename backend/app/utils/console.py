# app/utils/console.py
from colorama import init, Fore, Style

init(autoreset=True)

def info(msg: str):
    print(Fore.CYAN + msg + Style.RESET_ALL)

def ok(msg: str):
    print(Fore.GREEN + msg + Style.RESET_ALL)

def warn(msg: str):
    print(Fore.YELLOW + msg + Style.RESET_ALL)

def error(msg: str):
    print(Fore.RED + msg + Style.RESET_ALL)
