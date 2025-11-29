# System Scanner (系統掃描軟體)

A Python-based system scanner that collects information about your computer's operating system, hardware, and software, converts it to CPE (Common Platform Enumeration) format, and exports the data to an Excel file.

## Features

- **OS Scanning**: Detects operating system type, version, and distribution information
- **Hardware Scanning**: Collects CPU, memory, disk, and network interface information
- **Software Scanning**: Lists installed software packages (supports dpkg, rpm, snap, flatpak on Linux; Windows registry; macOS applications and Homebrew)
- **CPE Format Conversion**: Converts all collected data to CPE 2.3 format for standardized vulnerability assessment
- **Excel Export**: Generates a well-formatted Excel report with multiple sheets

## Installation

1. Clone the repository:
```bash
git clone https://github.com/d11216142/2025-11-29.git
cd 2025-11-29
```

2. Install dependencies:
```bash
cd scanner
pip install -r requirements.txt
```

## Usage

Basic usage:
```bash
cd scanner
python scanner.py
```

This will scan your system and generate an Excel file named `system_scan_<timestamp>.xlsx`.

### Command Line Options

```
Options:
  -o, --output FILE      Output Excel file path (default: system_scan_<timestamp>.xlsx)
  -d, --detailed         Generate detailed report with multiple sheets
  -v, --verbose          Enable verbose output
  --skip-software        Skip software scanning (faster)
  --limit-software N     Limit the number of software items to include (0 = no limit)
```

### Examples

Generate a detailed report:
```bash
python scanner.py -d -o my_report.xlsx
```

Quick scan (skip software):
```bash
python scanner.py --skip-software
```

Verbose output with software limit:
```bash
python scanner.py -v --limit-software 100
```

## Output Format

### CPE Format

The scanner converts all collected data to CPE 2.3 format:
```
cpe:2.3:part:vendor:product:version:update:edition:language:sw_edition:target_sw:target_hw:other
```

Where:
- `part`: `a` (application), `o` (operating system), or `h` (hardware)
- `vendor`: The vendor/manufacturer name
- `product`: The product name
- `version`: The version string
- Other fields default to `*` (any)

### Excel Report Structure

The generated Excel file contains:

1. **System Scan Report / CPE Report**: Main sheet with all CPE entries
2. **OS Information** (detailed mode): Raw OS data
3. **Hardware Info** (detailed mode): Raw hardware data
4. **Software List** (detailed mode): All detected software
5. **Summary**: Scan statistics and overview

## Supported Platforms

- **Linux**: Ubuntu, Debian, Fedora, CentOS, RHEL, and other distributions
- **Windows**: Windows 10, Windows 11, and Windows Server
- **macOS**: macOS (Darwin)

## Requirements

- Python 3.8+
- openpyxl >= 3.1.0
- psutil >= 5.9.0

## License

MIT License