"""
Software Scanner Module
Scans and collects installed software information.
"""
import platform
import subprocess
import re


class SoftwareScanner:
    """Scanner for installed software information."""
    
    def __init__(self):
        self.software_list = []
    
    def scan(self):
        """Scan installed software based on the operating system."""
        system = platform.system()
        
        if system == 'Linux':
            self.software_list = self._scan_linux()
        elif system == 'Windows':
            self.software_list = self._scan_windows()
        elif system == 'Darwin':  # macOS
            self.software_list = self._scan_macos()
        else:
            self.software_list = [{'error': f'Unsupported OS: {system}'}]
        
        return self.software_list
    
    def _scan_linux(self):
        """Scan installed software on Linux systems."""
        software = []
        
        # Try dpkg (Debian/Ubuntu)
        try:
            result = subprocess.run(
                ['dpkg-query', '-W', '-f=${Package}\t${Version}\t${Status}\n'],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    parts = line.split('\t')
                    if len(parts) < 2:
                        continue
                    # Check if package is installed (for dpkg, status is in the third column)
                    is_installed = True
                    if len(parts) > 2:
                        is_installed = 'installed' in parts[-1]
                    if is_installed:
                        software.append({
                            'name': parts[0],
                            'version': parts[1] if len(parts) > 1 else 'Unknown',
                            'vendor': 'Unknown',
                            'type': 'dpkg',
                        })
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Try rpm (Red Hat/CentOS/Fedora) if no dpkg packages found
        if not software:
            try:
                result = subprocess.run(
                    ['rpm', '-qa', '--queryformat', '%{NAME}\t%{VERSION}\t%{VENDOR}\n'],
                    capture_output=True, text=True, timeout=60
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            parts = line.split('\t')
                            software.append({
                                'name': parts[0],
                                'version': parts[1] if len(parts) > 1 else 'Unknown',
                                'vendor': parts[2] if len(parts) > 2 else 'Unknown',
                                'type': 'rpm',
                            })
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
        
        # Also scan snap packages
        try:
            result = subprocess.run(
                ['snap', 'list'],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 2:
                        software.append({
                            'name': parts[0],
                            'version': parts[1],
                            'vendor': 'Snap Store',
                            'type': 'snap',
                        })
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Also scan flatpak packages
        try:
            result = subprocess.run(
                ['flatpak', 'list', '--columns=application,version'],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    parts = line.split('\t')
                    if len(parts) >= 1:
                        software.append({
                            'name': parts[0],
                            'version': parts[1] if len(parts) > 1 else 'Unknown',
                            'vendor': 'Flathub',
                            'type': 'flatpak',
                        })
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return software
    
    def _scan_windows(self):
        """Scan installed software on Windows systems."""
        software = []
        
        try:
            # Use PowerShell to get installed programs with error handling
            # Try-Catch handles permission issues when accessing registry
            ps_script = '''
            $ErrorActionPreference = "SilentlyContinue"
            try {
                Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* -ErrorAction SilentlyContinue |
                Select-Object DisplayName, DisplayVersion, Publisher |
                Where-Object {$_.DisplayName -ne $null} |
                ForEach-Object { "$($_.DisplayName)`t$($_.DisplayVersion)`t$($_.Publisher)" }
            } catch {
                # Silently handle permission errors
            }
            try {
                Get-ItemProperty HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* -ErrorAction SilentlyContinue |
                Select-Object DisplayName, DisplayVersion, Publisher |
                Where-Object {$_.DisplayName -ne $null} |
                ForEach-Object { "$($_.DisplayName)`t$($_.DisplayVersion)`t$($_.Publisher)" }
            } catch {
                # Silently handle permission errors
            }
            '''
            
            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True, text=True, timeout=120
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    parts = line.split('\t')
                    if len(parts) >= 1 and parts[0]:
                        software.append({
                            'name': parts[0],
                            'version': parts[1] if len(parts) > 1 else 'Unknown',
                            'vendor': parts[2] if len(parts) > 2 else 'Unknown',
                            'type': 'windows',
                        })
        except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError):
            software.append({'error': 'Unable to scan Windows software'})
        
        return software
    
    def _scan_macos(self):
        """Scan installed software on macOS systems."""
        software = []
        
        try:
            # Get applications from /Applications
            result = subprocess.run(
                ['ls', '/Applications'],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                for app in result.stdout.strip().split('\n'):
                    if app.endswith('.app'):
                        app_name = app.replace('.app', '')
                        software.append({
                            'name': app_name,
                            'version': 'Unknown',
                            'vendor': 'Unknown',
                            'type': 'macos_app',
                        })
            
            # Get brew packages if available
            result = subprocess.run(
                ['brew', 'list', '--versions'],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    parts = line.split()
                    if len(parts) >= 2:
                        software.append({
                            'name': parts[0],
                            'version': parts[1],
                            'vendor': 'Homebrew',
                            'type': 'brew',
                        })
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return software
    
    def get_info(self):
        """Return the collected software information."""
        if not self.software_list:
            self.scan()
        return self.software_list
