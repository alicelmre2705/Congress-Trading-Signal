import glob
import os
import pandas as pd
from read_pdf import read_pdf
from data_utils import formatted_invested_amount_dict


def get_specific_trades(business_date):
    """Get trades for a specific date - works with both date folders and year folders"""
    path_to_folder = os.path.join('stock_purchases', business_date, "*pdf")
    daily_trades = glob.glob(path_to_folder)
    
    # If no PDFs found in date folder, check if it's in a year folder
    if not daily_trades:
        # Extract year from business_date (assuming format MM_DD_YYYY)
        try:
            year = business_date.split('_')[-1]
            year_path = os.path.join('stock_purchases', year, "*pdf")
            daily_trades = glob.glob(year_path)
            print(f"📅 Looking for {business_date} trades in year folder {year}/")
        except:
            print(f"⚠️ Could not find trades for {business_date}")
    
    # daily_trades.remove('stock_purchases\\05_23_2025\\WhitesidesGeorge_20027982.pdf')
    # daily_trades.remove('stock_purchases\\05_23_2025\\DoggettLloyd_20030285.pdf')

    all_stocks_df = pd.DataFrame()
    for path in daily_trades:
        df = read_pdf(path)
        representative_name = path.split(sep='\\')[-1].split(sep='_')[0]
        df.insert(0, 'representative_name', representative_name)
        all_stocks_df = pd.concat([all_stocks_df, df])

    if all_stocks_df.empty:
        print('Document probably filled manually, to check')
        return pd.DataFrame()

    all_stocks_df['formatted_inv_amount'] = all_stocks_df['invested_amount'].str.split('-').str[0].str.strip().map(formatted_invested_amount_dict)
    all_stocks_df['min_amount'] = all_stocks_df['formatted_inv_amount'].str.split('-').str[0].astype(float)
    all_stocks_df['max_amount'] = all_stocks_df['formatted_inv_amount'].str.split('-').str[1].astype(float)
    all_stocks_df.drop(['invested_amount', 'formatted_inv_amount'], inplace=True, axis=1)

    return all_stocks_df.reset_index(drop=True)

def get_and_format_all_trades():
    doc_paths = []
    
    # Check if stock_purchases directory exists
    if not os.path.exists('stock_purchases'):
        print("⚠️ stock_purchases directory not found. Run historical download first.")
        return pd.DataFrame()
    
    stock_purchases = os.listdir('stock_purchases')
    
    # Process all subdirectories (including year folders like '2022', '2023', etc.)
    for entry in stock_purchases:
        entry_path = os.path.join('stock_purchases', entry)
        
        # Skip the all_purchases file
        if entry == 'all_purchases':
            continue
            
        # If it's a directory, look for PDFs inside
        if os.path.isdir(entry_path):
            path = os.path.join('stock_purchases', entry, "*pdf")
            doc_paths += glob.glob(path)
            print(f"📁 Found {len(glob.glob(path))} PDFs in {entry}/")

    # For the time being, removing whitesides and doggett as their files are poorly formatted
    files_to_remove = ['WhitesidesGeorge_20027982.pdf', 'DoggettLloyd_20030285.pdf']
    for file in files_to_remove:
        path = os.path.join('stock_purchases', '05_23_2025', file)
        if os.path.exists(path):
            doc_paths.remove(path)

    print(f"\n📊 PROCESSING {len(doc_paths)} TOTAL PDFs FROM ALL YEARS...")
    
    all_trades_df = pd.DataFrame()
    processed_count = 0
    
    for path in doc_paths:
        try:
            df = read_pdf(path)
            representative_name = path.split(sep='\\')[-1].split(sep='_')[0]
            df.insert(0, 'representative_name', representative_name)
            all_trades_df = pd.concat([all_trades_df, df])
            processed_count += 1
            
            if processed_count % 50 == 0:  # Progress indicator
                print(f"   ⏳ Processed {processed_count}/{len(doc_paths)} PDFs...")
                
        except Exception as e:
            print(f"   ⚠️ Error processing {path}: {e}")
            continue

    if not all_trades_df.empty:
        print(f"\n✅ Successfully processed {processed_count} PDFs")
        print(f"📈 Extracted {len(all_trades_df)} total trading records")
        
        all_trades_df['formatted_inv_amount'] = all_trades_df['invested_amount'].str.split('-').str[0].str.strip().map(formatted_invested_amount_dict)
        all_trades_df['min_amount'] = all_trades_df['formatted_inv_amount'].str.split('-').str[0].astype(float)
        all_trades_df['max_amount'] = all_trades_df['formatted_inv_amount'].str.split('-').str[1].astype(float)
        all_trades_df.drop(['invested_amount', 'formatted_inv_amount'], inplace=True, axis=1)
    else:
        print("❌ No trading data extracted from PDFs")

    return all_trades_df.reset_index(drop=True)

def add_tickers(trades_df):
    trades_copy = trades_df.copy()
    trades_with_tickers = pd.DataFrame()

    if not trades_copy.empty:
        path_to_csv = os.path.join('mappings', 'all_stocks.csv')
        name_to_ticker_mapping = pd.read_csv(path_to_csv, header=None).rename(columns={
            0: 'stock_name', 1: 'ticker', 2: 'comment'})

        trades_with_tickers = trades_copy.merge(name_to_ticker_mapping[['stock_name', 'ticker']],on='stock_name', how='left')
        
        # Handle malformed dates more gracefully
        print(f"Converting {len(trades_with_tickers)} purchase dates...")
        trades_with_tickers['purchase_date'] = pd.to_datetime(
            trades_with_tickers['purchase_date'], 
            format='%m/%d/%Y', 
            errors='coerce'
        )
        
        # Report and filter out invalid dates
        invalid_dates = trades_with_tickers['purchase_date'].isnull()
        if invalid_dates.sum() > 0:
            print(f"⚠️ Warning: {invalid_dates.sum()} records with invalid dates will be excluded")
            print("Sample invalid date values:")
            invalid_samples = trades_copy.loc[invalid_dates, 'purchase_date'].unique()[:5]
            for sample in invalid_samples:
                print(f"  - '{sample}'")
            
            # Remove records with invalid dates
            trades_with_tickers = trades_with_tickers[~invalid_dates].copy()
            print(f"✅ Kept {len(trades_with_tickers)} records with valid dates")

    return trades_with_tickers

































































