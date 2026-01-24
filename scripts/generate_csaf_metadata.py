#!/usr/bin/env python3
"""
Generate index.txt and changes.csv metadata files for CSAF documents.

This script scans a specified directory (advisories or vex) for CSAF JSON files
and generates two metadata files:
- index.txt: List of all CSAF document filenames with their subdirectory paths
- changes.csv: CSV with filename and current_release_date, sorted by date (latest first)
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Tuple


def find_csaf_documents(base_path: Path) -> List[Path]:
    """Find all JSON files in subdirectories of the base path."""
    json_files = []
    
    if not base_path.exists():
        print(f"Error: Directory '{base_path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    # Find all .json files in subdirectories
    for json_file in base_path.rglob("*.json"):
        # Skip files in the root directory, only include files in subdirectories
        if json_file.parent != base_path:
            json_files.append(json_file)
    
    if not json_files:
        print(f"Warning: No CSAF documents found in '{base_path}'", file=sys.stderr)
    
    return sorted(json_files)


def extract_release_date(json_file: Path) -> str:
    """Extract current_release_date from a CSAF document."""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        release_date = data.get('document', {}).get('tracking', {}).get('current_release_date')
        
        if not release_date:
            print(f"Warning: No current_release_date found in {json_file}", file=sys.stderr)
            return ""
        
        return release_date
    
    except json.JSONDecodeError as e:
        print(f"Warning: Invalid JSON in {json_file}: {e}", file=sys.stderr)
        return ""
    except Exception as e:
        print(f"Warning: Error reading {json_file}: {e}", file=sys.stderr)
        return ""


def generate_index_txt(documents: List[Path], base_path: Path, output_file: Path) -> None:
    """Generate index.txt with list of all CSAF document paths."""
    lines = []
    
    for doc in documents:
        # Get relative path from base_path
        relative_path = doc.relative_to(base_path)
        lines.append(str(relative_path))
    
    # Write to file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
        if lines:  # Add trailing newline if file has content
            f.write('\n')
    
    print(f"Generated {output_file} with {len(lines)} entries")


def generate_changes_csv(documents: List[Path], base_path: Path, output_file: Path) -> None:
    """Generate changes.csv with filename and current_release_date, sorted by date."""
    entries: List[Tuple[str, str]] = []
    
    for doc in documents:
        release_date = extract_release_date(doc)
        if release_date:  # Only include documents with valid release dates
            relative_path = doc.relative_to(base_path)
            entries.append((str(relative_path), release_date))
    
    # Sort by release_date descending (latest first)
    entries.sort(key=lambda x: x[1], reverse=True)
    
    # Write to file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for filename, release_date in entries:
            f.write(f'"{filename}","{release_date}"\n')
    
    print(f"Generated {output_file} with {len(entries)} entries")


def main():
    parser = argparse.ArgumentParser(
        description='Generate metadata files for CSAF documents'
    )
    parser.add_argument(
        '--directory',
        required=True,
        choices=['advisories', 'vex'],
        help='Target directory (advisories or vex)'
    )
    
    args = parser.parse_args()
    
    # Determine paths
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    csaf_base = repo_root / 'csaf' / args.directory
    
    print(f"Scanning {csaf_base} for CSAF documents...")
    
    # Find all CSAF documents
    documents = find_csaf_documents(csaf_base)
    
    if not documents:
        print("No documents found. Exiting.")
        sys.exit(0)
    
    print(f"Found {len(documents)} CSAF documents")
    
    # Generate metadata files
    index_file = csaf_base / 'index.txt'
    changes_file = csaf_base / 'changes.csv'
    
    generate_index_txt(documents, csaf_base, index_file)
    generate_changes_csv(documents, csaf_base, changes_file)
    
    print("Metadata generation complete!")


if __name__ == '__main__':
    main()
