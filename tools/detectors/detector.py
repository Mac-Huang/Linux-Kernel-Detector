#!/usr/bin/env python3
"""
Linux Kernel Anti-Pattern Detector
Main script for detecting anti-patterns in Linux kernel code
"""

import os
import sys
import json
import yaml
import click
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Tuple
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import colorama
from colorama import Fore, Style

# Initialize colorama for cross-platform colored output
colorama.init()

class AntiPatternDetector:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self.load_config(config_path)
        self.setup_logging()
        self.results = {
            "summary": {},
            "findings": [],
            "statistics": {}
        }
        
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"{Fore.RED}Error: Configuration file {config_path} not found{Style.RESET_ALL}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"{Fore.RED}Error: Invalid YAML in {config_path}: {e}{Style.RESET_ALL}")
            sys.exit(1)
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_config.get('file', 'detector.log')),
                logging.StreamHandler() if log_config.get('console_output', True) else logging.NullHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_c_files(self, kernel_path: str) -> List[Path]:
        """Get all C files from the kernel directory"""
        kernel_dir = Path(kernel_path)
        c_files = []
        
        exclude_patterns = self.config['analysis']['exclude_patterns']
        max_file_size = self.config['analysis']['max_file_size']
        
        for file_path in kernel_dir.rglob("*.c"):
            # Skip excluded files
            if any(file_path.match(pattern) for pattern in exclude_patterns):
                continue
                
            # Skip large files
            if file_path.stat().st_size > max_file_size:
                self.logger.debug(f"Skipping large file: {file_path}")
                continue
                
            c_files.append(file_path)
        
        return c_files
    
    def analyze_file(self, file_path: Path) -> List[Dict]:
        """Analyze a single C file for anti-patterns"""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            self.logger.warning(f"Could not read {file_path}: {e}")
            return findings
        
        # Get enabled detection rules
        detection_rules = self.config['detection_rules']
        
        for rule_name, rule_config in detection_rules.items():
            if not rule_config.get('enabled', True):
                continue
                
            # Check if file is in the target directories
            file_dir = str(file_path.parent.relative_to(Path(self.config['analysis']['kernel_repository'].split('/')[-1].replace('.git', ''))))
            if not any(target_dir in file_dir for target_dir in rule_config.get('directories', [])):
                continue
            
            # Check each pattern
            for pattern in rule_config.get('patterns', []):
                try:
                    matches = list(re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE))
                    
                    for match in matches:
                        # Get line number
                        line_num = content[:match.start()].count('\n') + 1
                        
                        # Get context lines
                        context_lines = self.get_context_lines(lines, line_num - 1)
                        
                        finding = {
                            "file": str(file_path),
                            "line": line_num,
                            "pattern": pattern,
                            "rule": rule_name,
                            "severity": rule_config.get('severity', 'medium'),
                            "match": match.group(0),
                            "context": context_lines
                        }
                        findings.append(finding)
                        
                except re.error as e:
                    self.logger.warning(f"Invalid regex pattern '{pattern}': {e}")
        
        return findings
    
    def get_context_lines(self, lines: List[str], line_num: int, context: int = 3) -> List[str]:
        """Get context lines around the matched line"""
        start = max(0, line_num - context)
        end = min(len(lines), line_num + context + 1)
        return lines[start:end]
    
    def analyze_kernel(self, kernel_path: str = "linux") -> Dict:
        """Analyze the entire kernel for anti-patterns"""
        self.logger.info(f"Starting kernel analysis of {kernel_path}")
        
        # Get all C files
        c_files = self.get_c_files(kernel_path)
        self.logger.info(f"Found {len(c_files)} C files to analyze")
        
        # Analyze files in parallel
        all_findings = []
        statistics = {
            "total_files": len(c_files),
            "analyzed_files": 0,
            "files_with_findings": 0,
            "total_findings": 0,
            "findings_by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "findings_by_rule": {}
        }
        
        max_workers = self.config['performance']['max_concurrent_analyzers']
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all files for analysis
            future_to_file = {executor.submit(self.analyze_file, file_path): file_path 
                            for file_path in c_files}
            
            # Process results with progress bar
            with tqdm(total=len(c_files), desc="Analyzing files") as pbar:
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        findings = future.result()
                        all_findings.extend(findings)
                        
                        statistics["analyzed_files"] += 1
                        if findings:
                            statistics["files_with_findings"] += 1
                            statistics["total_findings"] += len(findings)
                            
                            # Count by severity
                            for finding in findings:
                                severity = finding["severity"]
                                statistics["findings_by_severity"][severity] += 1
                                
                                # Count by rule
                                rule = finding["rule"]
                                statistics["findings_by_rule"][rule] = statistics["findings_by_rule"].get(rule, 0) + 1
                        
                    except Exception as e:
                        self.logger.error(f"Error analyzing {file_path}: {e}")
                    
                    pbar.update(1)
        
        # Compile results
        self.results["findings"] = all_findings
        self.results["statistics"] = statistics
        
        # Generate summary
        self.results["summary"] = {
            "total_files_analyzed": statistics["analyzed_files"],
            "files_with_issues": statistics["files_with_findings"],
            "total_issues_found": statistics["total_findings"],
            "critical_issues": statistics["findings_by_severity"]["critical"],
            "high_priority_issues": statistics["findings_by_severity"]["high"],
            "medium_priority_issues": statistics["findings_by_severity"]["medium"],
            "low_priority_issues": statistics["findings_by_severity"]["low"]
        }
        
        return self.results
    
    def print_summary(self):
        """Print analysis summary to console"""
        summary = self.results["summary"]
        
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"LINUX KERNEL ANTI-PATTERN ANALYSIS SUMMARY")
        print(f"{'='*60}{Style.RESET_ALL}")
        
        print(f"Files analyzed: {summary['total_files_analyzed']}")
        print(f"Files with issues: {summary['files_with_issues']}")
        print(f"Total issues found: {summary['total_issues_found']}")
        
        print(f"\n{Fore.RED}Critical issues: {summary['critical_issues']}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}High priority issues: {summary['high_priority_issues']}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}Medium priority issues: {summary['medium_priority_issues']}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Low priority issues: {summary['low_priority_issues']}{Style.RESET_ALL}")
        
        # Print findings by rule
        if self.results["statistics"]["findings_by_rule"]:
            print(f"\n{Fore.CYAN}Issues by category:{Style.RESET_ALL}")
            for rule, count in sorted(self.results["statistics"]["findings_by_rule"].items(), 
                                    key=lambda x: x[1], reverse=True):
                print(f"  {rule}: {count}")
    
    def save_results(self, output_file: str = "anti_pattern_results.json"):
        """Save analysis results to file"""
        output_config = self.config.get('output', {})
        
        if output_config.get('report_format', 'json') == 'json':
            with open(output_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            self.logger.info(f"Results saved to {output_file}")
        else:
            # TODO: Implement other output formats (HTML, text)
            self.logger.warning("Only JSON output format is currently supported")

@click.command()
@click.option('--kernel-path', default='linux', help='Path to Linux kernel source')
@click.option('--config', default='config.yaml', help='Configuration file path')
@click.option('--output', default='anti_pattern_results.json', help='Output file path')
@click.option('--clone', is_flag=True, help='Clone kernel repository if not present')
def main(kernel_path: str, config: str, output: str, clone: bool):
    """Linux Kernel Anti-Pattern Detector"""
    
    # Initialize detector
    detector = AntiPatternDetector(config)
    
    # Clone kernel if requested
    if clone and not os.path.exists(kernel_path):
        print(f"Cloning Linux kernel to {kernel_path}...")
        try:
            subprocess.run([
                "git", "clone", "--depth", "1", 
                "https://github.com/torvalds/linux.git", 
                kernel_path
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"{Fore.RED}Error cloning kernel: {e}{Style.RESET_ALL}")
            sys.exit(1)
    
    # Run analysis
    results = detector.analyze_kernel(kernel_path)
    
    # Print summary
    detector.print_summary()
    
    # Save results
    detector.save_results(output)
    
    print(f"\n{Fore.GREEN}Analysis complete! Results saved to {output}{Style.RESET_ALL}")

if __name__ == "__main__":
    main() 