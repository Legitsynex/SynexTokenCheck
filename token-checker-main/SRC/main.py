import os
import json
import random
import base64
import datetime
import time
from colorama import Fore
from pathlib import Path
import ctypes
import tls_client
import shutil
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

if os.name == "nt":
    ctypes.windll.kernel32.SetConsoleTitleW("Token Checker | Synett.cc")

def display_logo():
    logo = """
┏┓        
┗┓┓┏┏┓┏┓╋╋
┗┛┗┫┛┗┗ ┗┗
┛   
Synett.cc | Version 1.0 \n
    """
    console_width = shutil.get_terminal_size((80, 20)).columns
    lines = logo.strip().split("\n")
    centered_lines = [line.center(console_width) for line in lines]
    print(f"{Fore.RESET}\n".join(centered_lines) + f"{Fore.RESET}")

def load_config():
    default_config = {
        "threads": 10,
        "thread_wait_time": 1,
        "proxyless": False,
        "clear_output_files": True,
    }
    if not os.path.exists("config.json"):
        with open("config.json", "w") as config_file:
            json.dump(default_config, config_file, indent=4)
    return json.load(open("config.json", encoding="utf-8"))

config = load_config()

def get_timestamp():
    return f"{Fore.LIGHTMAGENTA_EX}{datetime.datetime.now().strftime('%H:%M:%S')}{Fore.RESET}"

def print_status(message, status_type):
    status_symbol = "∆"
    print(f"{Fore.RESET}[{get_timestamp()}][{Fore.CYAN}{status_symbol}{Fore.RESET}]{message}{Fore.RESET}")

def create_output_directory():
    timestamp = datetime.datetime.now().strftime('[%Y-%m-%d] [%H-%M-%S]')
    output_dir = f"output/{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    for filename in ["invalid.txt", "locked.txt", "used.txt", "valid.txt", "unlocked.txt", "1m-tokens.txt", "3m-tokens.txt", "other.txt", "2-boosts.txt", "1-boosts.txt", "email-verified.txt", "fully-verified.txt", "flagged.txt", "ratelimited.txt", "not-subscribed.txt"]:
        open(os.path.join(output_dir, filename), "w").close()
    return output_dir

def write_to_file(content, filename, output_dir):
    with open(os.path.join(output_dir, filename), "a") as file:
        file.write(f"{content}\n")

def get_all_tokens(filename):
    return [line.split(":")[2] if ":" in line else line for line in open(filename, "r").read().splitlines()]

def get_proxy():
    if config.get('proxyless', False):
        return None
    try:
        proxies = [line.strip() for line in open("input/proxies.txt", "r").readlines() if line.strip()]
        if proxies:
            raw_proxy = random.choice(proxies)
            if "@" in raw_proxy:
                creds, ip_port = raw_proxy.split("@")
                username, password = creds.split(":")
                return {'http': f'http://{username}:{password}@{ip_port}', 'https': f'http://{username}:{password}@{ip_port}'}
            else:
                return {'http': f'http://{raw_proxy}', 'https': f'http://{raw_proxy}'}
    except FileNotFoundError:
        print_status("Proxy file not found. Proceeding without proxies.", False)
    return None

def validate_proxy(proxy):
    try:
        response = requests.get("https://httpbin.org/ip", proxies=proxy, timeout=5)
        return response.status_code == 200
    except Exception:
        return False

class TokenData:
    def __init__(self):
        self.other = self.valid = self.one_month_tokens = self.invalid = self.used = self.locked = self.no_nitro = self.three_month_tokens = self.checked = self.sorted = 0
        self.valid_lst = []

data = TokenData()

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.49 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.49 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.49 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:100.0) Gecko/20100101 Firefox/100.0',
    'Mozilla/5.0 (X11; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:99.0) Gecko/20100101 Firefox/99.0',
    'Mozilla/5.0 (X11; Linux x86_64; rv:99.0) Gecko/20100101 Firefox/99.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
]

def get_headers(token):
    super_properties = base64.b64encode('{"os":"Windows","browser":"Chrome","device":"","system_locale":"en-GB","browser_user_agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.49 Safari/537.36","browser_version":"112.0.5615.49","os_version":"10","referrer":"","referring_domain":"","referrer_current":"","referring_domain_current":"","release_channel":"stable","client_build_number":102113,"client_event_source":null}'.encode()).decode()
    return {
        'Authorization': token,
        'User-Agent': random.choice(user_agents),
        'Content-Type': 'application/json',
        'Connection': 'keep-alive'
    }

def validate_token(client, token):
    try:
        response = client.get("https://discord.com/api/v9/users/@me", headers=get_headers(token))
        if response.status_code == 200:
            profile = response.json()
            return f"{profile['username']}#{profile['discriminator']}"
        return None
    except Exception:
        return None

def get_full_token(token):
    with open("input/tokens.txt", "r") as file:
        for line in file:
            if token in line:
                return line.strip()
    return token

def check_token(token, proxy=None, output_dir=None):
    full_token = get_full_token(token)
    client = tls_client.Session(client_identifier="chrome_112", random_tls_extension_order=True)
    if proxy:
        client.proxies.update(proxy)
    headers = get_headers(token)
    try:
        response = client.get("https://discord.com/api/v9/users/@me", headers=headers)
        if response.status_code != 200:
            print_status(f"Token: {token[:39]} | Flags: [INVALID]", False)
            data.invalid += 1
            data.checked += 1
            write_to_file(full_token, "invalid.txt", output_dir)
            return False
        user_data = response.json()
        email_verified = user_data.get('verified', False)
        phone = user_data.get('phone')
        mfa_enabled = user_data.get('mfa_enabled', False)
        boost_response = client.get("https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots", headers=headers)
        flagged = "Flagged" if boost_response.status_code == 403 else "Unflagged"
        boost_count = len(boost_response.json()) if boost_response.status_code in [200, 201] else 0
        subscription_response = client.get("https://discord.com/api/v9/users/@me/billing/subscriptions", headers=headers)
        days_left = "N/A"
        if subscription_response.status_code in [200, 201]:
            subscriptions = subscription_response.json()
            if subscriptions:
                sub_end = subscriptions[0].get('current_period_end')
                if sub_end:
                    end_date = datetime.datetime.strptime(sub_end, '%Y-%m-%dT%H:%M:%S.%f%z')
                    now = datetime.datetime.now(datetime.timezone.utc)
                    days_left = (end_date - now).days
                if days_left <= 30:
                    write_to_file(full_token, "1m-tokens.txt", output_dir)
                elif days_left <= 90:
                    write_to_file(full_token, "3m-tokens.txt", output_dir)
                else:
                    write_to_file(full_token, "other.txt", output_dir)
        verification_status = "Fully Verified" if email_verified and phone else "Email Verified" if email_verified else "Not Verified"
        unlock_status = "Unlocked" if not mfa_enabled else "Locked"
        print_status(f"Token: {token[:39]} | Flags: [Boost Available: {boost_count}], [Days Left: {days_left}], [{flagged}], [{verification_status}], [{unlock_status}]", True)
        if flagged == "Flagged":
            data.locked += 1
            write_to_file(full_token, "flagged.txt", output_dir)
        elif days_left != "N/A":
            data.valid += 1
            data.valid_lst.append(token)
            if boost_count == 2:
                write_to_file(full_token, "2-boosts.txt", output_dir)
            elif boost_count == 1:
                write_to_file(full_token, "1-boosts.txt", output_dir)
            write_to_file(full_token, "valid.txt", output_dir)
        else:
            data.no_nitro += 1
            write_to_file(full_token, "not-subscribed.txt", output_dir)
        if email_verified and phone:
            write_to_file(full_token, "fully-verified.txt", output_dir)
        elif email_verified:
            write_to_file(full_token, "email-verified.txt", output_dir)
        data.checked += 1
        return True
    except Exception as e:
        print_status(f"Error checking token: {token[:39]} | Exception: {e}", False)
        write_to_file(full_token, "ratelimited.txt", output_dir)
        return False

def clear_file(filename):
    try:
        open(filename, "w").write("")
    except Exception:
        pass

def clear_input_tokens_file():
    if config.get("clear_input_tokens", False):
        with open("input/tokens.txt", "w") as file:
            file.truncate(0)
        print_status("Cleared Tokens File.", True)

def remove_duplicates(filename):
    all_tokens = open(filename, "r").read().splitlines()
    without_duplicates = list(dict.fromkeys(all_tokens))
    open(filename, "w").write("")
    for line in without_duplicates:
        open(filename, "a").write(f"{line}\n")
    return len(without_duplicates)

if __name__ == "__main__":
    clear_screen()
    display_logo()
    output_directory = create_output_directory()
    tokens = get_all_tokens("input/tokens.txt")
    if not tokens:
        print_status("No tokens found in input/tokens.txt. Exiting...", False)
        quit()
    with ThreadPoolExecutor(max_workers=config.get("threads", 10)) as executor:
        futures = {executor.submit(check_token, token, get_proxy(), output_directory): token for token in tokens}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print_status(f"Error processing token: {futures[future]} | Exception: {e}", False)
        time.sleep(config.get("thread_wait_time", 1))
    print_status(f"Checked: {data.checked} tokens.", True)
    clear_input_tokens_file()
    print_status(f"Valid Tokens: {data.valid} | Used: {data.used} | Unlocked: {data.no_nitro} | Locked: {data.locked} | Invalid: {data.invalid}", True)
    input("Press Enter to exit...")
    quit()