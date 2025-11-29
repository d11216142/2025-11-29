"""
Operating System Scanner Module
Scans and collects operating system information.
"""
import platform
import sys


class OSScanner:
    """Scanner for operating system information."""
    
    def __init__(self):
        self.os_info = {}
    
    def scan(self):
        """Scan operating system information."""
        self.os_info = {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'node': platform.node(),
            'platform': platform.platform(),
            'python_version': sys.version.split()[0],
        }
        
        # Get additional info for different OS
        if platform.system() == 'Linux':
            try:
                import distro
                self.os_info['distro_name'] = distro.name()
                self.os_info['distro_version'] = distro.version()
                self.os_info['distro_id'] = distro.id()
            except ImportError:
                # Try to read from /etc/os-release
                try:
                    with open('/etc/os-release', 'r') as f:
                        for line in f:
                            if line.startswith('NAME='):
                                self.os_info['distro_name'] = line.split('=')[1].strip().strip('"')
                            elif line.startswith('VERSION_ID='):
                                self.os_info['distro_version'] = line.split('=')[1].strip().strip('"')
                            elif line.startswith('ID='):
                                self.os_info['distro_id'] = line.split('=')[1].strip().strip('"')
                except FileNotFoundError:
                    pass
        elif platform.system() == 'Windows':
            self.os_info['win_edition'] = platform.win32_edition() if hasattr(platform, 'win32_edition') else 'Unknown'
            
        return self.os_info
    
    def get_info(self):
        """Return the collected OS information."""
        if not self.os_info:
            self.scan()
        return self.os_info
