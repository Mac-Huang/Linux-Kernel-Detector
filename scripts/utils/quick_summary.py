#!/usr/bin/env python3
"""
Quick Summary of Linux Kernel Anti-Pattern Analysis
"""

import json

def main():
    try:
        with open('results.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ results.json not found!")
        return
    
    summary = data['summary']
    stats = data['statistics']
    
    print("=" * 60)
    print("🔍 LINUX KERNEL ANTI-PATTERN ANALYSIS - QUICK SUMMARY")
    print("=" * 60)
    
    print(f"📊 Files analyzed: {summary['total_files_analyzed']:,}")
    print(f"📊 Files with issues: {summary['files_with_issues']:,}")
    print(f"📊 Total issues found: {summary['total_issues_found']:,}")
    print()
    
    print("🚨 CRITICAL ISSUES (Security):")
    print(f"   🔴 {summary['critical_issues']:,} critical security vulnerabilities")
    print()
    
    print("🟡 HIGH PRIORITY ISSUES:")
    print(f"   🟡 {summary['high_priority_issues']:,} high priority issues")
    print("   (Memory leaks, race conditions, deadlocks)")
    print()
    
    print("📁 TOP ISSUE CATEGORIES:")
    for rule, count in sorted(stats['findings_by_rule'].items(), 
                            key=lambda x: x[1], reverse=True)[:5]:
        print(f"   • {rule.replace('_', ' ').title()}: {count:,} issues")
    
    print()
    print("💡 To see detailed results, run:")
    print("   python view_results.py")
    print("   python view_results.py --interactive")

if __name__ == "__main__":
    main() 