#!/usr/bin/env python3

import ipaddress
import platform
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime


def ping(ip: str, timeout_seconds: int = 1) -> tuple[str, bool]:
    system = platform.system().lower()

    if system == "windows":
        command = ["ping", "-n", "1", "-w", str(timeout_seconds * 1000), ip]
    else:
        command = ["ping", "-c", "1", "-W", str(timeout_seconds), ip]

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout_seconds + 2
        )
        return ip, result.returncode == 0

    except subprocess.TimeoutExpired:
        return ip, False


def main():
    if len(sys.argv) < 2:
        print("Usage: python ping_sweep.py <network/CIDR> [output_file]")
        print("Example: python ping_sweep.py 192.168.1.0/24 results.txt")
        sys.exit(1)

    network_input = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) >= 3 else "ping_results.txt"

    try:
        network = ipaddress.ip_network(network_input, strict=False)
    except ValueError as e:
        print(f"Invalid network: {e}")
        sys.exit(1)

    addresses = [str(ip) for ip in network.hosts()]

    results = []

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(ping, ip) for ip in addresses]

        for future in as_completed(futures):
            ip, is_alive = future.result()
            status = "UP" if is_alive else "DOWN"
            results.append((ipaddress.ip_address(ip), status))
            print(f"{ip:<15} {status}")

    results.sort(key=lambda x: x[0])

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"Ping sweep results\n")
        f.write(f"Network: {network}\n")
        f.write(f"Generated: {datetime.now().isoformat(timespec='seconds')}\n")
        f.write("=" * 40 + "\n\n")

        for ip, status in results:
            f.write(f"{ip}\t{status}\n")

    print(f"\nResults written to: {output_file}")


if __name__ == "__main__":
    main()
