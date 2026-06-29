#!/usr/bin/env python3
"""
Historical Data Download Script
===============================

This script downloads all historical congressional trading data
for the years specified in TARGET_YEARS in compare_dates.py

Usage: python download_historical.py
"""

import compare_dates

if __name__ == '__main__':
    print("🚀 STARTING HISTORICAL CONGRESSIONAL DATA DOWNLOAD")
    print("=" * 60)
    print("This will download ZIP files for all years in TARGET_YEARS")
    print("and extract PDFs to stock_purchases/{year}/ folders\n")
    
    # Show which years will be downloaded
    print(f"📅 Years to download: {compare_dates.TARGET_YEARS}")
    
    # Ask for confirmation
    response = input("\nProceed with download? (y/n): ").lower().strip()
    
    if response in ['y', 'yes']:
        print("\n🏛️ Starting download...\n")
        
        # Run the historical download
        successful, failed = compare_dates.download_historical_data()
        
        if successful:
            print(f"\n🎉 DOWNLOAD COMPLETE!")
            print(f"✅ Successfully downloaded {len(successful)} years of data")
            print(f"\n📋 Next steps:")
            print(f"   1. Run: python daily_run.py")
            print(f"   2. Then: jupyter notebook us_congress_strat.ipynb")
            
        else:
            print(f"\n❌ Download failed for all years")
            
    else:
        print("\n❌ Download cancelled by user")
