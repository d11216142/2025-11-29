#!/usr/bin/env python3
"""
System Scanner - Main Entry Point
Scans operating system, hardware, and software information,
converts to CPE format, and exports to Excel.
"""
import argparse
import os
import sys
from datetime import datetime

from modules import OSScanner, HardwareScanner, SoftwareScanner
from cpe_converter import CPEConverter
from excel_exporter import ExcelExporter


def main():
    """Main function to run the system scanner."""
    parser = argparse.ArgumentParser(
        description='System Scanner - Scan OS, hardware, and software, convert to CPE format, and export to Excel'
    )
    parser.add_argument(
        '-o', '--output',
        default=f'system_scan_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
        help='Output Excel file path (default: system_scan_<timestamp>.xlsx)'
    )
    parser.add_argument(
        '-d', '--detailed',
        action='store_true',
        help='Generate detailed report with multiple sheets'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--skip-software',
        action='store_true',
        help='Skip software scanning (faster)'
    )
    parser.add_argument(
        '--limit-software',
        type=int,
        default=0,
        help='Limit the number of software items to include (0 = no limit)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  System Scanner - CPE Format Generator")
    print("=" * 60)
    print()
    
    # Initialize scanners
    os_scanner = OSScanner()
    hardware_scanner = HardwareScanner()
    software_scanner = SoftwareScanner()
    
    # Scan OS
    print("[1/4] Scanning Operating System...")
    os_info = os_scanner.scan()
    if args.verbose:
        print(f"      System: {os_info.get('system', 'Unknown')}")
        print(f"      Release: {os_info.get('release', 'Unknown')}")
        print(f"      Platform: {os_info.get('platform', 'Unknown')}")
    print("      Done!")
    
    # Scan Hardware
    print("\n[2/4] Scanning Hardware...")
    hardware_info = hardware_scanner.scan()
    if args.verbose:
        cpu = hardware_info.get('cpu', {})
        print(f"      CPU: {cpu.get('model', cpu.get('processor', 'Unknown'))}")
        memory = hardware_info.get('memory', {})
        print(f"      Memory: {memory.get('total_gb', 'Unknown')} GB")
        print(f"      Disks: {len(hardware_info.get('disks', []))} partition(s)")
    print("      Done!")
    
    # Scan Software
    if args.skip_software:
        print("\n[3/4] Skipping Software Scan (--skip-software)")
        software_list = []
    else:
        print("\n[3/4] Scanning Installed Software...")
        print("      (This may take a while...)")
        software_list = software_scanner.scan()
        
        if args.limit_software > 0:
            software_list = software_list[:args.limit_software]
        
        if args.verbose:
            print(f"      Found {len(software_list)} software package(s)")
        print("      Done!")
    
    # Convert to CPE format
    print("\n[4/4] Converting to CPE Format...")
    cpe_converter = CPEConverter()
    cpe_data = cpe_converter.convert_all(os_info, hardware_info, software_list)
    if args.verbose:
        print(f"      Generated {len(cpe_data)} CPE entries")
    print("      Done!")
    
    # Export to Excel
    print("\n" + "=" * 60)
    print("Exporting to Excel...")
    exporter = ExcelExporter()
    
    if args.detailed:
        output_file = exporter.export_detailed(
            os_info, hardware_info, software_list, cpe_data, args.output
        )
    else:
        output_file = exporter.export(cpe_data, args.output)
    
    print(f"\nReport saved to: {os.path.abspath(output_file)}")
    print()
    
    # Print summary
    print("=" * 60)
    print("  Summary")
    print("=" * 60)
    print(f"  Operating System:    {os_info.get('platform', 'Unknown')}")
    print(f"  Hardware Components: {len([item for item in cpe_data if 'Hardware' in item.get('type', '')])}")
    print(f"  Software Packages:   {len([item for item in cpe_data if 'Software' in item.get('type', '')])}")
    print(f"  Total CPE Entries:   {len(cpe_data)}")
    print("=" * 60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
