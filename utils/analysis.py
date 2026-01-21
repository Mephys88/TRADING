
import pandas_ta as ta
import pandas as pd
import numpy as np

def calculate_technical_indicators(df):
    """
    Calculate technical indicators: RSI, MACD, Bollinger Bands, EMAs, Volume SMA.
    """
    if df.empty:
        return df

    # RSI
    df['RSI'] = df.ta.rsi(length=14)

    # MACD
    macd = df.ta.macd(fast=12, slow=26, signal=9)
    df = pd.concat([df, macd], axis=1)

    # Bollinger Bands
    bbands = df.ta.bbands(length=20, std=2)
    if bbands is not None and not bbands.empty:
        new_names = {}
        for col in bbands.columns:
            if col.startswith('BBL'): new_names[col] = 'BBL'
            elif col.startswith('BBM'): new_names[col] = 'BBM'
            elif col.startswith('BBU'): new_names[col] = 'BBU'
            elif col.startswith('BBB'): new_names[col] = 'BBB'
            elif col.startswith('BBP'): new_names[col] = 'BBP'
        bbands.rename(columns=new_names, inplace=True)
    
    df = pd.concat([df, bbands], axis=1)

    # EMAs
    df['EMA_50'] = df.ta.ema(length=50)
    df['EMA_200'] = df.ta.ema(length=200)
    
    # Volume SMA for analysis
    if 'volume' in df.columns:
        df['VOL_SMA_20'] = df['volume'].rolling(window=20).mean()
    
    return df

def calculate_fibonacci_levels(df):
    """
    Calculate Fibonacci retracement levels based on the recent high and low.
    """
    if df.empty:
        return {}
    
    recent_high = df['high'].rolling(window=100).max().iloc[-1]
    recent_low = df['low'].rolling(window=100).min().iloc[-1]
    
    diff = recent_high - recent_low
    levels = {
        '0.0%': recent_high,
        '23.6%': recent_high - 0.236 * diff,
        '38.2%': recent_high - 0.382 * diff,
        '50.0%': recent_high - 0.5 * diff,
        '61.8%': recent_high - 0.618 * diff,
        '100.0%': recent_low
    }
    return levels

def calculate_historical_levels(df, window=20, tolerance=0.02):
    """
    Identify historical Support/Resistance levels based on Price Pivots (Highs/Lows)
    over a long period.
    """
    if df.empty:
        return []
    
    levels = []
    
    # Identify local highs and lows
    # We use a rolling window to find points that are the max/min of their neighborhood
    df['is_high'] = df['high'] == df['high'].rolling(window=window, center=True).max()
    df['is_low'] = df['low'] == df['low'].rolling(window=window, center=True).min()
    
    highs = df[df['is_high']]['high'].tolist()
    lows = df[df['is_low']]['low'].tolist()
    
    all_pivots = sorted(highs + lows)
    
    # Cluster levels that are close to each other
    if not all_pivots:
        return []
        
    merged_levels = []
    current_cluster = [all_pivots[0]]
    
    for i in range(1, len(all_pivots)):
        if all_pivots[i] <= current_cluster[-1] * (1 + tolerance):
            current_cluster.append(all_pivots[i])
        else:
            # Average the cluster to get a single strong level
            merged_levels.append(sum(current_cluster) / len(current_cluster))
            current_cluster = [all_pivots[i]]
            
    merged_levels.append(sum(current_cluster) / len(current_cluster))
    
    # Filter only significant levels (e.g. those tested multiple times would be better, 
    # but for now we essentially have all major pivots)
    return merged_levels

def analyze_trend(df):
    """
    Simple trend analysis for display.
    """
    if df.empty or len(df) < 200:
        return "Not enough data", 0
        
    current_close = df['close'].iloc[-1]
    ema_50 = df['EMA_50'].iloc[-1]
    ema_200 = df['EMA_200'].iloc[-1]
    rsi = df['RSI'].iloc[-1]
    
    trend = "Neutrale"
    if current_close > ema_50 and current_close > ema_200:
        trend = "Rialzista"
    elif current_close < ema_50 and current_close < ema_200:
        trend = "Ribassista"
        
    return trend, rsi

def detect_structure(df, window=5):
    """
    Detect recent market structure (HH, HL, LH, LL).
    This is a simplified local extrema check.
    """
    if df.empty or len(df) < window * 4:
        return "Indefinita"
        
    # Find local peaks/valleys
    # We compare last 2 detected pivots
    pass # Implementation requires complex pivot logic, using simplified version below
    
    # Simplified approach: Look at last 2 major highs/lows in 20 periods
    recent = df.tail(50)
    
    # Simple logic: Price position relative to recent High/Low
    high_50 = recent['high'].max()
    low_50 = recent['low'].min()
    current = df['close'].iloc[-1]
    
    if current > high_50 * 0.98:
        return "Test Massimi (Possibile Breakout)"
    elif current < low_50 * 1.02:
        return "Test Minimi (Possibile Breakdown)"
    else:
        return "Range / Consolidamento"

def detect_patterns(df):
    """
    Detect basic candlestick patterns on the last completed candle.
    """
    if df.empty:
        return []
    
    row = df.iloc[-1]
    prev = df.iloc[-2]
    
    patterns = []
    
    body = abs(row['close'] - row['open'])
    upper_wick = row['high'] - max(row['close'], row['open'])
    lower_wick = min(row['close'], row['open']) - row['low']
    total_range = row['high'] - row['low']
    
    # Pin Bar (Hammer/Shooting Star-like)
    if total_range > 0 and lower_wick > (body * 2) and upper_wick < body:
        patterns.append("Pin Bar Rialzista (Hammer)")
    elif total_range > 0 and upper_wick > (body * 2) and lower_wick < body:
        patterns.append("Pin Bar Ribassista (Shooting Star)")
        
    # Engulfing
    # Bullish: Previous Red, Current Green and covers previous body + wick
    if prev['close'] < prev['open'] and row['close'] > row['open']:
         if row['close'] > prev['open'] and row['open'] < prev['close']:
             patterns.append("Bullish Engulfing")
             
    # Bearish: Previous Green, Current Red
    if prev['close'] > prev['open'] and row['close'] < row['open']:
         if row['close'] < prev['open'] and row['open'] > prev['close']:
             patterns.append("Bearish Engulfing")
             
    return patterns

def analyze_volume(df):
    """
    Analyze volume regarding breakout or weakness.
    """
    if df.empty or 'VOL_SMA_20' not in df.columns:
        return "N/A"
        
    curr_vol = df['volume'].iloc[-1]
    avg_vol = df['VOL_SMA_20'].iloc[-1]
    
    if curr_vol > avg_vol * 1.5:
        return "Alto (Possibile Volatilità)"
    elif curr_vol < avg_vol * 0.5:
        return "Basso (Attesa)"
    else:
        return "Normale"

def generate_trading_signal(mtf_data):
    """
    LOGICA STRATEGICA AGGIORNATA: "SMART TREND FOLLOWER"
    OBIETTIVO: Identificare la tendenza primaria e sfruttare i ritracciamenti.
    Note: Requires mtf_data with '1d', '4h', '1h' keys containing dataframes with indicators.
    """
    # Initialize default response
    default_response = {
        "opinion": "DATI INSUFFICIENTI",
        "score": 0,
        "reasons": [],
        "advice": "Dati insufficienti per generare un segnale affidabile.",
        "color": "gray",
        "structure": "N/A"
    }

    # Extract dataframes
    df_daily = mtf_data.get('1d', pd.DataFrame())
    df_4h = mtf_data.get('4h', pd.DataFrame())
    df_1h = mtf_data.get('1h', pd.DataFrame())

    if df_daily.empty or df_1h.empty:
        return default_response
    
    # --- DATA PREPARATION ---
    # Daily (Primary Trend)
    try:
        daily_close = df_daily['close'].iloc[-1]
        daily_ema200 = df_daily['EMA_200'].iloc[-1]
    except:
        return default_response

    # 1H (Momentum & Execution)
    try:
        h1_close = df_1h['close'].iloc[-1]
        h1_ema50 = df_1h['EMA_50'].iloc[-1]
        h1_ema200 = df_1h['EMA_200'].iloc[-1]
        h1_rsi = df_1h['RSI'].iloc[-1]
    except:
        return default_response

    structure = detect_structure(df_1h)
    
    # --- FASE 1: ANALISI GERARCHICA DEL TREND (Il filtro "Boss") ---
    # Bias di fondo basato su EMA 200 Daily
    bias_fondo = "NEUTRAL"
    if daily_close > daily_ema200:
        bias_fondo = "LONG"
    elif daily_close < daily_ema200:
        bias_fondo = "SHORT"
    
    # --- FASE 2: ANALISI DELLO STATO ATTUALE (Il filtro "Momentum") ---
    # Confronto Prezzo vs EMA 50 e EMA 200 su 1H
    diagnosi = ""
    azione_suggerita = ""
    
    # Definisci lo stato per il template
    context_trend = "RIALZISTA" if bias_fondo == "LONG" else "RIBASSISTA" if bias_fondo == "SHORT" else "NEUTRO"
    context_state = "CONSOLIDAMENTO" # Default

    opinion_header = "NEUTRAL"
    advice_text = ""
    reasons = []
    
    # -- LOGICA LONG --
    if bias_fondo == "LONG":
        reasons.append("Bias di Fondo (Daily): RIALZISTA (Prezzo > EMA 200).")
        
        # Caso A: Prezzo > EMA 200 (1D) MA Prezzo < EMA 50 (1H).
        # Note: We compare H1 Price to Daily EMA 200 indirectly because Bias is LONG.
        # But instructions say: "Confronta il prezzo attuale con la EMA 50 e EMA 200 su Timeframe ORARIO (1H)"
        # And specifically: Caso A: Prezzo > EMA 200 (1D) MA Prezzo < EMA 50 (1H).
        
        if h1_close < h1_ema50:
            diagnosi = "Ritracciamento in corso in trend rialzista (Sconto)."
            azione_suggerita = "CERCARE LONG. Ignorare segnali Short. Attendere arrivo su supporto."
            opinion_header = "BULLISH DIP"
            context_state = "RITRACCIAMENTO"
            reasons.append("H1: Prezzo < EMA 50 (Ritracciamento).")
        
        # Caso B: Prezzo > EMA 200 (1D) E Prezzo > EMA 50 (1H).
        elif h1_close > h1_ema50:
            diagnosi = "Trend in spinta."
            azione_suggerita = "Valutare Breakout o piccoli pullback."
            opinion_header = "BULLISH MOMENTUM" # Adjusted slightly from prompt examples to be descriptive
            context_state = "IMPULSO RIALZISTA"
            reasons.append("H1: Prezzo > EMA 50 (Trend in spinta).")

    # -- LOGICA SHORT (Simmetrica, per completezza anche se l'utente si concentra sul trend follower) --
    elif bias_fondo == "SHORT":
        reasons.append("Bias di Fondo (Daily): RIBASSISTA (Prezzo < EMA 200).")
        
        if h1_close > h1_ema50:
            diagnosi = "Rimbalzo tecnico in trend ribassista."
            azione_suggerita = "CERCARE SHORT. Ignorare segnali Long. Attendere resistenza."
            opinion_header = "BEARISH RALLY"
            context_state = "RIMBALZO"
            reasons.append("H1: Prezzo > EMA 50 (Rimbalzo).")
            
        elif h1_close < h1_ema50:
            diagnosi = "Trend ribassista forte."
            azione_suggerita = "Valutare Breakdown o piccoli rimbalzi per short."
            opinion_header = "BEARISH MOMENTUM"
            context_state = "SPINTA RIBASSISTA"
            reasons.append("H1: Prezzo < EMA 50 (Trend ribassista attivo).")

    # --- FASE 3: FILTRI DI SICUREZZA E RSI (L'Anti-Incastro) ---
    rsi_state = "NEUTRO"
    can_trade = True
    
    if bias_fondo == "LONG":
        if h1_rsi > 70:
            reasons.append("⚠️ RSI > 70: Mercato Ipercomprato. Vietato Comprare.")
            advice_text = "Mercato Euforico (RSI > 70). Non entrare ora, rischio correzione immediata."
            can_trade = False
            opinion_header = "NEUTRAL (RSI HIGH)"
            rsi_state = "IPERCOMPRATO"
        elif h1_rsi < 35:
            reasons.append("✅ RSI < 35: Mercato Ipervenduto (Occasione).")
            advice_text = "RSI in zona di Panico/Sconto (< 35). Ottimo per cercare ingressi se su supporto."
            rsi_state = "IPERVENDUTO"
    
    elif bias_fondo == "SHORT":
        if h1_rsi < 30:
            reasons.append("⚠️ RSI < 30: Mercato Ipervenduto. Vietato Vendere.")
            advice_text = "Mercato Stanco (RSI < 30). Non shortare ora, rischio rimbalzo."
            can_trade = False
            opinion_header = "NEUTRAL (RSI LOW)"
            rsi_state = "IPERVENDUTO"
        elif h1_rsi > 65:
            reasons.append("✅ RSI > 65: Rimbalzo tecnico (Occasione Short).")
            advice_text = "RSI in zona di 'respiro' (> 65). Ottimo per cercare ingressi Short."
            rsi_state = "IPERCOMPRATO"

    # --- FASE 4: CALCOLO LIVELLI OPERATIVI (Smart Levels) ---
    # Utilizziamo i livelli calcolati precedentemente o calcoliamoli qui se necessario
    # Per semplicità, richiamiamo le funzioni helper se disponibili o usiamo stime basate su EMA
    
    # --- FASE 4: CALCOLO LIVELLI OPERATIVI (Smart Levels) ---
    # Utilizziamo i livelli calcolati precedentemente o calcoliamoli qui se necessario
    
    if can_trade:
        fib_levels = calculate_fibonacci_levels(df_1h) # Usiamo H1 per livelli operativi
        
        # Trova livelli vicini
        supports = sorted([v for k,v in fib_levels.items() if v < h1_close], reverse=True)
        resistances = sorted([v for k,v in fib_levels.items() if v > h1_close])
        
        # Default fallbacks
        # IMPORTANT: Ensure fallbacks respect geometry (Sup < Price < Res)
        # EMA 200 can be support or res depending on trend, so we use percentage of close for safe fallbacks
        
        sup_1 = supports[0] if len(supports) > 0 else h1_close * 0.98
        sup_2 = supports[1] if len(supports) > 1 else h1_close * 0.96
        res_1 = resistances[0] if len(resistances) > 0 else h1_close * 1.02
        res_2 = resistances[1] if len(resistances) > 1 else h1_close * 1.04

        advice_text = ""
        
        if bias_fondo == "LONG":
            # STRATEGIA LONG:
            # Entry: Supporti (Attesa Pullback)
            # TP: Resistenza
            # SL: Sotto Supporto/EMA
            
            entry_zone_low = sup_2
            entry_zone_high = sup_1
            target = res_1
            invalidazione = h1_ema200 * 0.99
            
            advice_text = (
                f"Non operare contro il trend primario. L'azione consigliata è ATTENDERE che il prezzo ritracci verso la zona di valore "
                f"compresa tra ${entry_zone_high:,.0f} e ${entry_zone_low:,.0f}. Solo al test di questi livelli (supporti) cercare ingresso LONG. "
                f"⛔ Stop Loss: Sotto ${invalidazione:,.0f}. 🎯 Take Profit: Primo target a ${target:,.0f}."
            )
            
        elif bias_fondo == "SHORT":
            # STRATEGIA SHORT:
            # Entry: Resistenze (Attesa Rimbalzo per vendere)
            # TP: Supporto
            # SL: Sopra Resistenza/EMA
            
            entry_zone_low = res_1
            entry_zone_high = res_2
            target = sup_1
            invalidazione = h1_ema200 * 1.01
            
            advice_text = (
                f"Non operare contro il trend primario. L'azione consigliata è ATTENDERE che il prezzo rimbalzi verso la zona di offerta "
                f"compresa tra ${entry_zone_low:,.0f} e ${entry_zone_high:,.0f}. Solo al test di questi livelli (resistenze) cercare ingresso SHORT. "
                f"⛔ Stop Loss: Sopra ${invalidazione:,.0f}. 🎯 Take Profit: Primo target a ${target:,.0f}."
            )

    # --- FORMATTAZIONE OUTPUT ---
    
    # Analisi Contesto String
    analisi_contesto = (
        f"Il Trend Primario (Daily) è [{context_trend}]. "
        f"Attualmente stiamo assistendo a un [{context_state}] sul breve termine (H1). "
        f"L'RSI attuale è [{h1_rsi:.1f}], indicando che il mercato è [{rsi_state}]."
    )
    
    final_advice = f"{analisi_contesto}\n\nCONSIGLIO OPERATIVO (PROFESSIONAL): \"{advice_text}\""
    
    # Determina colore
    color = "gray"
    if "LONG" in bias_fondo and can_trade:
        if "DIP" in opinion_header: color = "green" # Buy the dip
        elif "MOMENTUM" in opinion_header: color = "lightgreen"
    elif "SHORT" in bias_fondo and can_trade:
        if "RALLY" in opinion_header: color = "red" # Sell the rally
        elif "MOMENTUM" in opinion_header: color = "orange"
        
    score = 0 # Placeholder, non più centrale nella nuova logica scritta
    if bias_fondo == "LONG": score += 5
    if can_trade: score += 2

    return {
        "opinion": opinion_header,
        "score": score,
        "reasons": reasons,
        "advice": final_advice, # Contains both Analysis Context and Operational Advice
        "color": color,
        "structure": structure
    }

def analyze_mtf_trend(dfs_dict):
    """
    Analyze trend across multiple timeframes (15m, 1h, 4h, 1d).
    Input: Dict {'15m': df, '1h': df, ...} (must have technical indicators calc already or calc inside)
    Returns: Dict of trend status {'15m': 'BULL', '1h': 'BEAR', ...} and a Confluence Score.
    """
    results = {}
    bullish_count = 0
    bearish_count = 0
    valid_tfs = 0
    
    for tf, df in dfs_dict.items():
        if df.empty:
            results[tf] = "N/A"
            continue
            
        valid_tfs += 1
        # Recalculate basic EMAs if missing (simple check)
        if 'EMA_50' not in df.columns:
            df['EMA_50'] = df.ta.ema(length=50)
            df['EMA_200'] = df.ta.ema(length=200)
            
        close = df['close'].iloc[-1]
        ema50 = df['EMA_50'].iloc[-1]
        ema200 = df['EMA_200'].iloc[-1]
        
        # Simple Traffic Light Logic
        if close > ema50 and close > ema200:
            status = "BULLISH 🟢"
            bullish_count += 1
        elif close < ema50 and close < ema200:
            status = "BEARISH 🔴"
            bearish_count += 1
        else:
            status = "NEUTRAL ⚪"
            
        results[tf] = status
        
    # Confluence Score
    score_text = "Misto / Incerto"
    if bullish_count == valid_tfs and valid_tfs > 0:
        score_text = "FULL BULLISH (Confluenza Totale) 🚀"
    elif bearish_count == valid_tfs and valid_tfs > 0:
        score_text = "FULL BEARISH (Confluenza Totale) 🩸"
    elif bullish_count >= valid_tfs * 0.75:
        score_text = "Strong Bullish ✅"
    elif bearish_count >= valid_tfs * 0.75:
        score_text = "Strong Bearish ⚠️"
        
    return results, score_text

def analyze_dxy_correlation(dxy_df, btc_trend):
    """
    Analyze DXY trend and warn if it contradicts BTC position.
    """
    if dxy_df.empty:
        return "N/A", None, 0
        
    # Calculate DXY Trend
    # Using simple SMA/EMA on close
    dxy_close = dxy_df['Close'].iloc[-1]
    dxy_prev = dxy_df['Close'].iloc[-2]
    dxy_change = ((dxy_close - dxy_prev) / dxy_prev) * 100
    
    # Simple Technicals for DXY
    sma_20 = dxy_df['Close'].rolling(window=20).mean().iloc[-1]
    
    dxy_trend = "Neutrale"
    warning = None
    
    if dxy_close > sma_20 * 1.002: # 0.2% filter
        dxy_trend = "Rialzista (USD Forte) 💵"
        if "LONG" in btc_trend or "Bullish" in btc_trend:
             warning = "⚠️ DXY in salita: Rischio per i Long su BTC!"
    elif dxy_close < sma_20 * 0.998:
        dxy_trend = "Ribassista (USD Debole) 📉"
        if "SHORT" in btc_trend or "Bearish" in btc_trend:
             warning = "⚠️ DXY in discesa: Rischio per gli Short su BTC!"
             
    return dxy_trend, warning, dxy_change
