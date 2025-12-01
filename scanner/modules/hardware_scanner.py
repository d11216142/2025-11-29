"""
Hardware Scanner Module
Scans and collects hardware device information.
Similar to Device Manager on Windows, this module scans all available hardware.
"""
import platform
import subprocess
import re


class HardwareScanner:
    """Scanner for hardware device information."""
    
    def __init__(self):
        self.hardware_info = {}
    
    def scan(self):
        """Scan all hardware device information."""
        self.hardware_info = {
            'cpu': self._get_cpu_info(),
            'memory': self._get_memory_info(),
            'disks': self._get_disk_info(),
            'network': self._get_network_info(),
            'gpu': self._get_gpu_info(),
            'audio': self._get_audio_info(),
            'usb': self._get_usb_info(),
            'pci': self._get_pci_info(),
            'system_devices': self._get_system_devices(),
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
    
    def _get_gpu_info(self):
        """Get GPU/display adapter information."""
        gpu_info = []
        system = platform.system()
        
        if system == 'Linux':
            # Try lspci for GPU info
            try:
                result = subprocess.run(
                    ['lspci', '-v'],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    current_device = None
                    for line in result.stdout.split('\n'):
                        if line and not line.startswith('\t') and not line.startswith(' '):
                            # Check for VGA/3D/Display controller
                            if 'VGA' in line or '3D' in line or 'Display' in line:
                                parts = line.split(': ', 1)
                                if len(parts) > 1:
                                    current_device = {
                                        'name': parts[1].strip(),
                                        'type': 'GPU',
                                    }
                                    gpu_info.append(current_device)
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
            
            # Also check /proc/driver/nvidia if available (for NVIDIA GPUs)
            try:
                with open('/proc/driver/nvidia/version', 'r') as f:
                    version = f.read().strip()
                    for gpu in gpu_info:
                        if 'NVIDIA' in gpu.get('name', '').upper():
                            gpu['driver_version'] = version.split('\n')[0] if version else 'Unknown'
            except (FileNotFoundError, IOError):
                pass
                
        elif system == 'Windows':
            try:
                # Use WMIC to get GPU info
                result = subprocess.run(
                    ['wmic', 'path', 'win32_VideoController', 'get', 
                     'Name,AdapterRAM,DriverVersion', '/format:csv'],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n')[1:]:
                        parts = line.strip().split(',')
                        if len(parts) >= 4 and parts[2]:
                            gpu_info.append({
                                'name': parts[2],
                                'memory_bytes': parts[1] if parts[1] else 'Unknown',
                                'driver_version': parts[3] if len(parts) > 3 else 'Unknown',
                                'type': 'GPU',
                            })
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
                
        elif system == 'Darwin':  # macOS
            try:
                result = subprocess.run(
                    ['system_profiler', 'SPDisplaysDataType'],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    current_gpu = {}
                    for line in result.stdout.split('\n'):
                        line = line.strip()
                        if line.endswith(':') and not line.startswith('Displays') and not line.startswith('Graphics'):
                            if current_gpu and current_gpu.get('name'):
                                gpu_info.append(current_gpu)
                            current_gpu = {'name': line.rstrip(':'), 'type': 'GPU'}
                        elif 'Chipset Model:' in line:
                            current_gpu['name'] = line.split(':')[1].strip()
                        elif 'VRAM' in line:
                            current_gpu['vram'] = line.split(':')[1].strip()
                    if current_gpu and current_gpu.get('name'):
                        gpu_info.append(current_gpu)
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
        
        return gpu_info if gpu_info else [{'name': 'Unknown', 'type': 'GPU', 'error': 'Could not detect GPU'}]
    
    def _get_audio_info(self):
        """Get audio device information."""
        audio_info = []
        system = platform.system()
        
        if system == 'Linux':
            # Try lspci for audio controllers
            try:
                result = subprocess.run(
                    ['lspci'],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'Audio' in line or 'audio' in line:
                            parts = line.split(': ', 1)
                            if len(parts) > 1:
                                audio_info.append({
                                    'name': parts[1].strip(),
                                    'type': 'Audio Controller',
                                })
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
            
            # Also check ALSA sound cards
            try:
                with open('/proc/asound/cards', 'r') as f:
                    content = f.read()
                    # Parse card info
                    for line in content.split('\n'):
                        if line.strip() and line[0].isdigit():
                            # Format: " 0 [PCH            ]: HDA-Intel - HDA Intel PCH"
                            match = re.search(r'\d+\s+\[[^\]]+\]:\s+(.+)', line)
                            if match:
                                card_name = match.group(1).strip()
                                # Avoid duplicates
                                if not any(card_name in a.get('name', '') for a in audio_info):
                                    audio_info.append({
                                        'name': card_name,
                                        'type': 'Sound Card',
                                    })
            except (FileNotFoundError, IOError):
                pass
                
        elif system == 'Windows':
            try:
                result = subprocess.run(
                    ['wmic', 'sounddev', 'get', 'Name,Status', '/format:csv'],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n')[1:]:
                        parts = line.strip().split(',')
                        if len(parts) >= 2 and parts[1]:
                            audio_info.append({
                                'name': parts[1],
                                'status': parts[2] if len(parts) > 2 else 'Unknown',
                                'type': 'Audio Device',
                            })
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
                
        elif system == 'Darwin':
            try:
                result = subprocess.run(
                    ['system_profiler', 'SPAudioDataType'],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('Audio:') and line.endswith(':'):
                            audio_info.append({
                                'name': line.rstrip(':'),
                                'type': 'Audio Device',
                            })
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
        
        return audio_info if audio_info else []
    
    def _get_usb_info(self):
        """Get USB device information."""
        usb_info = []
        system = platform.system()
        
        if system == 'Linux':
            # Try lsusb
            try:
                result = subprocess.run(
                    ['lsusb'],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            # Format: Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
                            match = re.match(r'Bus\s+(\d+)\s+Device\s+(\d+):\s+ID\s+([0-9a-fA-F:]+)\s+(.+)', line)
                            if match:
                                usb_info.append({
                                    'bus': match.group(1),
                                    'device': match.group(2),
                                    'id': match.group(3),
                                    'name': match.group(4),
                                    'type': 'USB Device',
                                })
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
                
        elif system == 'Windows':
            try:
                result = subprocess.run(
                    ['wmic', 'path', 'Win32_USBHub', 'get', 'Name,DeviceID,Status', '/format:csv'],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n')[1:]:
                        parts = line.strip().split(',')
                        if len(parts) >= 3 and parts[1]:
                            usb_info.append({
                                'name': parts[2] if len(parts) > 2 else parts[1],
                                'device_id': parts[1],
                                'status': parts[3] if len(parts) > 3 else 'Unknown',
                                'type': 'USB Hub',
                            })
                
                # Also get USB controllers
                result = subprocess.run(
                    ['wmic', 'path', 'Win32_USBController', 'get', 'Name,DeviceID,Status', '/format:csv'],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n')[1:]:
                        parts = line.strip().split(',')
                        if len(parts) >= 3 and parts[1]:
                            usb_info.append({
                                'name': parts[2] if len(parts) > 2 else parts[1],
                                'device_id': parts[1],
                                'status': parts[3] if len(parts) > 3 else 'Unknown',
                                'type': 'USB Controller',
                            })
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
                
        elif system == 'Darwin':
            try:
                result = subprocess.run(
                    ['system_profiler', 'SPUSBDataType'],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    current_device = None
                    for line in result.stdout.split('\n'):
                        stripped = line.strip()
                        if stripped and stripped.endswith(':') and not stripped.startswith('USB'):
                            if current_device:
                                usb_info.append(current_device)
                            current_device = {'name': stripped.rstrip(':'), 'type': 'USB Device'}
                        elif current_device and 'Vendor ID:' in stripped:
                            current_device['vendor_id'] = stripped.split(':')[1].strip()
                        elif current_device and 'Product ID:' in stripped:
                            current_device['product_id'] = stripped.split(':')[1].strip()
                    if current_device:
                        usb_info.append(current_device)
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
        
        return usb_info if usb_info else []
    
    def _get_pci_info(self):
        """Get PCI device information."""
        pci_info = []
        system = platform.system()
        
        if system == 'Linux':
            try:
                result = subprocess.run(
                    ['lspci', '-nn'],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            # Format: 00:00.0 Host bridge [0600]: Intel Corporation...
                            match = re.match(r'([0-9a-fA-F:.]+)\s+([^:]+):\s+(.+)', line)
                            if match:
                                pci_info.append({
                                    'slot': match.group(1),
                                    'device_class': match.group(2).strip(),
                                    'name': match.group(3).strip(),
                                    'type': 'PCI Device',
                                })
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
                
        elif system == 'Windows':
            try:
                # Use wmic to get PCI devices via PnP entities
                result = subprocess.run(
                    ['wmic', 'path', 'Win32_PnPEntity', 'where', 
                     "DeviceID like 'PCI%'", 'get', 'Name,DeviceID,Status', '/format:csv'],
                    capture_output=True, text=True, timeout=60
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n')[1:]:
                        parts = line.strip().split(',')
                        if len(parts) >= 3 and parts[1]:
                            pci_info.append({
                                'device_id': parts[1],
                                'name': parts[2] if len(parts) > 2 else 'Unknown',
                                'status': parts[3] if len(parts) > 3 else 'Unknown',
                                'type': 'PCI Device',
                            })
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
                
        elif system == 'Darwin':
            try:
                result = subprocess.run(
                    ['system_profiler', 'SPPCIDataType'],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    current_device = None
                    for line in result.stdout.split('\n'):
                        stripped = line.strip()
                        if stripped and stripped.endswith(':') and not stripped.startswith('PCI'):
                            if current_device:
                                pci_info.append(current_device)
                            current_device = {'name': stripped.rstrip(':'), 'type': 'PCI Device'}
                        elif current_device and 'Vendor ID:' in stripped:
                            current_device['vendor_id'] = stripped.split(':')[1].strip()
                        elif current_device and 'Device ID:' in stripped:
                            current_device['device_id'] = stripped.split(':')[1].strip()
                    if current_device:
                        pci_info.append(current_device)
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
        
        return pci_info if pci_info else []
    
    def _get_system_devices(self):
        """Get other system devices (motherboard, BIOS, etc.)."""
        system_devices = []
        system = platform.system()
        
        if system == 'Linux':
            # Get DMI/SMBIOS info
            dmi_types = {
                '0': 'BIOS',
                '1': 'System',
                '2': 'Motherboard',
                '3': 'Chassis',
            }
            
            for dmi_type, device_type in dmi_types.items():
                try:
                    result = subprocess.run(
                        ['dmidecode', '-t', dmi_type],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode == 0:
                        info = {'type': device_type}
                        for line in result.stdout.split('\n'):
                            line = line.strip()
                            if ':' in line and not line.startswith('#'):
                                key, value = line.split(':', 1)
                                key = key.strip().lower().replace(' ', '_')
                                value = value.strip()
                                if value and key in ['manufacturer', 'product_name', 'version', 'vendor', 'serial_number']:
                                    info[key] = value
                        if len(info) > 1:  # Has more than just 'type'
                            # Create a name from available info
                            name_parts = []
                            if 'manufacturer' in info:
                                name_parts.append(info['manufacturer'])
                            elif 'vendor' in info:
                                name_parts.append(info['vendor'])
                            if 'product_name' in info:
                                name_parts.append(info['product_name'])
                            info['name'] = ' '.join(name_parts) if name_parts else device_type
                            system_devices.append(info)
                except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError):
                    pass
            
            # If dmidecode failed, try reading from /sys
            if not system_devices:
                dmi_paths = {
                    'System': '/sys/class/dmi/id/product_name',
                    'Motherboard': '/sys/class/dmi/id/board_name',
                    'BIOS': '/sys/class/dmi/id/bios_version',
                }
                for device_type, path in dmi_paths.items():
                    try:
                        with open(path, 'r') as f:
                            name = f.read().strip()
                            if name:
                                system_devices.append({
                                    'name': name,
                                    'type': device_type,
                                })
                    except (FileNotFoundError, IOError, PermissionError):
                        pass
                        
        elif system == 'Windows':
            try:
                # Get BIOS info
                result = subprocess.run(
                    ['wmic', 'bios', 'get', 'Manufacturer,Name,Version', '/format:csv'],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n')[1:]:
                        parts = line.strip().split(',')
                        if len(parts) >= 3 and parts[1]:
                            system_devices.append({
                                'name': f"{parts[1]} {parts[2]}" if len(parts) > 2 else parts[1],
                                'version': parts[3] if len(parts) > 3 else 'Unknown',
                                'type': 'BIOS',
                            })
                
                # Get motherboard info
                result = subprocess.run(
                    ['wmic', 'baseboard', 'get', 'Manufacturer,Product,Version', '/format:csv'],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n')[1:]:
                        parts = line.strip().split(',')
                        if len(parts) >= 3 and parts[1]:
                            system_devices.append({
                                'name': f"{parts[1]} {parts[2]}" if len(parts) > 2 else parts[1],
                                'version': parts[3] if len(parts) > 3 else 'Unknown',
                                'type': 'Motherboard',
                            })
                
                # Get system info
                result = subprocess.run(
                    ['wmic', 'computersystem', 'get', 'Manufacturer,Model', '/format:csv'],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n')[1:]:
                        parts = line.strip().split(',')
                        if len(parts) >= 3 and parts[1]:
                            system_devices.append({
                                'name': f"{parts[1]} {parts[2]}" if len(parts) > 2 else parts[1],
                                'type': 'System',
                            })
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
                
        elif system == 'Darwin':
            try:
                result = subprocess.run(
                    ['system_profiler', 'SPHardwareDataType'],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    info = {'type': 'System'}
                    for line in result.stdout.split('\n'):
                        stripped = line.strip()
                        if 'Model Name:' in stripped:
                            info['name'] = stripped.split(':')[1].strip()
                        elif 'Model Identifier:' in stripped:
                            info['model_id'] = stripped.split(':')[1].strip()
                        elif 'Serial Number' in stripped:
                            info['serial'] = stripped.split(':')[1].strip()
                    if 'name' in info:
                        system_devices.append(info)
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
        
        return system_devices if system_devices else []
    
    def get_info(self):
        """Return the collected hardware information."""
        if not self.hardware_info:
            self.scan()
        return self.hardware_info
