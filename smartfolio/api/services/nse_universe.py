"""
nse_universe.py — Full NSE-listed stock universe with sector/industry metadata.
Covers Nifty 50, Nifty 100, Nifty 200, Nifty Midcap 150, and Nifty 500 constituents.
Each stock: symbol -> {name, sector, industry, cap, index}
"""
from typing import Dict, List, Optional

NSE_STOCKS: Dict[str, dict] = {
    # ── NIFTY 50 ──────────────────────────────────────────────────────────
    "RELIANCE":   {"name": "Reliance Industries Ltd.",        "sector": "Energy",               "industry": "Oil & Gas Refining",      "cap": "Large", "index": "NIFTY 50"},
    "TCS":        {"name": "Tata Consultancy Services",       "sector": "IT",                   "industry": "IT Services",             "cap": "Large", "index": "NIFTY 50"},
    "HDFCBANK":   {"name": "HDFC Bank Ltd.",                  "sector": "Financials",           "industry": "Private Banks",           "cap": "Large", "index": "NIFTY 50"},
    "ICICIBANK":  {"name": "ICICI Bank Ltd.",                 "sector": "Financials",           "industry": "Private Banks",           "cap": "Large", "index": "NIFTY 50"},
    "INFY":       {"name": "Infosys Ltd.",                    "sector": "IT",                   "industry": "IT Services",             "cap": "Large", "index": "NIFTY 50"},
    "BHARTIARTL": {"name": "Bharti Airtel Ltd.",              "sector": "Telecom",              "industry": "Telecom Services",        "cap": "Large", "index": "NIFTY 50"},
    "ITC":        {"name": "ITC Ltd.",                        "sector": "Consumer Staples",     "industry": "Cigarettes & FMCG",       "cap": "Large", "index": "NIFTY 50"},
    "SBIN":       {"name": "State Bank of India",             "sector": "Financials",           "industry": "Public Sector Banks",     "cap": "Large", "index": "NIFTY 50"},
    "LT":         {"name": "Larsen & Toubro Ltd.",            "sector": "Industrials",          "industry": "Construction & EPC",      "cap": "Large", "index": "NIFTY 50"},
    "HINDUNILVR": {"name": "Hindustan Unilever Ltd.",         "sector": "Consumer Staples",     "industry": "FMCG",                    "cap": "Large", "index": "NIFTY 50"},
    "KOTAKBANK":  {"name": "Kotak Mahindra Bank Ltd.",        "sector": "Financials",           "industry": "Private Banks",           "cap": "Large", "index": "NIFTY 50"},
    "AXISBANK":   {"name": "Axis Bank Ltd.",                  "sector": "Financials",           "industry": "Private Banks",           "cap": "Large", "index": "NIFTY 50"},
    "TITAN":      {"name": "Titan Company Ltd.",              "sector": "Consumer Discretionary","industry": "Jewellery & Watches",    "cap": "Large", "index": "NIFTY 50"},
    "SUNPHARMA":  {"name": "Sun Pharmaceutical Ind. Ltd.",    "sector": "Healthcare",           "industry": "Pharmaceuticals",         "cap": "Large", "index": "NIFTY 50"},
    "TATAMOTORS": {"name": "Tata Motors Ltd.",                "sector": "Automobile",           "industry": "Commercial Vehicles",     "cap": "Large", "index": "NIFTY 50"},
    "MARUTI":     {"name": "Maruti Suzuki India Ltd.",        "sector": "Automobile",           "industry": "Passenger Vehicles",      "cap": "Large", "index": "NIFTY 50"},
    "NTPC":       {"name": "NTPC Ltd.",                       "sector": "Utilities",            "industry": "Power Generation",        "cap": "Large", "index": "NIFTY 50"},
    "ONGC":       {"name": "Oil & Natural Gas Corp.",         "sector": "Energy",               "industry": "Oil & Gas Exploration",   "cap": "Large", "index": "NIFTY 50"},
    "POWERGRID":  {"name": "Power Grid Corp. of India",       "sector": "Utilities",            "industry": "Power Transmission",      "cap": "Large", "index": "NIFTY 50"},
    "BAJFINANCE": {"name": "Bajaj Finance Ltd.",              "sector": "Financials",           "industry": "Consumer Finance",        "cap": "Large", "index": "NIFTY 50"},
    "ASIANPAINT": {"name": "Asian Paints Ltd.",               "sector": "Materials",            "industry": "Paints & Coatings",       "cap": "Large", "index": "NIFTY 50"},
    "WIPRO":      {"name": "Wipro Ltd.",                      "sector": "IT",                   "industry": "IT Services",             "cap": "Large", "index": "NIFTY 50"},
    "ULTRACEMCO": {"name": "UltraTech Cement Ltd.",           "sector": "Materials",            "industry": "Cement",                  "cap": "Large", "index": "NIFTY 50"},
    "HCLTECH":    {"name": "HCL Technologies Ltd.",           "sector": "IT",                   "industry": "IT Services",             "cap": "Large", "index": "NIFTY 50"},
    "JSWSTEEL":   {"name": "JSW Steel Ltd.",                  "sector": "Materials",            "industry": "Steel",                   "cap": "Large", "index": "NIFTY 50"},
    "TATASTEEL":  {"name": "Tata Steel Ltd.",                 "sector": "Materials",            "industry": "Steel",                   "cap": "Large", "index": "NIFTY 50"},
    "ADANIENT":   {"name": "Adani Enterprises Ltd.",          "sector": "Commodities",          "industry": "Diversified",             "cap": "Large", "index": "NIFTY 50"},
    "ADANIPORTS": {"name": "Adani Ports & SEZ Ltd.",          "sector": "Industrials",          "industry": "Ports & Logistics",       "cap": "Large", "index": "NIFTY 50"},
    "COALINDIA":  {"name": "Coal India Ltd.",                 "sector": "Energy",               "industry": "Mining",                  "cap": "Large", "index": "NIFTY 50"},
    "BAJAJFINSV": {"name": "Bajaj Finserv Ltd.",              "sector": "Financials",           "industry": "Financial Services",      "cap": "Large", "index": "NIFTY 50"},
    "TECHM":      {"name": "Tech Mahindra Ltd.",              "sector": "IT",                   "industry": "IT Services",             "cap": "Large", "index": "NIFTY 50"},
    "DRREDDY":    {"name": "Dr. Reddy's Laboratories",        "sector": "Healthcare",           "industry": "Pharmaceuticals",         "cap": "Large", "index": "NIFTY 50"},
    "CIPLA":      {"name": "Cipla Ltd.",                      "sector": "Healthcare",           "industry": "Pharmaceuticals",         "cap": "Large", "index": "NIFTY 50"},
    "GRASIM":     {"name": "Grasim Industries Ltd.",          "sector": "Materials",            "industry": "Textiles & Cement",       "cap": "Large", "index": "NIFTY 50"},
    "DIVISLAB":   {"name": "Divi's Laboratories Ltd.",        "sector": "Healthcare",           "industry": "Pharmaceuticals",         "cap": "Large", "index": "NIFTY 50"},
    "EICHERMOT":  {"name": "Eicher Motors Ltd.",              "sector": "Automobile",           "industry": "Two Wheelers",            "cap": "Large", "index": "NIFTY 50"},
    "HEROMOTOCO": {"name": "Hero MotoCorp Ltd.",              "sector": "Automobile",           "industry": "Two Wheelers",            "cap": "Large", "index": "NIFTY 50"},
    "BPCL":       {"name": "Bharat Petroleum Corp.",          "sector": "Energy",               "industry": "Oil Refining",            "cap": "Large", "index": "NIFTY 50"},
    "NESTLEIND":  {"name": "Nestle India Ltd.",               "sector": "Consumer Staples",     "industry": "Food & Beverages",        "cap": "Large", "index": "NIFTY 50"},
    "TATACONSUM": {"name": "Tata Consumer Products Ltd.",     "sector": "Consumer Staples",     "industry": "Food & Beverages",        "cap": "Large", "index": "NIFTY 50"},
    "APOLLOHOSP": {"name": "Apollo Hospitals Enterprise",     "sector": "Healthcare",           "industry": "Hospitals",               "cap": "Large", "index": "NIFTY 50"},
    "BRITANNIA":  {"name": "Britannia Industries Ltd.",       "sector": "Consumer Staples",     "industry": "Food & Beverages",        "cap": "Large", "index": "NIFTY 50"},
    "SBILIFE":    {"name": "SBI Life Insurance Co. Ltd.",     "sector": "Financials",           "industry": "Life Insurance",          "cap": "Large", "index": "NIFTY 50"},
    "HDFCLIFE":   {"name": "HDFC Life Insurance Co. Ltd.",    "sector": "Financials",           "industry": "Life Insurance",          "cap": "Large", "index": "NIFTY 50"},
    "INDUSINDBK": {"name": "IndusInd Bank Ltd.",              "sector": "Financials",           "industry": "Private Banks",           "cap": "Large", "index": "NIFTY 50"},
    "SHREECEM":   {"name": "Shree Cement Ltd.",               "sector": "Materials",            "industry": "Cement",                  "cap": "Large", "index": "NIFTY 50"},
    "HINDALCO":   {"name": "Hindalco Industries Ltd.",        "sector": "Materials",            "industry": "Aluminium",               "cap": "Large", "index": "NIFTY 50"},
    "UPL":        {"name": "UPL Ltd.",                        "sector": "Materials",            "industry": "Agrochemicals",           "cap": "Large", "index": "NIFTY 50"},
    "M&M":        {"name": "Mahindra & Mahindra Ltd.",        "sector": "Automobile",           "industry": "Farm & Commercial Vehicles","cap": "Large","index": "NIFTY 50"},
    "BAJAJ-AUTO": {"name": "Bajaj Auto Ltd.",                 "sector": "Automobile",           "industry": "Two Wheelers",            "cap": "Large", "index": "NIFTY 50"},
    # ── NIFTY 100 / NIFTY NEXT 50 ─────────────────────────────────────────
    "BANKBARODA": {"name": "Bank of Baroda",                  "sector": "Financials",           "industry": "Public Sector Banks",     "cap": "Large", "index": "NIFTY 100"},
    "CANBK":      {"name": "Canara Bank",                     "sector": "Financials",           "industry": "Public Sector Banks",     "cap": "Large", "index": "NIFTY 100"},
    "PNB":        {"name": "Punjab National Bank",            "sector": "Financials",           "industry": "Public Sector Banks",     "cap": "Mid",   "index": "NIFTY 100"},
    "UNIONBANK":  {"name": "Union Bank of India",             "sector": "Financials",           "industry": "Public Sector Banks",     "cap": "Mid",   "index": "NIFTY 100"},
    "IDFCFIRSTB": {"name": "IDFC First Bank Ltd.",            "sector": "Financials",           "industry": "Private Banks",           "cap": "Mid",   "index": "NIFTY 100"},
    "FEDERALBNK": {"name": "Federal Bank Ltd.",               "sector": "Financials",           "industry": "Private Banks",           "cap": "Mid",   "index": "NIFTY 100"},
    "RBLBANK":    {"name": "RBL Bank Ltd.",                   "sector": "Financials",           "industry": "Private Banks",           "cap": "Mid",   "index": "NIFTY 100"},
    "YESBANK":    {"name": "Yes Bank Ltd.",                   "sector": "Financials",           "industry": "Private Banks",           "cap": "Mid",   "index": "NIFTY 100"},
    "AUBANK":     {"name": "AU Small Finance Bank Ltd.",      "sector": "Financials",           "industry": "Small Finance Banks",     "cap": "Mid",   "index": "NIFTY 100"},
    "BANDHANBNK": {"name": "Bandhan Bank Ltd.",               "sector": "Financials",           "industry": "Private Banks",           "cap": "Mid",   "index": "NIFTY 100"},
    "ICICIGI":    {"name": "ICICI Lombard General Insurance", "sector": "Financials",           "industry": "General Insurance",       "cap": "Large", "index": "NIFTY 100"},
    "HDFCAMC":    {"name": "HDFC Asset Management Co.",       "sector": "Financials",           "industry": "Asset Management",        "cap": "Large", "index": "NIFTY 100"},
    "NAUKRI":     {"name": "Info Edge (India) Ltd.",          "sector": "IT",                   "industry": "Internet & Tech",         "cap": "Large", "index": "NIFTY 100"},
    "PIDILITIND": {"name": "Pidilite Industries Ltd.",        "sector": "Materials",            "industry": "Specialty Chemicals",     "cap": "Large", "index": "NIFTY 100"},
    "GODREJCP":   {"name": "Godrej Consumer Products Ltd.",   "sector": "Consumer Staples",     "industry": "FMCG",                    "cap": "Large", "index": "NIFTY 100"},
    "DABUR":      {"name": "Dabur India Ltd.",                "sector": "Consumer Staples",     "industry": "FMCG",                    "cap": "Large", "index": "NIFTY 100"},
    "MARICO":     {"name": "Marico Ltd.",                     "sector": "Consumer Staples",     "industry": "FMCG",                    "cap": "Large", "index": "NIFTY 100"},
    "COLPAL":     {"name": "Colgate-Palmolive (India) Ltd.",  "sector": "Consumer Staples",     "industry": "Personal Care",           "cap": "Large", "index": "NIFTY 100"},
    "VBL":        {"name": "Varun Beverages Ltd.",            "sector": "Consumer Staples",     "industry": "Food & Beverages",        "cap": "Large", "index": "NIFTY 100"},
    "TATAPOWER":  {"name": "Tata Power Company Ltd.",         "sector": "Utilities",            "industry": "Integrated Power",        "cap": "Large", "index": "NIFTY 100"},
    "RECLTD":     {"name": "REC Ltd.",                        "sector": "Financials",           "industry": "Power Finance",           "cap": "Large", "index": "NIFTY 100"},
    "PFC":        {"name": "Power Finance Corporation",       "sector": "Financials",           "industry": "Power Finance",           "cap": "Large", "index": "NIFTY 100"},
    "IRFC":       {"name": "Indian Railway Finance Corp.",    "sector": "Financials",           "industry": "Infrastructure Finance",  "cap": "Large", "index": "NIFTY 100"},
    "IOC":        {"name": "Indian Oil Corporation",          "sector": "Energy",               "industry": "Oil Refining",            "cap": "Large", "index": "NIFTY 100"},
    "HINDPETRO":  {"name": "Hindustan Petroleum Corp.",       "sector": "Energy",               "industry": "Oil Refining",            "cap": "Large", "index": "NIFTY 100"},
    "GAIL":       {"name": "GAIL (India) Ltd.",               "sector": "Energy",               "industry": "Gas Transmission",        "cap": "Large", "index": "NIFTY 100"},
    "INDIGO":     {"name": "IndiGo (InterGlobe Aviation)",    "sector": "Industrials",          "industry": "Airlines",                "cap": "Large", "index": "NIFTY 100"},
    "IRCTC":      {"name": "Indian Railway Catering & Tourism","sector": "Industrials",         "industry": "Travel & Tourism",        "cap": "Large", "index": "NIFTY 100"},
    "DMART":      {"name": "Avenue Supermarts Ltd. (D-Mart)", "sector": "Consumer Discretionary","industry": "Retail",                 "cap": "Large", "index": "NIFTY 100"},
    "TRENT":      {"name": "Trent Ltd. (Tata Retail)",        "sector": "Consumer Discretionary","industry": "Retail",                 "cap": "Large", "index": "NIFTY 100"},
    "PAGEIND":    {"name": "Page Industries Ltd.",            "sector": "Consumer Discretionary","industry": "Textiles & Apparel",     "cap": "Large", "index": "NIFTY 100"},
    "AUROPHARMA": {"name": "Aurobindo Pharma Ltd.",           "sector": "Healthcare",           "industry": "Pharmaceuticals",         "cap": "Large", "index": "NIFTY 100"},
    "LUPIN":      {"name": "Lupin Ltd.",                      "sector": "Healthcare",           "industry": "Pharmaceuticals",         "cap": "Large", "index": "NIFTY 100"},
    "BIOCON":     {"name": "Biocon Ltd.",                     "sector": "Healthcare",           "industry": "Biotechnology",           "cap": "Large", "index": "NIFTY 100"},
    "TORNTPHARM": {"name": "Torrent Pharmaceuticals Ltd.",    "sector": "Healthcare",           "industry": "Pharmaceuticals",         "cap": "Large", "index": "NIFTY 100"},
    "ALKEM":      {"name": "Alkem Laboratories Ltd.",         "sector": "Healthcare",           "industry": "Pharmaceuticals",         "cap": "Large", "index": "NIFTY 100"},
    "ABBOTINDIA": {"name": "Abbott India Ltd.",               "sector": "Healthcare",           "industry": "Pharmaceuticals",         "cap": "Large", "index": "NIFTY 100"},
    "FORTIS":     {"name": "Fortis Healthcare Ltd.",          "sector": "Healthcare",           "industry": "Hospitals",               "cap": "Large", "index": "NIFTY 100"},
    "MAXHEALTH":  {"name": "Max Healthcare Institute",        "sector": "Healthcare",           "industry": "Hospitals",               "cap": "Large", "index": "NIFTY 100"},
    "HAVELLS":    {"name": "Havells India Ltd.",              "sector": "Consumer Discretionary","industry": "Electrical Equipment",   "cap": "Large", "index": "NIFTY 100"},
    "VOLTAS":     {"name": "Voltas Ltd.",                     "sector": "Consumer Discretionary","industry": "AC & Appliances",        "cap": "Large", "index": "NIFTY 100"},
    "POLYCAB":    {"name": "Polycab India Ltd.",              "sector": "Industrials",          "industry": "Cables & Wires",          "cap": "Large", "index": "NIFTY 100"},
    "SIEMENS":    {"name": "Siemens Ltd.",                    "sector": "Industrials",          "industry": "Industrial Equipment",    "cap": "Large", "index": "NIFTY 100"},
    "ABB":        {"name": "ABB India Ltd.",                  "sector": "Industrials",          "industry": "Industrial Equipment",    "cap": "Large", "index": "NIFTY 100"},
    "BHEL":       {"name": "Bharat Heavy Electricals Ltd.",   "sector": "Industrials",          "industry": "Heavy Engineering",       "cap": "Large", "index": "NIFTY 100"},
    "BEL":        {"name": "Bharat Electronics Ltd.",         "sector": "Industrials",          "industry": "Defence Electronics",     "cap": "Large", "index": "NIFTY 100"},
    "HAL":        {"name": "Hindustan Aeronautics Ltd.",      "sector": "Industrials",          "industry": "Aerospace & Defence",     "cap": "Large", "index": "NIFTY 100"},
    "MUTHOOTFIN": {"name": "Muthoot Finance Ltd.",            "sector": "Financials",           "industry": "Gold Finance",            "cap": "Large", "index": "NIFTY 100"},
    "CHOLAFIN":   {"name": "Cholamandalam Investment",        "sector": "Financials",           "industry": "Vehicle Finance",         "cap": "Large", "index": "NIFTY 100"},
    "SHRIRAMFIN": {"name": "Shriram Finance Ltd.",            "sector": "Financials",           "industry": "CV Finance",              "cap": "Large", "index": "NIFTY 100"},
    "LICHSGFIN":  {"name": "LIC Housing Finance Ltd.",        "sector": "Financials",           "industry": "Housing Finance",         "cap": "Large", "index": "NIFTY 100"},
    "PNBHOUSING": {"name": "PNB Housing Finance Ltd.",        "sector": "Financials",           "industry": "Housing Finance",         "cap": "Mid",   "index": "NIFTY 100"},
    "MANAPPURAM": {"name": "Manappuram Finance Ltd.",         "sector": "Financials",           "industry": "Gold Finance",            "cap": "Mid",   "index": "NIFTY 100"},
    "ADANIGREEN": {"name": "Adani Green Energy Ltd.",         "sector": "Utilities",            "industry": "Renewable Energy",        "cap": "Large", "index": "NIFTY 100"},
    "ADANIPOWER": {"name": "Adani Power Ltd.",                "sector": "Utilities",            "industry": "Power Generation",        "cap": "Large", "index": "NIFTY 100"},
    # ── NIFTY MIDCAP 150 ──────────────────────────────────────────────────
    "ASHOKLEY":   {"name": "Ashok Leyland Ltd.",              "sector": "Automobile",           "industry": "Commercial Vehicles",     "cap": "Large", "index": "NIFTY Midcap"},
    "TVSMOTOR":   {"name": "TVS Motor Company Ltd.",          "sector": "Automobile",           "industry": "Two Wheelers",            "cap": "Large", "index": "NIFTY Midcap"},
    "EXIDEIND":   {"name": "Exide Industries Ltd.",           "sector": "Automobile",           "industry": "Auto Batteries",          "cap": "Mid",   "index": "NIFTY Midcap"},
    "MOTHERSON":  {"name": "Samvardhana Motherson Intl.",     "sector": "Automobile",           "industry": "Auto Components",         "cap": "Large", "index": "NIFTY Midcap"},
    "BOSCHLTD":   {"name": "Bosch Ltd.",                      "sector": "Automobile",           "industry": "Auto Components",         "cap": "Large", "index": "NIFTY Midcap"},
    "BALKRISIND": {"name": "Balkrishna Industries Ltd.",      "sector": "Automobile",           "industry": "Tyres",                   "cap": "Large", "index": "NIFTY Midcap"},
    "APOLLOTYRE": {"name": "Apollo Tyres Ltd.",               "sector": "Automobile",           "industry": "Tyres",                   "cap": "Large", "index": "NIFTY Midcap"},
    "MRF":        {"name": "MRF Ltd.",                        "sector": "Automobile",           "industry": "Tyres",                   "cap": "Large", "index": "NIFTY Midcap"},
    "CEATLTD":    {"name": "CEAT Ltd.",                       "sector": "Automobile",           "industry": "Tyres",                   "cap": "Mid",   "index": "NIFTY Midcap"},
    "TATAELXSI":  {"name": "Tata Elxsi Ltd.",                 "sector": "IT",                   "industry": "Product Engineering",     "cap": "Large", "index": "NIFTY Midcap"},
    "COFORGE":    {"name": "Coforge Ltd.",                    "sector": "IT",                   "industry": "IT Services",             "cap": "Large", "index": "NIFTY Midcap"},
    "MPHASIS":    {"name": "Mphasis Ltd.",                    "sector": "IT",                   "industry": "IT Services",             "cap": "Large", "index": "NIFTY Midcap"},
    "PERSISTENT": {"name": "Persistent Systems Ltd.",         "sector": "IT",                   "industry": "IT Services",             "cap": "Large", "index": "NIFTY Midcap"},
    "LTIM":       {"name": "LTIMindtree Ltd.",                "sector": "IT",                   "industry": "IT Services",             "cap": "Large", "index": "NIFTY Midcap"},
    "KPITTECH":   {"name": "KPIT Technologies Ltd.",          "sector": "IT",                   "industry": "Automotive IT",           "cap": "Large", "index": "NIFTY Midcap"},
    "ZOMATO":     {"name": "Zomato Ltd.",                     "sector": "Consumer Discretionary","industry": "Food Delivery",          "cap": "Large", "index": "NIFTY Midcap"},
    "NYKAA":      {"name": "FSN E-Commerce (Nykaa)",          "sector": "Consumer Discretionary","industry": "E-Commerce",            "cap": "Large", "index": "NIFTY Midcap"},
    "POLICYBZR":  {"name": "PB Fintech Ltd. (PolicyBazaar)",  "sector": "Financials",           "industry": "Insurance Aggregator",   "cap": "Large", "index": "NIFTY Midcap"},
    "LODHA":      {"name": "Macrotech Developers (Lodha)",    "sector": "Real Estate",          "industry": "Real Estate Dev.",        "cap": "Large", "index": "NIFTY Midcap"},
    "GODREJPROP": {"name": "Godrej Properties Ltd.",          "sector": "Real Estate",          "industry": "Real Estate Dev.",        "cap": "Large", "index": "NIFTY Midcap"},
    "OBEROIRLTY": {"name": "Oberoi Realty Ltd.",              "sector": "Real Estate",          "industry": "Real Estate Dev.",        "cap": "Large", "index": "NIFTY Midcap"},
    "PRESTIGE":   {"name": "Prestige Estates Projects Ltd.",  "sector": "Real Estate",          "industry": "Real Estate Dev.",        "cap": "Large", "index": "NIFTY Midcap"},
    "DLF":        {"name": "DLF Ltd.",                        "sector": "Real Estate",          "industry": "Real Estate Dev.",        "cap": "Large", "index": "NIFTY Midcap"},
    "PHOENIXLTD": {"name": "Phoenix Mills Ltd.",              "sector": "Real Estate",          "industry": "Retail Malls",            "cap": "Large", "index": "NIFTY Midcap"},
    # ── CHEMICALS & SPECIALTY ─────────────────────────────────────────────
    "NAVINFLUOR": {"name": "Navin Fluorine Intl. Ltd.",       "sector": "Materials",            "industry": "Specialty Chemicals",     "cap": "Mid",   "index": "NIFTY 500"},
    "DEEPAKNTR":  {"name": "Deepak Nitrite Ltd.",             "sector": "Materials",            "industry": "Specialty Chemicals",     "cap": "Large", "index": "NIFTY 500"},
    "SOLARINDS":  {"name": "Solar Industries India Ltd.",     "sector": "Materials",            "industry": "Explosives & Defence",    "cap": "Large", "index": "NIFTY 500"},
    "AARTIIND":   {"name": "Aarti Industries Ltd.",           "sector": "Materials",            "industry": "Specialty Chemicals",     "cap": "Large", "index": "NIFTY 500"},
    "VINATIORGA": {"name": "Vinati Organics Ltd.",            "sector": "Materials",            "industry": "Specialty Chemicals",     "cap": "Mid",   "index": "NIFTY 500"},
    "FINEORG":    {"name": "Fine Organic Industries Ltd.",    "sector": "Materials",            "industry": "Specialty Chemicals",     "cap": "Mid",   "index": "NIFTY 500"},
    "PIIND":      {"name": "PI Industries Ltd.",              "sector": "Materials",            "industry": "Agrochemicals",           "cap": "Large", "index": "NIFTY 500"},
    "COROMANDEL": {"name": "Coromandel International Ltd.",   "sector": "Materials",            "industry": "Fertilisers",             "cap": "Large", "index": "NIFTY 500"},
    # ── METALS & MINING ───────────────────────────────────────────────────
    "VEDL":       {"name": "Vedanta Ltd.",                    "sector": "Materials",            "industry": "Diversified Metals",      "cap": "Large", "index": "NIFTY 500"},
    "SAIL":       {"name": "Steel Authority of India Ltd.",   "sector": "Materials",            "industry": "Steel",                   "cap": "Large", "index": "NIFTY 500"},
    "JINDALSTEL": {"name": "Jindal Steel & Power Ltd.",       "sector": "Materials",            "industry": "Steel",                   "cap": "Large", "index": "NIFTY 500"},
    "NMDC":       {"name": "NMDC Ltd.",                       "sector": "Materials",            "industry": "Iron Ore Mining",         "cap": "Large", "index": "NIFTY 500"},
    "HINDZINC":   {"name": "Hindustan Zinc Ltd.",             "sector": "Materials",            "industry": "Zinc & Lead",             "cap": "Large", "index": "NIFTY 500"},
    "NATIONALUM": {"name": "National Aluminium Co. Ltd.",     "sector": "Materials",            "industry": "Aluminium",               "cap": "Mid",   "index": "NIFTY 500"},
    # ── ENERGY & GAS ──────────────────────────────────────────────────────
    "ATGL":       {"name": "Adani Total Gas Ltd.",            "sector": "Energy",               "industry": "Gas Distribution",        "cap": "Large", "index": "NIFTY 500"},
    "MGL":        {"name": "Mahanagar Gas Ltd.",              "sector": "Energy",               "industry": "Gas Distribution",        "cap": "Mid",   "index": "NIFTY 500"},
    "IGL":        {"name": "Indraprastha Gas Ltd.",           "sector": "Energy",               "industry": "Gas Distribution",        "cap": "Large", "index": "NIFTY 500"},
    "GUJGASLTD":  {"name": "Gujarat Gas Ltd.",               "sector": "Energy",               "industry": "Gas Distribution",        "cap": "Mid",   "index": "NIFTY 500"},
    "PETRONET":   {"name": "Petronet LNG Ltd.",               "sector": "Energy",               "industry": "LNG Infrastructure",      "cap": "Large", "index": "NIFTY 500"},
    # ── PAINTS & BUILDING MATERIALS ───────────────────────────────────────
    "BERGEPAINT": {"name": "Berger Paints India Ltd.",        "sector": "Materials",            "industry": "Paints",                  "cap": "Large", "index": "NIFTY 500"},
    "KANSAINER":  {"name": "Kansai Nerolac Paints Ltd.",      "sector": "Materials",            "industry": "Paints",                  "cap": "Mid",   "index": "NIFTY 500"},
    "ACC":        {"name": "ACC Ltd.",                        "sector": "Materials",            "industry": "Cement",                  "cap": "Large", "index": "NIFTY 500"},
    "AMBUJACEM":  {"name": "Ambuja Cements Ltd.",             "sector": "Materials",            "industry": "Cement",                  "cap": "Large", "index": "NIFTY 500"},
    "DALBHARAT":  {"name": "Dalmia Bharat Ltd.",              "sector": "Materials",            "industry": "Cement",                  "cap": "Large", "index": "NIFTY 500"},
    # ── DEFENCE & AEROSPACE ───────────────────────────────────────────────
    "RVNL":       {"name": "Rail Vikas Nigam Ltd.",           "sector": "Industrials",          "industry": "Railway Infrastructure",  "cap": "Mid",   "index": "NIFTY 500"},
    "COCHINSHIP": {"name": "Cochin Shipyard Ltd.",            "sector": "Industrials",          "industry": "Shipbuilding",            "cap": "Mid",   "index": "NIFTY 500"},
    "MAZAGON":    {"name": "Mazagon Dock Shipbuilders",       "sector": "Industrials",          "industry": "Shipbuilding",            "cap": "Mid",   "index": "NIFTY 500"},
    "IRCON":      {"name": "Ircon International Ltd.",        "sector": "Industrials",          "industry": "Railway Infrastructure",  "cap": "Mid",   "index": "NIFTY 500"},
    "CUMMINSIND": {"name": "Cummins India Ltd.",              "sector": "Industrials",          "industry": "Industrial Equipment",    "cap": "Large", "index": "NIFTY 500"},
    "THERMAX":    {"name": "Thermax Ltd.",                    "sector": "Industrials",          "industry": "Energy Equipment",        "cap": "Large", "index": "NIFTY 500"},
    "NCC":        {"name": "NCC Ltd.",                        "sector": "Industrials",          "industry": "Construction",            "cap": "Mid",   "index": "NIFTY 500"},
    # ── DIAGNOSTICS & HEALTHCARE ──────────────────────────────────────────
    "METROPOLIS": {"name": "Metropolis Healthcare Ltd.",      "sector": "Healthcare",           "industry": "Diagnostics",             "cap": "Mid",   "index": "NIFTY 500"},
    "NH":         {"name": "Narayana Hrudayalaya Ltd.",       "sector": "Healthcare",           "industry": "Hospitals",               "cap": "Mid",   "index": "NIFTY 500"},
    "IPCALAB":    {"name": "IPCA Laboratories Ltd.",          "sector": "Healthcare",           "industry": "Pharmaceuticals",         "cap": "Mid",   "index": "NIFTY 500"},
    "GLENMARK":   {"name": "Glenmark Pharmaceuticals",        "sector": "Healthcare",           "industry": "Pharmaceuticals",         "cap": "Mid",   "index": "NIFTY 500"},
    # ── LOGISTICS ──────────────────────────────────────────────────────────
    "DELHIVERY":  {"name": "Delhivery Ltd.",                  "sector": "Industrials",          "industry": "Logistics Tech",          "cap": "Large", "index": "NIFTY 500"},
    "BLUEDART":   {"name": "Blue Dart Express Ltd.",          "sector": "Industrials",          "industry": "Logistics",               "cap": "Mid",   "index": "NIFTY 500"},
    # ── FINTECH & NEW-AGE ─────────────────────────────────────────────────
    "PAYTM":      {"name": "One 97 Communications (Paytm)",   "sector": "Financials",           "industry": "Fintech",                 "cap": "Mid",   "index": "NIFTY 500"},
    "ANGELONE":   {"name": "Angel One Ltd.",                  "sector": "Financials",           "industry": "Stock Broking",           "cap": "Mid",   "index": "NIFTY 500"},
    "CDSL":       {"name": "Central Depository Services",     "sector": "Financials",           "industry": "Capital Markets",         "cap": "Large", "index": "NIFTY 500"},
    "BSE":        {"name": "BSE Ltd.",                        "sector": "Financials",           "industry": "Stock Exchange",          "cap": "Mid",   "index": "NIFTY 500"},
    "MCX":        {"name": "Multi Commodity Exchange",        "sector": "Financials",           "industry": "Commodity Exchange",      "cap": "Mid",   "index": "NIFTY 500"},
    # ── TEXTILES & APPAREL ────────────────────────────────────────────────
    "RAYMOND":    {"name": "Raymond Ltd.",                    "sector": "Consumer Discretionary","industry": "Textiles",               "cap": "Mid",   "index": "NIFTY 500"},
    "WELSPUNIND": {"name": "Welspun India Ltd.",              "sector": "Consumer Discretionary","industry": "Home Textiles",          "cap": "Mid",   "index": "NIFTY 500"},
    "TRIDENT":    {"name": "Trident Ltd.",                    "sector": "Consumer Discretionary","industry": "Home Textiles",          "cap": "Mid",   "index": "NIFTY 500"},
    # ── MEDIA & ENTERTAINMENT ────────────────────────────────────────────
    "ZEEL":       {"name": "Zee Entertainment Enterprises",   "sector": "Consumer Discretionary","industry": "Media & Entertainment",  "cap": "Mid",   "index": "NIFTY 500"},
    "PVRINOX":    {"name": "PVR INOX Ltd.",                   "sector": "Consumer Discretionary","industry": "Film Exhibition",        "cap": "Mid",   "index": "NIFTY 500"},
    # ── UTILITIES & RENEWABLES ────────────────────────────────────────────
    "TORNTPOWER": {"name": "Torrent Power Ltd.",              "sector": "Utilities",            "industry": "Integrated Power",        "cap": "Large", "index": "NIFTY 500"},
    "CESC":       {"name": "CESC Ltd.",                       "sector": "Utilities",            "industry": "Integrated Power",        "cap": "Mid",   "index": "NIFTY 500"},
    "SUZLON":     {"name": "Suzlon Energy Ltd.",              "sector": "Utilities",            "industry": "Wind Energy",             "cap": "Large", "index": "NIFTY 500"},
    # ── CONSUMER ELECTRONICS ─────────────────────────────────────────────
    "DIXON":      {"name": "Dixon Technologies (India)",      "sector": "Consumer Discretionary","industry": "Electronics Mfg.",       "cap": "Mid",   "index": "NIFTY 500"},
    "AMBER":      {"name": "Amber Enterprises India",         "sector": "Consumer Discretionary","industry": "AC Manufacturing",       "cap": "Mid",   "index": "NIFTY 500"},
    "CROMPTON":   {"name": "Crompton Greaves Consumer",       "sector": "Consumer Discretionary","industry": "Electrical Appliances",  "cap": "Mid",   "index": "NIFTY 500"},
    "BLUESTARCO": {"name": "Blue Star Ltd.",                  "sector": "Consumer Discretionary","industry": "AC & Appliances",        "cap": "Mid",   "index": "NIFTY 500"},
    # ── INSURANCE ────────────────────────────────────────────────────────
    "GICRE":      {"name": "General Insurance Corp.",         "sector": "Financials",           "industry": "Reinsurance",             "cap": "Large", "index": "NIFTY 500"},
    "STARHEALTH": {"name": "Star Health & Allied Insurance",  "sector": "Financials",           "industry": "Health Insurance",        "cap": "Large", "index": "NIFTY 500"},
    "NIACL":      {"name": "New India Assurance Co.",         "sector": "Financials",           "industry": "General Insurance",       "cap": "Large", "index": "NIFTY 500"},
    # ── AUTOMOBILE EV & NEW-AGE ───────────────────────────────────────────
    "OLECTRA":    {"name": "Olectra Greentech Ltd.",          "sector": "Automobile",           "industry": "Electric Buses",          "cap": "Mid",   "index": "NIFTY 500"},
    "CRAFTSMAN":  {"name": "Craftsman Automation Ltd.",       "sector": "Automobile",           "industry": "Auto Components",         "cap": "Mid",   "index": "NIFTY 500"},
    "SCHAEFFLER": {"name": "Schaeffler India Ltd.",           "sector": "Industrials",          "industry": "Auto Components",         "cap": "Large", "index": "NIFTY 500"},
}

# Sector colour palette for frontend charts
SECTOR_COLORS: Dict[str, str] = {
    "Energy":                "#ef4444",
    "IT":                    "#3b82f6",
    "Financials":            "#8b5cf6",
    "Automobile":            "#f59e0b",
    "Consumer Staples":      "#22c55e",
    "Consumer Discretionary":"#14b8a6",
    "Healthcare":            "#ec4899",
    "Industrials":           "#64748b",
    "Materials":             "#f97316",
    "Utilities":             "#06b6d4",
    "Telecom":               "#a855f7",
    "Real Estate":           "#84cc16",
    "Commodities":           "#d97706",
}

ALL_SECTORS: List[str] = sorted(set(v["sector"] for v in NSE_STOCKS.values()))
ALL_INDICES: List[str] = ["NIFTY 50", "NIFTY 100", "NIFTY Midcap", "NIFTY 500"]


def search_stocks(
    query: str,
    sector: Optional[str] = None,
    cap: Optional[str] = None,
    index: Optional[str] = None,
    limit: int = 20,
) -> List[dict]:
    """
    Fast in-memory full-text stock search.
    Matches query against symbol, company name, sector, and industry.
    Returns up to `limit` matching results.
    """
    q = query.strip().upper()
    results = []

    for sym, meta in NSE_STOCKS.items():
        # Sector filter
        if sector and meta["sector"] != sector:
            continue
        # Cap filter
        if cap and meta["cap"] != cap:
            continue
        # Index filter
        if index and meta.get("index") != index:
            continue
        # Text search
        if q:
            haystack = f"{sym} {meta['name'].upper()} {meta['sector'].upper()} {meta['industry'].upper()}"
            if q not in haystack:
                continue
        results.append({
            "symbol": sym,
            "name": meta["name"],
            "sector": meta["sector"],
            "industry": meta["industry"],
            "cap": meta["cap"],
            "index": meta.get("index", "NSE"),
        })
        if len(results) >= limit:
            break

    return results
