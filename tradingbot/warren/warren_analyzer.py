import os
import yfinance as yf
from datetime import datetime

# --- KONFIGURATION ---
MARKET_MODE = "EUR"  # "EUR" oder "US"
MIN_SCORE = 50
TOP_N_STOCKS = 5  # Für Newsletter

def get_clean_ticker_list(market):
    """Lädt Ticker-Liste basierend auf Markt"""
    ticker_file = f"ticker{market.lower()}.txt"
    
    if not os.path.exists(ticker_file):
        print(f"⚠️  Datei nicht gefunden: {ticker_file}")
        return []
    
    with open(ticker_file, "r", encoding="utf-8") as f:
        return sorted(list({
            line.strip().replace('\\', '/').split('/')[-1].upper()
            for line in f if line.strip() and not line.strip().upper().endswith('.TXT')
        }))


def analyze_stock(symbol):
    """Analysiert Aktie basierend auf Warren Buffett Kriterien"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        if not info or 'currentPrice' not in info:
            return None
        
        score = 0
        defizite = []
        
        # 1. Burggraben: Marge > 15%
        margin = info.get('profitMargins', 0)
        if margin > 0.15:
            score += 25
        else:
            defizite.append(f"Marge({margin:.1%})")
        
        # 2. Management: ROE > 15%
        roe = info.get('returnOnEquity', 0)
        if roe > 0.15:
            score += 25
        else:
            defizite.append(f"ROE({roe:.1%})")
        
        # 3. Cashflow-Qualität: FCF/NetIncome > 0.8
        fcf = info.get('freeCashflow', 0)
        net_inc = info.get('netIncomeToCommon', 1)
        cash_ratio = fcf / net_inc if net_inc != 0 else 0
        if fcf > 0 and cash_ratio > 0.8:
            score += 25
        else:
            defizite.append(f"Cash({cash_ratio:.1f}x)")
        
        # 4. Sicherheit: Debt/Equity < 80
        de_ratio = info.get('debtToEquity', 999)
        if de_ratio < 80:
            score += 25
        else:
            defizite.append(f"Schuld({de_ratio:.0f})")
        
        price = info.get('currentPrice')
        kgv = info.get('forwardPE') or info.get('trailingPE') or 0
        eps = info.get('forwardEps') or info.get('trailingEps', 1)
        industry = info.get('industry', 'N/A')
        name = info.get('shortName', symbol)
        
        # Fairer Wert Logik
        multiplier = 22 if score == 100 else 15
        fair_value = eps * multiplier
        
        if score >= MIN_SCORE:
            return {
                "Symbol": symbol,
                "Name": name[:18],
                "Industrie": industry[:22],
                "Score": score,
                "KGV": kgv,
                "Kurs": price,
                "Fair": fair_value,
                "Abstand": ((fair_value / price) - 1) * 100,
                "Defizite": ", ".join(defizite) if defizite else "TOP"
            }
    
    except Exception as e:
        print(f"⚠️  Fehler bei {symbol}: {e}")
    
    return None


def run_buffett_monitor(market="EUR", show_all=False):
    """Hauptfunktion: Analysiert alle Aktien"""
    tickers = get_clean_ticker_list(market)
    results = []
    
    print(f"\n📊 Analysiere {len(tickers)} Aktien aus {market} Markt...")
    
    for i, symbol in enumerate(tickers):
        print(f"   [{i+1}/{len(tickers)}] {symbol}...", end="\r")
        data = analyze_stock(symbol)
        if data:
            results.append(data)
    
    print(f"\n{'─'*140}")
    print(f"--- VOLLSTÄNDIGER BUFFETT-MONITOR ({market}) ---")
    
    header = f"{'SYMBOL':<10} | {'NAME':<18} | {'INDUSTRIE':<22} | {'SCORE':<5} | {'KGV':<6} | {'KURS':<8} | {'FAIR':<8} | {'POTENZIAL':<10} | {'DEFIZITE'}"
    print(header)
    print("-" * 140)
    
    if not results:
        print("❌ Keine Aktie erfüllt die Kriterien.")
    else:
        # Sortierung: Höchster Score zuerst, dann höchstes Potenzial
        results.sort(key=lambda x: (x['Score'], x['Abstand']), reverse=True)
        
        for res in results:
            print(f"{res['Symbol']:<10} | {res['Name']:<18} | {res['Industrie']:<22} | {res['Score']:>5} | {res['KGV']:>6.1f} | {res['Kurs']:>8.2f} | {res['Fair']:>8.2f} | {res['Abstand']:>9.1f}% | {res['Defizite']}")
    
    print("\n" + "="*50 + " LEGENDE " + "="*50)
    print("Soll-Werte: Marge > 15%, ROE > 15%, Cashflow > 0.8, Schulden < 80")
    print("Faire Wert Multiple: 100 Pkt = 22x EPS | <100 Pkt = 15x EPS")
    print("=" * 109 + "\n")
    
    return results


def get_top_stocks(market="EUR", n=5):
    """Gibt die Top N Aktien zurück (für Newsletter)"""
    tickers = get_clean_ticker_list(market)
    results = []
    
    for symbol in tickers:
        data = analyze_stock(symbol)
        if data:
            results.append(data)
    
    # Sortiere nach Score und Potenzial
    results.sort(key=lambda x: (x['Score'], x['Abstand']), reverse=True)
    
    return results[:n]


if __name__ == "__main__":
    # Interaktiv: Benutzer kann Markt wählen
    print("Warren Buffett Stock Analyzer")
    print("=" * 50)
    print("1. EUR (Europa)")
    print("2. US (United States)")
    choice = input("Wähle Markt (1 oder 2): ").strip()
    
    market = "EUR" if choice == "1" else "US"
    run_buffett_monitor(market)
