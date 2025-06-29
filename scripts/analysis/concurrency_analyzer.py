#!/usr/bin/env python3
"""
Concurrency Issues Analyzer for Linux Kernel
Extracts and classifies concurrency-related anti-patterns
"""

import json
import re
from collections import defaultdict
from pathlib import Path
import os

class ConcurrencyAnalyzer:
    def __init__(self, results_file="results.json"):
        self.results_file = results_file
        self.concurrency_issues = []
        self.classified_issues = defaultdict(list)
        
    def load_results(self):
        """Load analysis results and filter concurrency issues"""
        try:
            with open(self.results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Filter only concurrency issues
            self.concurrency_issues = [
                issue for issue in data['findings'] 
                if issue['rule'] == 'concurrency'
            ]
            
            print(f"📊 Found {len(self.concurrency_issues)} concurrency issues")
            return True
            
        except FileNotFoundError:
            print(f"❌ Error: {self.results_file} not found!")
            return False
        except Exception as e:
            print(f"❌ Error loading results: {e}")
            return False
    
    def classify_concurrency_issues(self):
        """Classify concurrency issues into different types"""
        
        # Define concurrency issue patterns and their classifications
        concurrency_patterns = {
            'race_condition': {
                'patterns': [
                    r'race.*condition',
                    r'race.*between',
                    r'concurrent.*access',
                    r'parallel.*access',
                    r'thread.*safety',
                    r'atomic.*operation',
                    r'data.*race'
                ],
                'description': 'Race conditions between concurrent threads/processes'
            },
            'deadlock': {
                'patterns': [
                    r'deadlock',
                    r'lock.*order',
                    r'circular.*dependency',
                    r'lock.*inversion',
                    r'priority.*inversion'
                ],
                'description': 'Deadlock scenarios and lock ordering issues'
            },
            'missing_lock': {
                'patterns': [
                    r'missing.*lock',
                    r'no.*lock',
                    r'unprotected.*access',
                    r'without.*lock',
                    r'lock.*missing'
                ],
                'description': 'Missing locks for shared resource protection'
            },
            'double_lock': {
                'patterns': [
                    r'double.*lock',
                    r'reentrant.*lock',
                    r'lock.*twice',
                    r'duplicate.*lock'
                ],
                'description': 'Double locking or reentrant lock issues'
            },
            'spinlock_issue': {
                'patterns': [
                    r'spinlock',
                    r'spin.*lock',
                    r'busy.*wait',
                    r'cpu.*spin'
                ],
                'description': 'Spinlock-related issues and CPU spinning'
            },
            'mutex_issue': {
                'patterns': [
                    r'mutex',
                    r'semaphore',
                    r'rwlock',
                    r'read.*write.*lock'
                ],
                'description': 'Mutex, semaphore, and read-write lock issues'
            },
            'memory_barrier': {
                'patterns': [
                    r'memory.*barrier',
                    r'barrier',
                    r'fence',
                    r'ordering.*guarantee'
                ],
                'description': 'Memory ordering and barrier issues'
            },
            'atomic_operation': {
                'patterns': [
                    r'atomic.*',
                    r'cmpxchg',
                    r'xchg',
                    r'atomic.*read',
                    r'atomic.*write'
                ],
                'description': 'Atomic operation issues'
            },
            'irq_lock': {
                'patterns': [
                    r'irq.*lock',
                    r'interrupt.*lock',
                    r'irq.*save',
                    r'irq.*restore'
                ],
                'description': 'Interrupt-related locking issues'
            },
            'rcu_issue': {
                'patterns': [
                    r'rcu',
                    r'read.*copy.*update',
                    r'rcu.*lock',
                    r'rcu.*unlock'
                ],
                'description': 'Read-Copy Update (RCU) related issues'
            }
        }
        
        # Classify each issue
        for issue in self.concurrency_issues:
            issue_text = issue['match'].lower()
            file_path = issue['file']
            
            # Try to match against each pattern
            matched = False
            for category, config in concurrency_patterns.items():
                for pattern in config['patterns']:
                    if re.search(pattern, issue_text, re.IGNORECASE):
                        self.classified_issues[category].append({
                            'file': file_path,
                            'line': issue['line'],
                            'match': issue['match'],
                            'context': issue.get('context', []),
                            'pattern': pattern,
                            'description': config['description']
                        })
                        matched = True
                        break
                if matched:
                    break
            
            # If no specific pattern matched, classify as 'general_concurrency'
            if not matched:
                self.classified_issues['general_concurrency'].append({
                    'file': file_path,
                    'line': issue['line'],
                    'match': issue['match'],
                    'context': issue.get('context', []),
                    'pattern': issue['pattern'],
                    'description': 'General concurrency issues'
                })
    
    def extract_code_snippets(self, kernel_path="linux"):
        """Extract actual code snippets for each issue"""
        kernel_dir = Path(kernel_path)
        
        for category, issues in self.classified_issues.items():
            for issue in issues:
                file_path = kernel_dir / issue['file']
                
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                        
                        line_num = issue['line'] - 1  # Convert to 0-based index
                        
                        # Extract context (5 lines before and after)
                        start = max(0, line_num - 5)
                        end = min(len(lines), line_num + 6)
                        
                        code_snippet = []
                        for i in range(start, end):
                            prefix = ">>> " if i == line_num else "    "
                            code_snippet.append(f"{prefix}{i+1:4d}: {lines[i].rstrip()}")
                        
                        issue['code_snippet'] = code_snippet
                        
                    except Exception as e:
                        issue['code_snippet'] = [f"Error reading file: {e}"]
                else:
                    issue['code_snippet'] = [f"File not found: {file_path}"]
    
    def generate_report(self):
        """Generate a comprehensive concurrency issues report"""
        
        print("=" * 80)
        print("🔒 LINUX KERNEL CONCURRENCY ISSUES ANALYSIS")
        print("=" * 80)
        
        # Summary statistics
        total_issues = len(self.concurrency_issues)
        print(f"📊 Total Concurrency Issues: {total_issues}")
        print()
        
        # Issues by category
        print("📁 CONCURRENCY ISSUES BY CATEGORY:")
        for category, issues in sorted(self.classified_issues.items(), 
                                     key=lambda x: len(x[1]), reverse=True):
            percentage = (len(issues) / total_issues * 100) if total_issues > 0 else 0
            print(f"   • {category.replace('_', ' ').title()}: {len(issues)} ({percentage:.1f}%)")
        print()
        
        # Detailed breakdown
        for category, issues in sorted(self.classified_issues.items(), 
                                     key=lambda x: len(x[1]), reverse=True):
            if not issues:
                continue
                
            print(f"🔍 {category.replace('_', ' ').upper()} ({len(issues)} issues)")
            print(f"   Description: {issues[0]['description']}")
            print()
            
            # Show top files for this category
            file_counts = defaultdict(int)
            for issue in issues:
                file_counts[issue['file']] += 1
            
            print("   Top files with issues:")
            for file_path, count in sorted(file_counts.items(), 
                                         key=lambda x: x[1], reverse=True)[:5]:
                clean_path = file_path.replace('linux/', '')
                print(f"     • {clean_path}: {count} issues")
            print()
            
            # Show sample code snippets
            print("   Sample code snippets:")
            for i, issue in enumerate(issues[:3]):  # Show first 3 examples
                print(f"     Example {i+1}: {issue['file']}:{issue['line']}")
                print(f"     Pattern: {issue['pattern']}")
                print(f"     Match: {issue['match'][:100]}...")
                
                if 'code_snippet' in issue:
                    print("     Code:")
                    for line in issue['code_snippet']:
                        print(f"       {line}")
                print()
            
            if len(issues) > 3:
                print(f"     ... and {len(issues) - 3} more issues")
            print("-" * 60)
    
    def save_detailed_report(self, output_file="concurrency_analysis_report.json"):
        """Save detailed analysis to JSON file"""
        report_data = {
            'summary': {
                'total_concurrency_issues': len(self.concurrency_issues),
                'categories_found': len(self.classified_issues),
                'analysis_date': '2025-06-29'
            },
            'categories': {}
        }
        
        for category, issues in self.classified_issues.items():
            report_data['categories'][category] = {
                'count': len(issues),
                'description': issues[0]['description'] if issues else '',
                'issues': issues
            }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Detailed report saved to {output_file}")
    
    def run_analysis(self):
        """Run the complete concurrency analysis"""
        print("🔒 Starting Concurrency Issues Analysis...")
        
        if not self.load_results():
            return
        
        print("📊 Classifying concurrency issues...")
        self.classify_concurrency_issues()
        
        print("📝 Extracting code snippets...")
        self.extract_code_snippets()
        
        print("📋 Generating report...")
        self.generate_report()
        
        print("💾 Saving detailed report...")
        self.save_detailed_report()
        
        print("✅ Concurrency analysis complete!")

def main():
    analyzer = ConcurrencyAnalyzer()
    analyzer.run_analysis()

if __name__ == "__main__":
    main() 