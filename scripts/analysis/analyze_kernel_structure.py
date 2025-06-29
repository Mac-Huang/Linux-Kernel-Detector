#!/usr/bin/env python3
"""
Linux Kernel Structure Analyzer
Analyzes the Linux kernel repository to identify potential anti-pattern categories
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Set
import re

class KernelAnalyzer:
    def __init__(self, kernel_path: str = None):
        self.kernel_path = kernel_path or "linux"
        self.analysis_results = {}
        
    def clone_kernel_if_needed(self):
        """Clone the Linux kernel repository if it doesn't exist"""
        if not os.path.exists(self.kernel_path):
            print(f"Cloning Linux kernel to {self.kernel_path}...")
            subprocess.run([
                "git", "clone", "--depth", "1", 
                "https://github.com/torvalds/linux.git", 
                self.kernel_path
            ], check=True)
        else:
            print(f"Kernel repository already exists at {self.kernel_path}")
    
    def analyze_directory_structure(self) -> Dict:
        """Analyze the main directory structure of the kernel"""
        print("Analyzing kernel directory structure...")
        
        structure = {
            "main_directories": [],
            "file_types": {},
            "total_files": 0,
            "total_lines": 0
        }
        
        kernel_dir = Path(self.kernel_path)
        
        # Main directories from the kernel structure
        main_dirs = [
            "arch", "block", "certs", "crypto", "drivers", "fs", 
            "include", "init", "io_uring", "ipc", "kernel", "lib", 
            "mm", "net", "rust", "samples", "scripts", "security", 
            "sound", "tools", "usr", "virt", "Documentation"
        ]
        
        for dir_name in main_dirs:
            dir_path = kernel_dir / dir_name
            if dir_path.exists():
                structure["main_directories"].append({
                    "name": dir_name,
                    "exists": True,
                    "description": self.get_directory_description(dir_name)
                })
        
        return structure
    
    def get_directory_description(self, dir_name: str) -> str:
        """Get description for each main directory"""
        descriptions = {
            "arch": "Architecture-specific code (x86, ARM, etc.)",
            "block": "Block device subsystem",
            "certs": "Certificate handling",
            "crypto": "Cryptographic API",
            "drivers": "Device drivers",
            "fs": "File system implementations",
            "include": "Header files",
            "init": "Kernel initialization",
            "io_uring": "Asynchronous I/O interface",
            "ipc": "Inter-process communication",
            "kernel": "Core kernel functionality",
            "lib": "Kernel libraries",
            "mm": "Memory management",
            "net": "Networking subsystem",
            "rust": "Rust language support",
            "samples": "Sample code and examples",
            "scripts": "Build and utility scripts",
            "security": "Security framework",
            "sound": "Audio subsystem",
            "tools": "Development tools",
            "usr": "User space utilities",
            "virt": "Virtualization support",
            "Documentation": "Kernel documentation"
        }
        return descriptions.get(dir_name, "Unknown directory")
    
    def identify_anti_pattern_categories(self) -> Dict:
        """Identify categories of anti-patterns commonly found in kernel code"""
        print("Identifying anti-pattern categories...")
        
        categories = {
            "memory_management": {
                "description": "Memory leaks, use-after-free, double-free",
                "patterns": [
                    "kmalloc without kfree",
                    "use after free",
                    "double free",
                    "memory leak",
                    "null pointer dereference"
                ],
                "directories": ["drivers", "kernel", "mm", "fs"]
            },
            "concurrency": {
                "description": "Race conditions, deadlocks, improper locking",
                "patterns": [
                    "race condition",
                    "deadlock",
                    "missing lock",
                    "double lock",
                    "lock ordering violation"
                ],
                "directories": ["kernel", "drivers", "fs", "net"]
            },
            "error_handling": {
                "description": "Improper error handling, unchecked return values",
                "patterns": [
                    "unchecked return value",
                    "missing error handling",
                    "ignored error code",
                    "wrong error propagation"
                ],
                "directories": ["drivers", "fs", "net", "kernel"]
            },
            "security": {
                "description": "Security vulnerabilities, privilege escalation",
                "patterns": [
                    "buffer overflow",
                    "format string vulnerability",
                    "privilege escalation",
                    "information disclosure"
                ],
                "directories": ["security", "drivers", "fs", "net"]
            },
            "performance": {
                "description": "Performance bottlenecks, inefficient algorithms",
                "patterns": [
                    "O(n²) algorithm",
                    "unnecessary memory allocation",
                    "inefficient data structure",
                    "cache miss pattern"
                ],
                "directories": ["kernel", "drivers", "fs", "mm"]
            },
            "code_quality": {
                "description": "Code style violations, maintainability issues",
                "patterns": [
                    "magic numbers",
                    "hardcoded values",
                    "complex functions",
                    "code duplication"
                ],
                "directories": ["drivers", "fs", "net", "kernel"]
            },
            "api_usage": {
                "description": "Incorrect API usage, deprecated functions",
                "patterns": [
                    "deprecated function",
                    "wrong API usage",
                    "missing parameter validation",
                    "incorrect flags"
                ],
                "directories": ["drivers", "fs", "net", "kernel"]
            }
        }
        
        return categories
    
    def analyze_file_patterns(self) -> Dict:
        """Analyze file patterns to understand code distribution"""
        print("Analyzing file patterns...")
        
        patterns = {
            "c_files": 0,
            "h_files": 0,
            "makefiles": 0,
            "kconfig_files": 0,
            "documentation_files": 0,
            "script_files": 0
        }
        
        kernel_dir = Path(self.kernel_path)
        
        for file_path in kernel_dir.rglob("*"):
            if file_path.is_file():
                suffix = file_path.suffix.lower()
                if suffix == ".c":
                    patterns["c_files"] += 1
                elif suffix == ".h":
                    patterns["h_files"] += 1
                elif file_path.name.lower() in ["makefile", "kbuild"]:
                    patterns["makefiles"] += 1
                elif suffix == ".rst" or suffix == ".txt":
                    patterns["documentation_files"] += 1
                elif suffix in [".sh", ".py", ".pl"]:
                    patterns["script_files"] += 1
                elif suffix == "" and "kconfig" in file_path.name.lower():
                    patterns["kconfig_files"] += 1
        
        return patterns
    
    def generate_analysis_report(self) -> Dict:
        """Generate a comprehensive analysis report"""
        print("Generating analysis report...")
        
        report = {
            "kernel_info": {
                "repository": "https://github.com/torvalds/linux.git",
                "description": "Linux kernel source tree",
                "primary_language": "C (98.3%)",
                "other_languages": ["Assembly", "Shell", "Python", "Makefile", "Rust"]
            },
            "structure_analysis": self.analyze_directory_structure(),
            "anti_pattern_categories": self.identify_anti_pattern_categories(),
            "file_patterns": self.analyze_file_patterns(),
            "recommendations": {
                "focus_areas": [
                    "drivers/ - Most anti-patterns due to diverse hardware support",
                    "fs/ - File system complexity leads to concurrency issues",
                    "net/ - Networking code has security and performance concerns",
                    "kernel/ - Core functionality requires careful analysis"
                ],
                "analysis_priorities": [
                    "Memory management patterns",
                    "Concurrency and locking",
                    "Error handling practices",
                    "Security vulnerabilities"
                ]
            }
        }
        
        return report
    
    def save_report(self, report: Dict, filename: str = "kernel_analysis_report.json"):
        """Save the analysis report to a JSON file"""
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Analysis report saved to {filename}")
    
    def run_full_analysis(self):
        """Run the complete kernel analysis"""
        print("Starting Linux kernel analysis...")
        
        # Clone kernel if needed
        self.clone_kernel_if_needed()
        
        # Generate report
        report = self.generate_analysis_report()
        
        # Save report
        self.save_report(report)
        
        print("Analysis complete!")
        return report

def main():
    analyzer = KernelAnalyzer()
    report = analyzer.run_full_analysis()
    
    # Print summary
    print("\n" + "="*50)
    print("LINUX KERNEL ANALYSIS SUMMARY")
    print("="*50)
    print(f"Main directories analyzed: {len(report['structure_analysis']['main_directories'])}")
    print(f"Anti-pattern categories identified: {len(report['anti_pattern_categories'])}")
    print(f"C files found: {report['file_patterns']['c_files']}")
    print(f"Header files found: {report['file_patterns']['h_files']}")
    
    print("\nAnti-pattern Categories:")
    for category, info in report['anti_pattern_categories'].items():
        print(f"  - {category}: {info['description']}")

if __name__ == "__main__":
    main() 