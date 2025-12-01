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
        
        # GPU/Display Adapters
        gpus = hardware_info.get('gpu', [])
        for gpu in gpus:
            if 'error' not in gpu:
                gpu_name = gpu.get('name', 'Unknown GPU')
                vendor = self._detect_hardware_vendor(gpu_name)
                version = gpu.get('driver_version', '*')
                
                cpe = self._generate_cpe(
                    part='h',
                    vendor=vendor,
                    product=self._sanitize_cpe_value(gpu_name),
                    version=version,
                )
                
                cpe_list.append({
                    'type': 'Hardware - GPU',
                    'name': gpu_name,
                    'vendor': vendor,
                    'product': gpu_name,
                    'version': version,
                    'cpe': cpe,
                })
        
        # Audio Devices
        audio_devices = hardware_info.get('audio', [])
        for audio in audio_devices:
            if 'error' not in audio:
                audio_name = audio.get('name', 'Unknown Audio Device')
                vendor = self._detect_hardware_vendor(audio_name)
                
                cpe = self._generate_cpe(
                    part='h',
                    vendor=vendor,
                    product=self._sanitize_cpe_value(audio_name),
                    version='*',
                )
                
                cpe_list.append({
                    'type': 'Hardware - Audio',
                    'name': audio_name,
                    'vendor': vendor,
                    'product': audio_name,
                    'version': '*',
                    'cpe': cpe,
                })
        
        # USB Devices
        usb_devices = hardware_info.get('usb', [])
        for usb in usb_devices:
            if 'error' not in usb:
                usb_name = usb.get('name', 'Unknown USB Device')
                vendor = self._detect_hardware_vendor(usb_name)
                device_type = usb.get('type', 'USB Device')
                
                cpe = self._generate_cpe(
                    part='h',
                    vendor=vendor,
                    product=self._sanitize_cpe_value(usb_name),
                    version='*',
                )
                
                cpe_list.append({
                    'type': f'Hardware - {device_type}',
                    'name': usb_name,
                    'vendor': vendor,
                    'product': usb_name,
                    'version': '*',
                    'cpe': cpe,
                })
        
        # PCI Devices
        pci_devices = hardware_info.get('pci', [])
        for pci in pci_devices:
            if 'error' not in pci:
                pci_name = pci.get('name', 'Unknown PCI Device')
                vendor = self._detect_hardware_vendor(pci_name)
                device_class = pci.get('device_class', 'PCI Device')
                
                cpe = self._generate_cpe(
                    part='h',
                    vendor=vendor,
                    product=self._sanitize_cpe_value(pci_name),
                    version='*',
                )
                
                cpe_list.append({
                    'type': f'Hardware - {device_class}',
                    'name': pci_name,
                    'vendor': vendor,
                    'product': pci_name,
                    'version': '*',
                    'cpe': cpe,
                })
        
        # System Devices (BIOS, Motherboard, etc.)
        system_devices = hardware_info.get('system_devices', [])
        for device in system_devices:
            if 'error' not in device:
                device_name = device.get('name', 'Unknown System Device')
                device_type = device.get('type', 'System Device')
                vendor = device.get('manufacturer', device.get('vendor', ''))
                if not vendor:
                    vendor = self._detect_hardware_vendor(device_name)
                version = device.get('version', '*')
                
                cpe = self._generate_cpe(
                    part='h',
                    vendor=vendor,
                    product=self._sanitize_cpe_value(device_name),
                    version=version,
                )
                
                cpe_list.append({
                    'type': f'Hardware - {device_type}',
                    'name': device_name,
                    'vendor': vendor,
                    'product': device_name,
                    'version': version,
                    'cpe': cpe,
                })
        
        return cpe_list
    
    def _detect_hardware_vendor(self, name):
        """Detect hardware vendor from device name."""
        if not name:
            return 'unknown'
        
        name_lower = name.lower()
        
        # Direct vendor name mappings
        vendor_keywords = {
            'intel': 'intel',
            'amd': 'amd',
            'nvidia': 'nvidia',
            'realtek': 'realtek',
            'broadcom': 'broadcom',
            'qualcomm': 'qualcomm',
            'marvell': 'marvell',
            'samsung': 'samsung',
            'western digital': 'western_digital',
            'seagate': 'seagate',
            'sandisk': 'sandisk',
            'kingston': 'kingston',
            'corsair': 'corsair',
            'asus': 'asus',
            'msi': 'msi',
            'gigabyte': 'gigabyte',
            'asrock': 'asrock',
            'dell': 'dell',
            'hp': 'hp',
            'lenovo': 'lenovo',
            'acer': 'acer',
            'apple': 'apple',
            'microsoft': 'microsoft',
            'logitech': 'logitech',
            'razer': 'razer',
            'creative': 'creative',
            'conexant': 'conexant',
            'via': 'via',
            'linux foundation': 'linux',
        }
        
        # Product/brand names that map to their parent vendor
        product_to_vendor = {
            'ati': 'amd',       # ATI is now AMD
            'radeon': 'amd',   # Radeon is AMD product line
            'geforce': 'nvidia',  # GeForce is NVIDIA product line
        }
        
        # Check direct vendor keywords first
        for keyword, vendor in vendor_keywords.items():
            if keyword in name_lower:
                return vendor
        
        # Check product-to-vendor mappings
        for product, vendor in product_to_vendor.items():
            if product in name_lower:
                return vendor
        
        return 'unknown'
    
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
