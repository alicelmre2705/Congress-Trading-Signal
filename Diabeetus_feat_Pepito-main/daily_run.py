import compare_dates
import load_trades
from data_utils import bot_token, my_channel_id
import utils
import os
import sys
import time
import io
import requests
import zipfile
from datetime import datetime

import asyncio
import telegram


def download_and_extract_year_data(year):
    """Download congressional data for a specific year and extract TXT/XML files"""
    print(f"📥 Downloading {year} congressional data...")
    
    # Create year-specific folder in financial_disclosures
    year_folder = os.path.join('financial_disclosures', str(year))
    if not os.path.exists(year_folder):
        os.makedirs(year_folder)
    
    # Download year's ZIP file
    financial_disclosures_url = f"https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.zip"
    
    try:
        response = requests.get(financial_disclosures_url, timeout=30)
        
        if response.status_code == 200:
            # Extract ZIP contents directly to year folder (TXT and XML files)
            z = zipfile.ZipFile(io.BytesIO(response.content))
            z.extractall(year_folder)
            
            # Count extracted files
            extracted_files = os.listdir(year_folder)
            txt_files = [f for f in extracted_files if f.endswith('.txt')]
            xml_files = [f for f in extracted_files if f.endswith('.xml')]
            
            print(f"   ✅ Extracted {len(txt_files)} TXT and {len(xml_files)} XML files to {year_folder}")
            return year_folder, txt_files
        else:
            print(f"   ❌ Failed to download - Status code {response.status_code}")
            return None, []
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Network error - {e}")
        return None, []
    except Exception as e:
        print(f"   ❌ Unexpected error - {e}")
        return None, []


def download_pdfs_from_txt(year_folder, txt_files, year):
    """Read TXT file and download individual PDFs to stock_purchases/{year}/"""
    print(f"📄 Processing TXT files to download PDFs for {year}...")
    
    # Create year-specific folder in stock_purchases
    stock_folder = os.path.join('stock_purchases', str(year))
    if not os.path.exists(stock_folder):
        os.makedirs(stock_folder)
    
    # Get existing PDF files to avoid duplicates
    existing_files = set()
    if os.path.exists(stock_folder):
        existing_files = {f for f in os.listdir(stock_folder) if f.endswith('.pdf')}
    
    successful_downloads = 0
    failed_downloads = 0
    skipped_downloads = 0
    
    # Process each TXT file
    for txt_file in txt_files:
        txt_path = os.path.join(year_folder, txt_file)
        print(f"   📋 Reading {txt_file}...")
        
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            print(f"   📊 Found {len(lines)} disclosure entries")
            
            for line in lines:
                try:
                    # Parse the tab-separated line
                    entry = line.strip().split('\t')
                    if len(entry) >= 9:
                        disclosure_id = entry[8].strip()
                        full_name = entry[1] + entry[2]
                        
                        # Create filename with full name + disclosure ID (like original)
                        full_name = (entry[1] + entry[2]).replace('"', '')  # Remove quotes if any
                        pdf_filename = f"{full_name}_{disclosure_id}.pdf"
                        
                        # Check if PDF already exists
                        if pdf_filename in existing_files:
                            skipped_downloads += 1
                            continue
                        
                        # Download the PDF using existing functions
                        response, document_type = get_response(disclosure_id, year)
                        
                        if response is not None and document_type is not None:
                            # Save PDF to stock_purchases/{year}/
                            pdf_path = os.path.join(stock_folder, pdf_filename)
                            with open(pdf_path, 'wb') as pdf_file:
                                pdf_file.write(response.content)
                            
                            successful_downloads += 1
                            existing_files.add(pdf_filename)  # Update set to avoid re-downloading
                        else:
                            failed_downloads += 1
                            
                except Exception as e:
                    print(f"   ⚠️ Error processing entry: {e}")
                    failed_downloads += 1
                    
        except Exception as e:
            print(f"   ❌ Error reading {txt_file}: {e}")
    
    print(f"   ✅ Downloaded {successful_downloads} new PDFs to {stock_folder}")
    if skipped_downloads > 0:
        print(f"   ⏭️ Skipped {skipped_downloads} existing PDFs")
    if failed_downloads > 0:
        print(f"   ❌ Failed to download {failed_downloads} PDFs")
    
    return successful_downloads


# Import the helper functions from compare_dates
def get_response(disclosure_id, year, max_retries=3, timeout=30):
    """Get response for a disclosure ID (adapted from compare_dates.py)"""
    base_urls = [
        "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/",
        "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/"
    ]
    
    for attempt in range(max_retries):
        for i, base_url in enumerate(base_urls):
            try:
                url = f"{base_url}{year}/{disclosure_id}.pdf"
                response = requests.get(url, timeout=timeout)
                
                if response.status_code == 200:
                    document_type = "ptr" if i == 0 else "financial"
                    return response, document_type
                    
            except requests.exceptions.RequestException:
                continue
        
        if attempt < max_retries - 1:
            time.sleep(1)  # Wait before retry
    
    return None, None


def process_year_data(year):
    """Process PDFs for a specific year and return complete trading data with representative names"""
    print(f"🔄 Processing {year} trading data...")
    
    stock_folder = os.path.join('stock_purchases', str(year))
    
    if not os.path.exists(stock_folder):
        print(f"   ❌ No data folder found for {year}")
        return None
    
    # Get PDFs from year folder
    pdf_files = [f for f in os.listdir(stock_folder) if f.endswith('.pdf')]
    
    if not pdf_files:
        print(f"   ❌ No PDF files found for {year}")
        return None
    
    print(f"   📄 Found {len(pdf_files)} PDF files")
    
    # Use the complete processing logic from load_trades.py that includes representative names
    import glob
    import pandas as pd
    from read_pdf import read_pdf
    from data_utils import formatted_invested_amount_dict
    
    year_path = os.path.join('stock_purchases', str(year), "*pdf")
    year_pdfs = glob.glob(year_path)
    
    if not year_pdfs:
        print(f"   ❌ No PDFs found to process for {year}")
        return None
    
    # Process PDFs with complete data extraction (same logic as get_and_format_all_trades)
    all_trades_df = pd.DataFrame()
    processed_count = 0
    
    for pdf_path in year_pdfs:
        try:
            df = read_pdf(pdf_path)
            if df is not None and not df.empty:
                # Extract representative name from filename (same as load_trades.py)
                representative_name = pdf_path.split(sep='\\')[-1].split(sep='_')[0]
                df.insert(0, 'representative_name', representative_name)
                all_trades_df = pd.concat([all_trades_df, df], ignore_index=True)
                processed_count += 1
        except Exception as e:
            print(f"   ⚠️ Error processing {os.path.basename(pdf_path)}: {e}")
    
    if not all_trades_df.empty:
        print(f"   ✅ Processed {processed_count} PDFs, found {len(all_trades_df)} trading records")
        
        # Format investment amounts into min_amount and max_amount (same as load_trades.py)
        try:
            all_trades_df['formatted_inv_amount'] = all_trades_df['invested_amount'].str.split('-').str[0].str.strip().map(formatted_invested_amount_dict)
            all_trades_df['min_amount'] = all_trades_df['formatted_inv_amount'].str.split('-').str[0].astype(float)
            all_trades_df['max_amount'] = all_trades_df['formatted_inv_amount'].str.split('-').str[1].astype(float)
            
            # Add transaction_year column for analysis
            all_trades_df['purchase_date'] = pd.to_datetime(all_trades_df['purchase_date'], errors='coerce')
            all_trades_df['transaction_year'] = all_trades_df['purchase_date'].dt.year
            
            # Drop intermediate columns
            all_trades_df.drop(['formatted_inv_amount'], inplace=True, axis=1)
            
            print(f"   ✅ Formatted investment amounts and added representative names")
        except Exception as e:
            print(f"   ⚠️ Warning: Could not format investment amounts: {e}")
        
        return all_trades_df
    else:
        print(f"   ❌ No valid trading data found for {year}")
        return None


if __name__ == '__main__':
    # create folder structure for 1st run
    folders_to_create = ['financial_disclosures', 'stock_purchases', 'other_documents']
    for folder in folders_to_create:
        if not os.path.exists(folder):
            os.mkdir(folder)

    print("🏛️ CONGRESSIONAL TRADING DATA PIPELINE")
    print("=" * 50)
    
    # Check for year argument
    target_year = None
    if len(sys.argv) > 1:
        try:
            target_year = int(sys.argv[1])
            if target_year < 2020 or target_year > 2030:
                print("❌ Please provide a valid year (2020-2030)")
                sys.exit(1)
        except ValueError:
            print("❌ Please provide a valid year as argument")
            sys.exit(1)
    else:
        # Interactive year selection
        print("\n📅 SELECT YEAR TO PROCESS:")
        print("Available years: 2022, 2023, 2024, 2025")
        while target_year is None:
            try:
                year_input = input("Enter year to download and process: ").strip()
                target_year = int(year_input)
                if target_year < 2020 or target_year > 2030:
                    print("Please enter a year between 2020-2030")
                    target_year = None
            except ValueError:
                print("Please enter a valid year")
    
    print(f"\n🎯 Processing congressional data for year: {target_year}")
    print("=" * 50)
    
    # Step 1: Download and extract TXT/XML files
    print(f"\n📥 Step 1: Downloading and extracting {target_year} data...")
    year_folder, txt_files = download_and_extract_year_data(target_year)
    
    if not year_folder or not txt_files:
        print(f"❌ Failed to download data or no TXT files found for {target_year}")
        sys.exit(1)
    
    # Step 2: Download PDFs from TXT file entries
    print(f"\n📄 Step 2: Downloading PDFs from TXT file entries...")
    new_files = download_pdfs_from_txt(year_folder, txt_files, target_year)
    
    if new_files == 0:
        print(f"ℹ️ No new PDFs downloaded for {target_year}")
    
    # Step 3: Process year-specific data
    print(f"\n🔄 Step 3: Processing {target_year} trading data...")
    year_trades = process_year_data(target_year)
    
    if year_trades is None or year_trades.empty:
        print(f"❌ No trading data found for {target_year}")
        sys.exit(1)
    
    # Step 4: Add ticker symbols
    print(f"\n🏷️ Step 4: Adding ticker symbols...")
    trades_with_tickers = load_trades.add_tickers(year_trades)
    
    # Step 5: Save year-specific dataset
    print(f"\n💾 Step 5: Saving {target_year} dataset...")
    year_output_path = os.path.join('stock_purchases', f'trades_{target_year}.csv')
    trades_with_tickers.to_csv(year_output_path, index=False)
    
    print(f"✅ Saved {len(trades_with_tickers)} trading records to {year_output_path}")
    
    # Step 6: Create year-specific all_purchases file
    print(f"\n💾 Step 6: Creating year-specific all_purchases file...")
    year_all_purchases_path = os.path.join('stock_purchases', 'all_purchases')
    trades_with_tickers.to_csv(year_all_purchases_path, index=False)
    
    print(f"✅ Created all_purchases file with {len(trades_with_tickers)} records for {target_year}")
    print(f"📁 Year-specific all_purchases: {year_all_purchases_path}")
    
    print(f"\n🎉 PROCESSING COMPLETE FOR {target_year}!")
    print(f"📁 Year-specific CSV: {year_output_path}")
    print(f"📁 Year-specific all_purchases: stock_purchases/all_purchases")
    print(f"\n💡 The all_purchases file now contains only {target_year} data")
    print(f"💡 Use the exploration notebook to analyze this year's data")
    
    # Processing complete - no additional daily updates needed
    # The year-specific processing above already handles all PDF downloads and processing
