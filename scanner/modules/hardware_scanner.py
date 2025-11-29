"""
Hardware Scanner Module
Scans and collects hardware device information.
"""
import platform
import subprocess


class HardwareScanner:
    """Scanner for hardware device information."""
    
    def __init__(self):
        self.hardware_info = {}
    
    def scan(self):
        """Scan hardware device information."""
        self.hardware_info = {
            'cpu': self._get_cpu_info(),
            'memory': self._get_memory_info(),
            'disks': self._get_disk_info(),
            'network': self._get_network_info(),
        }
        return self.hardware_info
    
    def _get_cpu_info(self):
        """Get CPU information."""
        cpu_info = {
            'processor': platform.processor(),
            'machine': platform.machine(),
            'architecture': platform.architecture()[0],
        }
        
        # Try to get more details using psutil
        try:
            import psutil
            cpu_info['physical_cores'] = psutil.cpu_count(logical=False)
            cpu_info['logical_cores'] = psutil.cpu_count(logical=True)
            cpu_info['frequency_mhz'] = psutil.cpu_freq().current if psutil.cpu_freq() else 'N/A'
        except ImportError:
            pass
        
        # Try to get CPU model on Linux
        if platform.system() == 'Linux':
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if 'model name' in line:
                            cpu_info['model'] = line.split(':')[1].strip()
                            break
            except (FileNotFoundError, IOError):
                pass
        
        return cpu_info
    
    def _get_memory_info(self):
        """Get memory information."""
        memory_info = {}
        
        try:
            import psutil
            mem = psutil.virtual_memory()
            memory_info['total_gb'] = round(mem.total / (1024**3), 2)
            memory_info['available_gb'] = round(mem.available / (1024**3), 2)
            memory_info['used_gb'] = round(mem.used / (1024**3), 2)
            memory_info['percent_used'] = mem.percent
        except ImportError:
            memory_info['error'] = 'psutil not installed'
        
        return memory_info
    
    def _get_disk_info(self):
        """Get disk information."""
        disks = []
        
        try:
            import psutil
            partitions = psutil.disk_partitions()
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk = {
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total_gb': round(usage.total / (1024**3), 2),
                        'used_gb': round(usage.used / (1024**3), 2),
                        'free_gb': round(usage.free / (1024**3), 2),
                        'percent_used': usage.percent,
                    }
                    disks.append(disk)
                except (PermissionError, OSError):
                    disks.append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'error': 'Permission denied or unavailable',
                    })
        except ImportError:
            disks.append({'error': 'psutil not installed'})
        
        return disks
    
    def _get_network_info(self):
        """Get network interface information."""
        network_info = []
        
        try:
            import psutil
            interfaces = psutil.net_if_addrs()
            for interface_name, addresses in interfaces.items():
                interface = {
                    'name': interface_name,
                    'addresses': []
                }
                for addr in addresses:
                    interface['addresses'].append({
                        'family': str(addr.family),
                        'address': addr.address,
                        'netmask': addr.netmask,
                    })
                network_info.append(interface)
        except ImportError:
            network_info.append({'error': 'psutil not installed'})
        
        return network_info
    
    def get_info(self):
        """Return the collected hardware information."""
        if not self.hardware_info:
            self.scan()
        return self.hardware_info
