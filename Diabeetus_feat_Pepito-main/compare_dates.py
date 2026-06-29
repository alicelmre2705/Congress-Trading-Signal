from datetime import datetime, timedelta

import io
import os
import requests
import zipfile

# MULTI-YEAR DATA DOWNLOAD CONFIGURATION
# Years to download for comprehensive backtesting (oldest to newest)
TARGET_YEARS = [2022, 2023, 2024, 2025]  # Add/remove years as needed
CURRENT_YEAR = 2024  # Current year for daily operations


def download_today_public_data():
    """Download current year's data for daily operations"""
    financial_disclosures_report_url = f"https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{CURRENT_YEAR}FD.zip"
    response = requests.get(financial_disclosures_report_url)

    if response.status_code == 200:
        # Extraction of today's zip file
        z = zipfile.ZipFile(io.BytesIO(response.content))
        today = datetime.today()
        today_folder_name = "disclosures_" + today.strftime("%m_%d_%Y")
        path_to_folder = os.path.join('financial_disclosures', today_folder_name)
        z.extractall(path_to_folder)
        print(f"✅ Downloaded {CURRENT_YEAR} data to {path_to_folder}")
    else:
        print(f'❌ Failed to download {CURRENT_YEAR} data - Status code: {response.status_code}')


def download_historical_data():
    """Download all years of historical congressional data for comprehensive backtesting"""
    print("🏛️ DOWNLOADING MULTI-YEAR CONGRESSIONAL DATA")
    print("=" * 50)
    
    successful_downloads = []
    failed_downloads = []
    
    # Ensure stock_purchases directory exists
    if not os.path.exists('stock_purchases'):
        os.makedirs('stock_purchases')
    
    for year in TARGET_YEARS:
        print(f"\n📅 Downloading {year} congressional data...")
        
        # Create year-specific folder in stock_purchases
        year_folder_name = str(year)
        path_to_folder = os.path.join('stock_purchases', year_folder_name)
        
        if not os.path.exists(path_to_folder):
            os.makedirs(path_to_folder)
        
        # Download year's data
        financial_disclosures_url = f"https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.zip"
        
        try:
            response = requests.get(financial_disclosures_url, timeout=30)
            
            if response.status_code == 200:
                # Extract zip file directly to stock_purchases/{year}/
                z = zipfile.ZipFile(io.BytesIO(response.content))
                z.extractall(path_to_folder)
                
                # Count extracted files
                extracted_files = len([f for f in os.listdir(path_to_folder) if f.endswith('.pdf')])
                
                print(f"   ✅ {year}: Downloaded {extracted_files} PDF files to {path_to_folder}")
                successful_downloads.append((year, extracted_files))
                
            else:
                print(f"   ❌ {year}: Failed - Status code {response.status_code}")
                failed_downloads.append(year)
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ {year}: Network error - {e}")
            failed_downloads.append(year)
        except Exception as e:
            print(f"   ❌ {year}: Unexpected error - {e}")
            failed_downloads.append(year)
    
    # Summary
    print(f"\n📊 DOWNLOAD SUMMARY:")
    print(f"   ✅ Successful: {len(successful_downloads)} years")
    for year, count in successful_downloads:
        print(f"      • {year}: {count} PDF files → stock_purchases/{year}/")
    
    if failed_downloads:
        print(f"   ❌ Failed: {len(failed_downloads)} years - {failed_downloads}")
    
    total_files = sum(count for _, count in successful_downloads)
    print(f"\n🎯 TOTAL: {total_files} congressional disclosure PDFs downloaded")
    print(f"📁 All PDFs organized by year in stock_purchases/ folders")
    print(f"📈 Ready for comprehensive multi-year backtesting!")
    
    return successful_downloads, failed_downloads


def compare_today_yesterday():
    today = datetime.today()
    today_folder_name = "disclosures_" + today.strftime("%m_%d_%Y")
    file_name = f'{CURRENT_YEAR}FD.txt'  # Uses current year
    path_today_txt_file = os.path.join("financial_disclosures", today_folder_name, file_name)
    download_today_public_data()

    # Reading today and yesterday's txt files
    yesterday = today - timedelta(1)
    yesterday_folder_name = "disclosures_" + yesterday.strftime("%m_%d_%Y")
    path_yesterday_txt_file = os.path.join("financial_disclosures", yesterday_folder_name, file_name)

    # Comparing the contents and extracting the difference
    if not os.path.exists(path_yesterday_txt_file):
        with open(path_today_txt_file) as today_txt_file:
            differences = set(today_txt_file.readlines())
    else:
        with open(path_today_txt_file) as today_txt_file, open(path_yesterday_txt_file) as yesterday_txt_file:
            differences = set(today_txt_file.readlines()) - set(yesterday_txt_file.readlines())

    # Comparing today and yesterday
    if differences != set():
        new_entries_list = [diff.split("\t") for diff in differences]
        messages_list = [
            "New entry from {0} {1} {2} on {3}, disclosure_id: {4}".format(entry[0], entry[1], entry[2], entry[7],
                                                                           entry[8][:-1])
            for entry in new_entries_list]
        return messages_list, new_entries_list
    else:
        return ['No new congressional shenanigans'], list()


def get_response(disclosure_id, max_retries=3, timeout=30):
    """
    There are two different base URLs on the disclosures-clerk website corresponding
    to two types of files:
    https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2025/ => for new stock purchases
    https://disclosures-clerk.house.gov/public_disc/financial-pdfs/2025/ => for other documents
    """
    import time
    
    urls_to_try = [
        (f'https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{CURRENT_YEAR}/' + disclosure_id + '.pdf', 'stock_purchases'),
        (f'https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{CURRENT_YEAR}/' + disclosure_id + '.pdf', 'other_documents')
    ]
    
    for disclosure_url, document_type in urls_to_try:
        for attempt in range(max_retries):
            try:
                print(f"   📥 Downloading {disclosure_id} (attempt {attempt + 1}/{max_retries})...")
                response = requests.get(disclosure_url, timeout=timeout)
                
                if response.status_code == 200:
                    print(f"   ✅ Success: {disclosure_id}")
                    return response, document_type
                elif response.status_code == 404:
                    print(f"   ⚠️ Not found at {document_type}, trying next URL...")
                    break  # Try next URL
                else:
                    print(f"   ⚠️ HTTP {response.status_code}, retrying...")
                    
            except requests.exceptions.Timeout:
                print(f"   ⏱️ Timeout on attempt {attempt + 1}, retrying...")
                if attempt < max_retries - 1:
                    time.sleep(2)  # Wait 2 seconds before retry
            except requests.exceptions.ConnectionError:
                print(f"   🌐 Connection error on attempt {attempt + 1}, retrying...")
                if attempt < max_retries - 1:
                    time.sleep(5)  # Wait 5 seconds before retry
            except Exception as e:
                print(f"   ❌ Unexpected error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
    
    print(f"   ❌ Failed to download {disclosure_id} after all attempts")
    return None, None


def get_disclosure(response, document_type, full_name, disclosure_id):
    path_to_folder = os.path.join(document_type, datetime.today().strftime('%m_%d_%Y'))
    path_to_file = os.path.join(path_to_folder, full_name.replace('"', '') + '_' + disclosure_id + '.pdf')

    if not os.path.exists(path_to_folder):
        os.mkdir(path_to_folder)

    with open(path_to_file, 'wb') as disclosure:
        disclosure.write(response.content)
    print("File was written to: ", path_to_file)


def run():
    """Standard daily run - downloads current year data and compares"""
    download_today_public_data()
    messages_list, new_entries_list = compare_today_yesterday()
    
    successful_downloads = 0
    failed_downloads = 0
    
    for entry in new_entries_list:
        disclosure_id = entry[8][:-1]
        response, document_type = get_response(disclosure_id)
        
        if response is not None and document_type is not None:
            full_name = entry[1] + entry[2]
            get_disclosure(response, document_type, full_name, disclosure_id)
            successful_downloads += 1
        else:
            failed_downloads += 1
            print(f"⚠️ Skipping {disclosure_id} due to download failure")

    print(f"\n📊 DOWNLOAD SUMMARY:")
    print(f"   ✅ Successful: {successful_downloads} files")
    print(f"   ❌ Failed: {failed_downloads} files")
    
    for message in messages_list:
        print(message)

    return messages_list


def run_historical():
    """Download all historical data for comprehensive backtesting"""
    print("🚀 STARTING COMPREHENSIVE HISTORICAL DATA DOWNLOAD")
    print("This will download multiple years of congressional data...\n")
    
    # Download all historical years
    successful, failed = download_historical_data()
    
    if successful:
        print("\n🔄 Now processing all downloaded PDFs into trades...")
        # The load_trades.py will automatically process all PDFs in stock_purchases/
        print("   Run: python daily_run.py (to process all PDFs into CSV)")
        print("   Then: jupyter notebook us_congress_strat.ipynb (for backtesting)")
    else:
        print("\n❌ No data downloaded successfully. Check your internet connection.")
