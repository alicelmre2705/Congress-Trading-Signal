#!/usr/bin/env python3
"""
Congressional Trading PDFs Downloader
====================================

This script downloads actual congressional trading PDFs (PTR files) for a specific year.
These contain the individual stock trading disclosures, not just summary data.

Usage: python download_trading_pdfs.py [YEAR]
Example: python download_trading_pdfs.py 2024
"""

import sys
import os
import requests
import pandas as pd
from datetime import datetime
import time

def download_trading_pdfs_for_year(target_year):
    """Download actual trading PDFs for a specific year"""
    
    print(f"🏛️ DOWNLOADING TRADING PDFs FOR {target_year}")
    print("=" * 60)
    
    # Create year folder
    year_folder = os.path.join('stock_purchases', str(target_year))
    if not os.path.exists(year_folder):
        os.makedirs(year_folder)
        print(f"📁 Created folder: {year_folder}")
    
    # First, get the summary file to extract disclosure IDs
    summary_url = f"https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{target_year}FD.txt"
    
    print(f"📋 Downloading {target_year} summary file...")
    
    try:
        response = requests.get(summary_url, timeout=30)
        if response.status_code != 200:
            print(f"❌ Failed to download summary file: HTTP {response.status_code}")
            return False
        
        # Parse the summary file to get disclosure IDs
        summary_content = response.text
        lines = summary_content.strip().split('\n')
        
        print(f"📊 Found {len(lines)} disclosure entries")
        
        # Extract disclosure IDs and representative names
        disclosure_data = []
        for line in lines[1:]:  # Skip header
            parts = line.split('\t')
            if len(parts) >= 9:  # Ensure we have enough columns
                disclosure_id = parts[8].strip()
                first_name = parts[0].strip()
                last_name = parts[1].strip()
                full_name = f"{last_name}{first_name}"
                disclosure_data.append((disclosure_id, full_name))
        
        print(f"🎯 Attempting to download {len(disclosure_data)} individual PDFs...")
        
        successful_downloads = 0
        failed_downloads = 0
        
        for i, (disclosure_id, full_name) in enumerate(disclosure_data):
            if i % 10 == 0:
                print(f"   ⏳ Progress: {i}/{len(disclosure_data)} PDFs...")
            
            # Try to download the PDF
            success = download_individual_pdf(disclosure_id, full_name, target_year, year_folder)
            if success:
                successful_downloads += 1
            else:
                failed_downloads += 1
            
            # Small delay to be respectful to the server
            time.sleep(0.5)
        
        print(f"\n📊 DOWNLOAD SUMMARY:")
        print(f"   ✅ Successful: {successful_downloads} PDFs")
        print(f"   ❌ Failed: {failed_downloads} PDFs")
        print(f"   📁 Saved to: {year_folder}")
        
        if successful_downloads > 0:
            print(f"\n🚀 Ready to process {target_year} data!")
            print(f"   Next: python process_year.py {target_year}")
            return True
        else:
            print(f"\n❌ No PDFs downloaded successfully")
            return False
            
    except Exception as e:
        print(f"❌ Error downloading summary file: {e}")
        return False

def download_individual_pdf(disclosure_id, full_name, year, year_folder):
    """Download an individual congressional trading PDF"""
    
    # Try both PTR and financial disclosure URLs
    urls_to_try = [
        f'https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{year}/{disclosure_id}.pdf',
        f'https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}/{disclosure_id}.pdf'
    ]
    
    for url in urls_to_try:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                # Save the PDF
                filename = f"{full_name}_{disclosure_id}.pdf"
                filepath = os.path.join(year_folder, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                return True
                
        except Exception:
            continue
    
    return False

def main():
    """Main function to handle command line arguments"""
    
    if len(sys.argv) != 2:
        print("📋 USAGE:")
        print("   python download_trading_pdfs.py [YEAR]")
        print("\n📅 EXAMPLES:")
        print("   python download_trading_pdfs.py 2024")
        print("   python download_trading_pdfs.py 2023")
        print("\n🎯 This will download actual trading PDFs for the specified year")
        return
    
    target_year = sys.argv[1]
    
    # Validate year
    try:
        year_int = int(target_year)
        if year_int < 2020 or year_int > datetime.now().year + 1:
            print(f"❌ Invalid year: {target_year}")
            return
    except ValueError:
        print(f"❌ Invalid year format: {target_year}")
        return
    
    # Download PDFs for the year
    success = download_trading_pdfs_for_year(target_year)
    
    if success:
        print(f"\n✅ Download complete for {target_year}!")
        print(f"📋 Next steps:")
        print(f"   1. python process_year.py {target_year}")
        print(f"   2. Use the generated trades_{target_year}.csv for analysis")
    else:
        print(f"\n❌ Download failed for {target_year}")

if __name__ == '__main__':
    main()
