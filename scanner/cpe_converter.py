"""
CPE (Common Platform Enumeration) Converter Module
Converts system information to CPE 2.3 format.

CPE 2.3 format: cpe:2.3:part:vendor:product:version:update:edition:language:sw_edition:target_sw:target_hw:other
Part values: a = application, o = operating system, h = hardware device
"""
import re
import platform


class CPEConverter:
    """Converter for system information to CPE format."""
    
    # Known vendor mappings for common software
    VENDOR_MAPPINGS = {
        'microsoft': 'microsoft',
        'google': 'google',
        'mozilla': 'mozilla',
        'apple': 'apple',
        'oracle': 'oracle',
        'adobe': 'adobe',
        'canonical': 'canonical',
        'redhat': 'redhat',
        'red hat': 'redhat',
        'debian': 'debian',
        'ubuntu': 'canonical',
        'fedora': 'fedoraproject',
        'centos': 'centos',
        'suse': 'suse',
        'intel': 'intel',
        'amd': 'amd',
        'nvidia': 'nvidia',
        'linux': 'linux',
        'python': 'python',
        'node': 'nodejs',
        'nodejs': 'nodejs',
    }
    
    # OS mappings
    OS_MAPPINGS = {
        'linux': ('linux', 'linux_kernel'),
        'windows': ('microsoft', 'windows'),
        'darwin': ('apple', 'macos'),
    }
    
    def __init__(self):
        self.cpe_list = []
    
    def _sanitize_cpe_value(self, value):
        """
        Sanitize a value for use in CPE format.
        Replace special characters and spaces with underscores.
        """
        if not value or value == 'Unknown':
            return '*'
        
        # Convert to lowercase
        value = str(value).lower()
        
        # Replace spaces and special characters with underscores
        value = re.sub(r'[^a-z0-9._-]', '_', value)
        
        # Remove leading/trailing underscores
        value = value.strip('_')
        
        # Replace multiple underscores with single
        value = re.sub(r'_+', '_', value)
        
        return value if value else '*'
    
    def _format_version(self, version):
        """Format version string for CPE."""
        if not version or version == 'Unknown':
            return '*'
        
        # Extract version numbers
        version = str(version)
        
        # Remove common prefixes
        version = re.sub(r'^[vV]', '', version)
        
        # Sanitize for CPE
        return self._sanitize_cpe_value(version)
    
    def _generate_cpe(self, part, vendor, product, version='*', update='*', 
                      edition='*', language='*', sw_edition='*', 
                      target_sw='*', target_hw='*', other='*'):
        """
        Generate a CPE 2.3 formatted string.
        
        Args:
            part: 'a' for application, 'o' for OS, 'h' for hardware
            vendor: Vendor name
            product: Product name
            version: Version string
            update: Update/patch level
            edition: Edition
            language: Language
            sw_edition: Software edition
            target_sw: Target software
            target_hw: Target hardware
            other: Other attributes
        
        Returns:
            CPE 2.3 formatted string
        """
        components = [
            'cpe', '2.3', part,
            self._sanitize_cpe_value(vendor),
            self._sanitize_cpe_value(product),
            self._format_version(version),
            self._sanitize_cpe_value(update),
            self._sanitize_cpe_value(edition),
            self._sanitize_cpe_value(language),
            self._sanitize_cpe_value(sw_edition),
            self._sanitize_cpe_value(target_sw),
            self._sanitize_cpe_value(target_hw),
            self._sanitize_cpe_value(other),
        ]
        
        return ':'.join(components)
    
    def _get_vendor_from_name(self, name, vendor_hint=None):
        """Try to determine vendor from product name or hint."""
        if vendor_hint and vendor_hint != 'Unknown':
            return vendor_hint
        
        name_lower = name.lower()
        
        for key, vendor in self.VENDOR_MAPPINGS.items():
            if key in name_lower:
                return vendor
        
        # If no match found, use first word as vendor
        first_word = name.split()[0] if name else 'unknown'
        return self._sanitize_cpe_value(first_word)
    
    def convert_os(self, os_info):
        """
        Convert OS information to CPE format.
        
        Args:
            os_info: Dictionary containing OS information
        
        Returns:
            CPE formatted string for the OS
        """
        system = os_info.get('system', 'Unknown').lower()
        
        if system in self.OS_MAPPINGS:
            vendor, product = self.OS_MAPPINGS[system]
        else:
            vendor = 'unknown'
            product = system
        
        # Get version
        if system == 'linux':
            # Use distro info if available
            distro_id = os_info.get('distro_id', '')
            distro_name = os_info.get('distro_name', '')
            version = os_info.get('distro_version', os_info.get('release', '*'))
            
            if distro_id:
                product = distro_id
                if distro_id in self.VENDOR_MAPPINGS:
                    vendor = self.VENDOR_MAPPINGS[distro_id]
                else:
                    # Use sanitization for consistent formatting
                    vendor = self._sanitize_cpe_value(distro_id)
        elif system == 'windows':
            version = os_info.get('release', '*')
            edition = os_info.get('win_edition', '*')
        else:
            version = os_info.get('release', '*')
        
        cpe = self._generate_cpe(
            part='o',
            vendor=vendor,
            product=product,
            version=version,
            target_hw=os_info.get('machine', '*')
        )
        
        return {
            'type': 'Operating System',
            'name': os_info.get('platform', f"{system} {version}"),
            'vendor': vendor,
            'product': product,
            'version': version,
            'cpe': cpe,
        }
    
    def convert_hardware(self, hardware_info):
        """
        Convert hardware information to CPE format.
        
        Args:
            hardware_info: Dictionary containing hardware information
        
        Returns:
            List of CPE formatted dictionaries for hardware
        """
        cpe_list = []
        
        # CPU
        cpu_info = hardware_info.get('cpu', {})
        if cpu_info:
            cpu_model = cpu_info.get('model', cpu_info.get('processor', 'Unknown'))
            
            # Try to determine vendor
            vendor = 'unknown'
            cpu_lower = cpu_model.lower()
            if 'intel' in cpu_lower:
                vendor = 'intel'
            elif 'amd' in cpu_lower:
                vendor = 'amd'
            elif 'arm' in cpu_lower:
                vendor = 'arm'
            
            cpe = self._generate_cpe(
                part='h',
                vendor=vendor,
                product=self._sanitize_cpe_value(cpu_model),
                version='*',
            )
            
            cpe_list.append({
                'type': 'Hardware - CPU',
                'name': cpu_model,
                'vendor': vendor,
                'product': cpu_model,
                'version': '*',
                'cpe': cpe,
            })
        
        # Memory (generic hardware entry)
        memory_info = hardware_info.get('memory', {})
        if memory_info and 'total_gb' in memory_info:
            cpe = self._generate_cpe(
                part='h',
                vendor='generic',
                product='memory',
                version=f"{memory_info['total_gb']}gb",
            )
            
            cpe_list.append({
                'type': 'Hardware - Memory',
                'name': f"System Memory ({memory_info['total_gb']} GB)",
                'vendor': 'generic',
                'product': 'memory',
                'version': f"{memory_info['total_gb']}gb",
                'cpe': cpe,
            })
        
        # Disks
        disks = hardware_info.get('disks', [])
        for i, disk in enumerate(disks):
            if 'error' not in disk:
                device_name = disk.get('device', f'disk{i}')
                cpe = self._generate_cpe(
                    part='h',
                    vendor='generic',
                    product='storage',
                    version=f"{disk.get('total_gb', 0)}gb",
                )
                
                cpe_list.append({
                    'type': 'Hardware - Storage',
                    'name': f"{device_name} ({disk.get('total_gb', 'Unknown')} GB)",
                    'vendor': 'generic',
                    'product': 'storage',
                    'version': f"{disk.get('total_gb', 0)}gb",
                    'cpe': cpe,
                })
        
        return cpe_list
    
    def convert_software(self, software_list):
        """
        Convert software information to CPE format.
        
        Args:
            software_list: List of software dictionaries
        
        Returns:
            List of CPE formatted dictionaries for software
        """
        cpe_list = []
        
        for software in software_list:
            if 'error' in software:
                continue
            
            name = software.get('name', 'Unknown')
            version = software.get('version', '*')
            vendor_hint = software.get('vendor', 'Unknown')
            
            vendor = self._get_vendor_from_name(name, vendor_hint)
            
            cpe = self._generate_cpe(
                part='a',
                vendor=vendor,
                product=self._sanitize_cpe_value(name),
                version=version,
            )
            
            cpe_list.append({
                'type': f"Software ({software.get('type', 'unknown')})",
                'name': name,
                'vendor': vendor,
                'product': name,
                'version': version,
                'cpe': cpe,
            })
        
        return cpe_list
    
    def convert_all(self, os_info, hardware_info, software_list):
        """
        Convert all system information to CPE format.
        
        Args:
            os_info: Dictionary containing OS information
            hardware_info: Dictionary containing hardware information
            software_list: List of software dictionaries
        
        Returns:
            List of all CPE formatted dictionaries
        """
        self.cpe_list = []
        
        # Convert OS
        self.cpe_list.append(self.convert_os(os_info))
        
        # Convert Hardware
        self.cpe_list.extend(self.convert_hardware(hardware_info))
        
        # Convert Software
        self.cpe_list.extend(self.convert_software(software_list))
        
        return self.cpe_list
