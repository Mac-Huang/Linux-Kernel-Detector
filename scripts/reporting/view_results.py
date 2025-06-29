#!/usr/bin/env python3
"""
Enhanced Results Viewer for Linux Kernel Anti-Pattern Analysis
"""

import json
import sys
import os
from pathlib import Path
from collections import defaultdict

def load_results(filename):
    """Load results from JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: {filename} not found!")
        print("Make sure you've run the analysis first with:")
        print("  python kernel-analysis/detector.py --clone --output results.json")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {filename}: {e}")
        return None
    except Exception as e:
        print(f"❌ Error loading {filename}: {e}")
        return None

def print_summary(data):
    """Print analysis summary with better formatting"""
    summary = data['summary']
    stats = data['statistics']
    
    print("=" * 80)
    print("🔍 LINUX KERNEL ANTI-PATTERN ANALYSIS RESULTS")
    print("=" * 80)
    
    # Overall statistics
    print(f"📊 OVERALL STATISTICS:")
    print(f"   Files analyzed: {summary['total_files_analyzed']:,}")
    print(f"   Files with issues: {summary['files_with_issues']:,}")
    print(f"   Total issues found: {summary['total_issues_found']:,}")
    print(f"   Issue rate: {(summary['files_with_issues']/summary['total_files_analyzed']*100):.1f}%")
    print()
    
    # Issues by severity
    print("🚨 ISSUES BY SEVERITY:")
    severity_icons = {
        'critical': '🔴',
        'high': '🟡', 
        'medium': '🔵',
        'low': '🟢'
    }
    
    for severity in ['critical', 'high', 'medium', 'low']:
        count = summary.get(f'{severity}_issues', 0)
        icon = severity_icons.get(severity, '⚪')
        percentage = (count / summary['total_issues_found'] * 100) if summary['total_issues_found'] > 0 else 0
        print(f"   {icon} {severity.title()}: {count:,} ({percentage:.1f}%)")
    print()
    
    # Issues by category
    print("📁 ISSUES BY CATEGORY:")
    for rule, count in sorted(stats['findings_by_rule'].items(), 
                            key=lambda x: x[1], reverse=True):
        percentage = (count / summary['total_issues_found'] * 100) if summary['total_issues_found'] > 0 else 0
        print(f"   • {rule.replace('_', ' ').title()}: {count:,} ({percentage:.1f}%)")

def print_detailed_findings(data, max_samples=3):
    """Print detailed findings with better organization"""
    findings = data['findings']
    
    print("\n" + "=" * 80)
    print("🔍 DETAILED FINDINGS BY CATEGORY")
    print("=" * 80)
    
    # Group by rule and severity
    by_rule = defaultdict(lambda: defaultdict(list))
    for finding in findings:
        by_rule[finding['rule']][finding['severity']].append(finding)
    
    # Category descriptions
    descriptions = {
        'memory_management': 'Memory leaks, use-after-free, double-free issues',
        'concurrency': 'Race conditions, deadlocks, improper locking',
        'error_handling': 'Unchecked return values, missing error handling',
        'security': 'Buffer overflows, format string vulnerabilities',
        'performance': 'Inefficient algorithms, unnecessary allocations',
        'code_quality': 'Magic numbers, complex functions, code duplication',
        'api_usage': 'Deprecated functions, incorrect API usage'
    }
    
    for rule, severities in by_rule.items():
        total_issues = sum(len(issues) for issues in severities.values())
        print(f"\n📁 {rule.replace('_', ' ').upper()} ({total_issues} issues)")
        print(f"   Description: {descriptions.get(rule, 'Various issues')}")
        
        # Show by severity within each category
        for severity in ['critical', 'high', 'medium', 'low']:
            if severity in severities:
                issues = severities[severity]
                icon = {'critical': '🔴', 'high': '🟡', 'medium': '🔵', 'low': '🟢'}[severity]
                print(f"\n   {icon} {severity.title()} Priority ({len(issues)} issues):")
                
                for i, finding in enumerate(issues[:max_samples]):
                    file_path = finding['file'].replace('linux/', '')
                    print(f"     {i+1}. {file_path}:{finding['line']}")
                    print(f"        Pattern: {finding['pattern']}")
                    print(f"        Match: {finding['match'][:80]}...")
                
                if len(issues) > max_samples:
                    print(f"        ... and {len(issues) - max_samples} more {severity} issues")

def print_top_files(data, top_n=10):
    """Print files with the most issues"""
    findings = data['findings']
    
    # Count issues per file
    file_counts = defaultdict(int)
    for finding in findings:
        file_counts[finding['file']] += 1
    
    print("\n" + "=" * 80)
    print(f"📋 TOP {top_n} FILES WITH MOST ISSUES")
    print("=" * 80)
    
    for i, (file_path, count) in enumerate(sorted(file_counts.items(), 
                                                 key=lambda x: x[1], reverse=True)[:top_n]):
        clean_path = file_path.replace('linux/', '')
        print(f"   {i+1:2d}. {clean_path}: {count} issues")

def print_severity_breakdown(data):
    """Print detailed breakdown by severity"""
    findings = data['findings']
    
    print("\n" + "=" * 80)
    print("📊 DETAILED SEVERITY BREAKDOWN")
    print("=" * 80)
    
    for severity in ['critical', 'high', 'medium', 'low']:
        severity_findings = [f for f in findings if f['severity'] == severity]
        if not severity_findings:
            continue
            
        icon = {'critical': '🔴', 'high': '🟡', 'medium': '🔵', 'low': '🟢'}[severity]
        print(f"\n{icon} {severity.upper()} ISSUES ({len(severity_findings)} total):")
        
        # Group by rule
        by_rule = defaultdict(list)
        for finding in severity_findings:
            by_rule[finding['rule']].append(finding)
        
        for rule, issues in sorted(by_rule.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"   • {rule.replace('_', ' ').title()}: {len(issues)} issues")

def interactive_viewer(data):
    """Enhanced interactive viewer"""
    findings = data['findings']
    
    while True:
        print("\n" + "=" * 50)
        print("🎮 INTERACTIVE RESULTS VIEWER")
        print("=" * 50)
        print("1. 📊 View summary")
        print("2. 🚨 Browse by severity")
        print("3. 📁 Browse by category")
        print("4. 🔍 Search by filename")
        print("5. 📋 Top problematic files")
        print("6. 📈 Severity breakdown")
        print("7. 💾 Export filtered results")
        print("8. ❌ Exit")
        
        try:
            choice = input("\nEnter your choice (1-8): ").strip()
            
            if choice == '1':
                print_summary(data)
            elif choice == '2':
                severity = input("Enter severity (critical/high/medium/low): ").strip().lower()
                if severity in ['critical', 'high', 'medium', 'low']:
                    filtered = [f for f in findings if f['severity'] == severity]
                    print(f"\n🔍 Found {len(filtered)} {severity} issues:")
                    for i, finding in enumerate(filtered[:15]):
                        file_path = finding['file'].replace('linux/', '')
                        print(f"  {i+1:2d}. {file_path}:{finding['line']} - {finding['rule']}")
                else:
                    print("❌ Invalid severity level")
            elif choice == '3':
                rule = input("Enter category: ").strip().lower()
                filtered = [f for f in findings if f['rule'] == rule]
                if filtered:
                    print(f"\n🔍 Found {len(filtered)} issues in {rule}:")
                    for i, finding in enumerate(filtered[:15]):
                        file_path = finding['file'].replace('linux/', '')
                        print(f"  {i+1:2d}. {file_path}:{finding['line']} - {finding['severity']}")
                else:
                    print(f"❌ No issues found for category '{rule}'")
            elif choice == '4':
                filename = input("Enter filename pattern: ").strip()
                filtered = [f for f in findings if filename.lower() in f['file'].lower()]
                print(f"\n🔍 Found {len(filtered)} issues in files matching '{filename}':")
                for i, finding in enumerate(filtered[:15]):
                    file_path = finding['file'].replace('linux/', '')
                    print(f"  {i+1:2d}. {file_path}:{finding['line']} - {finding['rule']} ({finding['severity']})")
            elif choice == '5':
                print_top_files(data)
            elif choice == '6':
                print_severity_breakdown(data)
            elif choice == '7':
                export_filtered_results(data)
            elif choice == '8':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please try again.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def export_filtered_results(data):
    """Export filtered results to a new JSON file"""
    print("\n📤 EXPORT FILTERED RESULTS")
    print("Filter options:")
    print("1. By severity")
    print("2. By category")
    print("3. By filename pattern")
    
    try:
        filter_choice = input("Choose filter type (1-3): ").strip()
        
        if filter_choice == '1':
            severity = input("Enter severity (critical/high/medium/low): ").strip().lower()
            filtered = [f for f in data['findings'] if f['severity'] == severity]
            filename = f"results_{severity}_only.json"
        elif filter_choice == '2':
            rule = input("Enter category: ").strip().lower()
            filtered = [f for f in data['findings'] if f['rule'] == rule]
            filename = f"results_{rule}_only.json"
        elif filter_choice == '3':
            pattern = input("Enter filename pattern: ").strip()
            filtered = [f for f in data['findings'] if pattern.lower() in f['file'].lower()]
            filename = f"results_filtered_{pattern.replace('*', 'all').replace('/', '_')}.json"
        else:
            print("❌ Invalid choice")
            return
        
        if filtered:
            export_data = {
                'summary': {
                    'total_issues_found': len(filtered),
                    'filter_applied': filter_choice
                },
                'findings': filtered
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            print(f"✅ Exported {len(filtered)} issues to {filename}")
        else:
            print("❌ No issues match the filter criteria")
            
    except Exception as e:
        print(f"❌ Export failed: {e}")

def main():
    # Determine filename
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "results.json"
    
    # Load data
    data = load_results(filename)
    if not data:
        return
    
    # Check if interactive mode is requested
    if len(sys.argv) > 2 and sys.argv[2] == "--interactive":
        interactive_viewer(data)
    else:
        # Show comprehensive report
        print_summary(data)
        print_detailed_findings(data)
        print_top_files(data)
        print_severity_breakdown(data)
        
        print("\n" + "=" * 80)
        print("💡 TIP: Run with --interactive for interactive browsing:")
        print("   python view_results.py --interactive")
        print("=" * 80)

if __name__ == "__main__":
    main() 