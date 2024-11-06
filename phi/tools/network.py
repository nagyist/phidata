"""Network monitoring toolkit for phi agent.
Install dependencies: pip install psutil requests speedtest-cli dnspython
"""

import json
from phi.tools import Toolkit
import psutil
import requests
import socket
import speedtest
import subprocess
from typing import List, Dict
import platform
import dns.resolver
from datetime import datetime

class NetworkTools(Toolkit):
    def __init__(self):
        super().__init__(name="network_tools")

        # Register all methods
        self.register(self.get_network_info)
        self.register(self.check_connection)
        self.register(self.monitor_bandwidth)
        self.register(self.run_speed_test)
        self.register(self.get_dns_info)
        self.register(self.trace_route)
        self.register(self.scan_wifi_networks)
        self.register(self.get_network_usage_by_process)
        self.register(self.check_port_status)
        self.register(self.get_network_latency)
        self.register(self.get_network_interfaces)

    def get_network_interfaces(self) -> str:
        """Get detailed information about all network interfaces"""
        try:
            interfaces_info = {}
            for interface, addrs in psutil.net_if_addrs().items():
                addresses = []
                for addr in addrs:
                    try:
                        addr_info = {
                            "address": getattr(addr, "address", "N/A"),
                            "netmask": getattr(addr, "netmask", "N/A"),
                            "family": str(getattr(addr, "family", "N/A"))
                        }
                        addresses.append(addr_info)
                    except Exception:
                        continue

                # Get interface statistics
                try:
                    stats = psutil.net_if_stats()[interface]
                    interfaces_info[interface] = {
                        "addresses": addresses,
                        "status": "up" if stats.isup else "down",
                        "speed": f"{stats.speed} MB/s" if stats.speed else "unknown",
                        "mtu": stats.mtu
                    }
                except Exception:
                    interfaces_info[interface] = {"addresses": addresses}

            return json.dumps(interfaces_info, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to get network interfaces: {str(e)}"})

    def get_network_info(self) -> str:
        """Get comprehensive network information including interfaces and public IP"""
        try:
            # Get basic network info
            interfaces = self.get_network_interfaces()

            # Get public IP
            try:
                public_ip = requests.get("https://api.ipify.org").text
            except:
                public_ip = "Unable to fetch public IP"

            # Get active connections count
            try:
                connections = len(list(psutil.net_connections()))
            except:
                connections = 0

            info = {
                "interfaces": json.loads(interfaces),
                "public_ip": public_ip,
                "active_connections": connections,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            return json.dumps(info, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to get network info: {str(e)}"})

    def check_connection(self, host: str = "8.8.8.8", port: int = 53, timeout: int = 3) -> str:
        """Check connection to a specific host and port"""
        try:
            start_time = datetime.now()
            socket.create_connection((host, port), timeout=timeout)
            response_time = (datetime.now() - start_time).total_seconds() * 1000

            return json.dumps({
                "status": "connected",
                "host": host,
                "port": port,
                "response_time_ms": round(response_time, 2)
            })
        except Exception as e:
            return json.dumps({
                "status": "failed",
                "host": host,
                "port": port,
                "error": str(e)
            })

    def monitor_bandwidth(self) -> str:
        """Get current bandwidth usage statistics"""
        try:
            stats = psutil.net_io_counters()
            return json.dumps({
                "bytes_sent": stats.bytes_sent,
                "bytes_recv": stats.bytes_recv,
                "packets_sent": stats.packets_sent,
                "packets_recv": stats.packets_recv,
                "errors_in": stats.errin,
                "errors_out": stats.errout,
                "drops_in": stats.dropin,
                "drops_out": stats.dropout
            }, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to get bandwidth info: {str(e)}"})

    def run_speed_test(self) -> str:
        """Run a network speed test and return download/upload speeds"""
        try:
            st = speedtest.Speedtest()
            st.get_best_server()

            # Run tests
            download_speed = st.download() / 1_000_000  # Convert to Mbps
            upload_speed = st.upload() / 1_000_000  # Convert to Mbps
            ping = st.results.ping
            server = st.get_best_server()

            return json.dumps({
                "download_speed_mbps": round(download_speed, 2),
                "upload_speed_mbps": round(upload_speed, 2),
                "ping_ms": round(ping, 2),
                "server": {
                    "name": server["sponsor"],
                    "location": f"{server['name']}, {server['country']}",
                    "latency": server["latency"]
                },
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Speed test failed: {str(e)}"})

    def get_dns_info(self, domain: str) -> str:
        """Get comprehensive DNS information for a domain"""
        try:
            records = {}
            for record_type in ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA']:
                try:
                    answers = dns.resolver.resolve(domain, record_type)
                    records[record_type] = [str(answer) for answer in answers]
                except Exception:
                    continue

            return json.dumps({
                "domain": domain,
                "records": records,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, indent=2)
        except Exception as e:
            return json.dumps({"error": f"DNS lookup failed: {str(e)}"})

    def trace_route(self, host: str) -> str:
        """Perform a traceroute to a host"""
        try:
            if platform.system().lower() == "windows":
                cmd = ["tracert", host]
            else:
                cmd = ["traceroute", "-n", host]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return json.dumps({
                "host": host,
                "traceroute": result.stdout,
                "status": "success" if result.returncode == 0 else "failed",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Traceroute failed: {str(e)}"})

    def scan_wifi_networks(self) -> str:
        """Scan for available WiFi networks"""
        try:
            if platform.system().lower() == "linux":
                cmd = ["nmcli", "dev", "wifi", "list"]
            elif platform.system().lower() == "darwin":  # macOS
                cmd = ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-s"]
            else:
                return json.dumps({"error": "WiFi scanning not supported on this platform"})

            result = subprocess.run(cmd, capture_output=True, text=True)
            return json.dumps({
                "networks": result.stdout.split('\n'),
                "status": "success" if result.returncode == 0 else "failed",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, indent=2)
        except Exception as e:
            return json.dumps({"error": f"WiFi scan failed: {str(e)}"})

    def get_network_usage_by_process(self) -> str:
        """Get network usage statistics per process"""
        try:
            process_stats = []
            for proc in psutil.process_iter(['pid', 'name', 'connections', 'username']):
                try:
                    connections = proc.connections()
                    if connections:
                        process_stats.append({
                            'pid': proc.pid,
                            'name': proc.name(),
                            'username': proc.info['username'],
                            'connection_count': len(connections),
                            'connections': [{
                                'local_address': f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else None,
                                'remote_address': f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else None,
                                'status': c.status
                            } for c in connections]
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            return json.dumps({
                "processes": process_stats,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to get process network stats: {str(e)}"})

    def check_port_status(self, host: str, ports: List[int]) -> str:
        """Check if specific ports are open on a host"""
        results = []
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                sock.close()

                status = "open" if result == 0 else "closed"
                try:
                    service = socket.getservbyport(port) if result == 0 else "unknown"
                except:
                    service = "unknown"

                results.append({
                    "port": port,
                    "status": status,
                    "service": service
                })
            except Exception as e:
                results.append({
                    "port": port,
                    "status": "error",
                    "error": str(e)
                })

        return json.dumps({
            "host": host,
            "ports": results,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }, indent=2)

    def get_network_latency(self, host: str, count: int = 4) -> str:
        """Measure network latency to a host using ping"""
        try:
            if platform.system().lower() == "windows":
                cmd = ["ping", "-n", str(count), host]
            else:
                cmd = ["ping", "-c", str(count), host]

            result = subprocess.run(cmd, capture_output=True, text=True)
            return json.dumps({
                "host": host,
                "ping_output": result.stdout,
                "status": "success" if result.returncode == 0 else "failed",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Ping failed: {str(e)}"})


# Example usage
if __name__ == "__main__":
    from phi.agent import Agent
    from phi.model.openai import OpenAIChat

    # Initialize the agent with network tools
    agent = Agent(
        model=OpenAIChat(id="gpt-4"),
        tools=[NetworkTools()],
        markdown=True
    )

    # Example queries
    print("\nGetting network interfaces...")
    agent.print_response("Show me all network interfaces")

    print("\nChecking connection to Google...")
    agent.print_response("Check if I can connect to google.com on port 443")

    print("\nGetting bandwidth usage...")
    agent.print_response("Show my current bandwidth usage")

    print("\nChecking common ports...")
    agent.print_response("Check if ports 80,443,3306 are open on localhost")
