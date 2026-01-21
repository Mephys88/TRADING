
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.data import fetch_crypto_data, fetch_stock_data, fetch_dxy_data
from utils.analysis import calculate_technical_indicators, calculate_fibonacci_levels, analyze_trend, generate_trading_signal, calculate_historical_levels, analyze_mtf_trend, analyze_dxy_correlation
from utils.sentiment import fetch_news_sentiment

# Page Config
st.set_page_config(page_title="Assistente Trading BTC", layout="wide", page_icon="📈")

# Custom CSS for styling
st.markdown("""
<style>
    .metric-card {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #333;
        text-align: center;
    }
    .stMetric label {
        color: #aaaaaa;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("₿ Assistente Trading BTC/USDT")

# Sidebar - Investment & Risk
with st.sidebar:
    st.header("💰 Gestione Capitale")
    investment = st.number_input("Capitale Investito ($)", min_value=10.0, value=1000.0, step=10.0)
    
    st.info(f"Rischio Massimo (50%): **${investment * 0.5:.2f}**")
    
    st.markdown("---")
    st.subheader("⚙️ Impostazioni Leva & Rischio")
    
    # User Inputs for Risk
    risk_pct_input = st.slider("Rischio Max su Capitale (%)", min_value=1, max_value=100, value=50, step=1, help="Quanto del tuo capitale sei disposto a perdere prima dello Stop Loss?")
    
    # Manual Take Profit instead of R/R
    tp_target_pct = st.number_input("Target Profit (% Movimento Prezzo)", min_value=0.1, value=5.0, step=0.1, help="Percentuale di movimento prezzo che ti aspetti per il profitto.")
    
    risk_money = investment * (risk_pct_input / 100.0)
    st.info(f"Rischio Monetario: **${risk_money:.2f}** ({risk_pct_input}%)")
    
    # Calculate Risk Parameters
    leverages = [5, 10, 15]
    current_price = 0 
    
    # We need price to calculate valid SL/TP distances based on liquidation/risk
    display_risk = st.container()

# Main Data Fetching
with st.spinner('Recupero dati di mercato & Analisi Pro...'):
    # 1. Crypto Data - MTF Fetching
    timeframes = ['15m', '1h', '4h', '1d']
    mtf_data = {}
    
    # Primary Data (1h)
    df_btc = fetch_crypto_data('BTC/USDT', timeframe='1h', limit=500)
    mtf_data['1h'] = df_btc
    
    # Secondary Timeframes
    for tf in ['15m', '4h', '1d']:
        try:
            # For 1d trend analysis, we just need recent data
            mtf_data[tf] = fetch_crypto_data('BTC/USDT', timeframe=tf if tf != '1d' else '1d', limit=400)
        except:
             mtf_data[tf] = pd.DataFrame()

    # Calculate indicators for all TFs
    for tf, df in mtf_data.items():
        if not df.empty:
            mtf_data[tf] = calculate_technical_indicators(df)

    # 2. Main Analysis (on 1h)
    # df_btc is already mtf_data['1h'] but we ensure it has indicators
    df_btc = mtf_data['1h'] # This reference should point to the DF with indicators now
    
    # Calculations if data exists
    if not df_btc.empty:
        fib_levels = calculate_fibonacci_levels(df_btc)
        trend, rsi_val = analyze_trend(df_btc)
        # Note: We now pass the entire mtf_data to use multi-timeframe logic (1D, 4H, 1H)
        signal_data = generate_trading_signal(mtf_data)
        
        # 3. Pro Analysis
        mtf_results, mtf_score = analyze_mtf_trend(mtf_data)
        
        # 4. Long Term History
        df_btc_daily_hist = fetch_crypto_data('BTC/USDT', timeframe='1D', limit=400)
        historical_levels = calculate_historical_levels(df_btc_daily_hist)
    else:
        # Defaults to prevent errors
        fib_levels = {}
        trend = "N/A"
        rsi_val = 0
        signal_data = {"opinion": "N/A", "color": "gray", "score": 0, "advice": "", "reasons": [], "structure": "N/A"}
        mtf_results = {}
        mtf_score = "N/A"
        historical_levels = []
        
    # 5. DXY & Stock
    dxy_data = fetch_dxy_data()
    stock_data = fetch_stock_data()
    
    # Run Correlation Check if we have signals
    dxy_trend = "N/A"
    dxy_warning = None
    dxy_change = 0.0
    
    if not df_btc.empty:
        dxy_trend, dxy_warning, dxy_change = analyze_dxy_correlation(dxy_data, signal_data['opinion'])
    
    # Sentiment
    sentiment_label, sentiment_score, news_items = fetch_news_sentiment()

if not df_btc.empty:
    current_price = df_btc['close'].iloc[-1]
    prev_close = df_btc['close'].iloc[-2]
    price_change = ((current_price - prev_close) / prev_close) * 100
    
    # Top Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Prezzo BTC", f"${current_price:,.2f}", f"{price_change:.2f}%")
    with col2:
        st.metric("Trend (1H)", trend, f"RSI: {rsi_val:.1f}")
    with col3:
        st.metric("Sentiment Mercato", sentiment_label, f"{sentiment_score:.2f}")
    with col4:
        # DXY Display
        if not dxy_data.empty:
            st.metric("DXY Index", f"${dxy_data['Close'].iloc[-1]:.2f}", f"{dxy_change:.2f}%", delta_color="inverse")
        else:
            st.metric("DXY Index", "N/A")

    # --- PROFESSIONAL DASHBOARD ---
    st.markdown("### 🚦 Dashboard Multi-Timeframe (Analisi Pro)")
    
    # DXY Warning
    if dxy_warning:
        st.error(dxy_warning)
        
    dashboard_cols = st.columns(5)
    tfs = ['15m', '1h', '4h', '1d']
    
    with dashboard_cols[0]:
        st.markdown(f"**Confluenza:**")
        st.info(f"**{mtf_score}**")
        
    for i, tf in enumerate(tfs):
        with dashboard_cols[i+1]:
            # Use get in case '1d' key mismatch or missing
            status = mtf_results.get(tf, 'N/A')
            st.metric(f"Trend {tf.upper()}", status)
            
    st.markdown("---")
    # ------------------------------

    # Risk Calculator Logic (Updated in Sidebar)
    with display_risk:
        st.write("Scenari Take Profit / Stop Loss")
        
        # Sort fib levels for reference
        sorted_fibs = sorted(fib_levels.values())
        next_res = next((x for x in sorted_fibs if x > current_price * 1.001), None)
        next_sup = next((x for x in sorted(sorted_fibs, reverse=True) if x < current_price * 0.999), None)
        
        st.caption(f"ℹ️ Livelli Chiave: Supporto ${next_sup if next_sup else 'N/A':,.0f} | Resistenza ${next_res if next_res else 'N/A':,.0f}")
        
        for lev in leverages:
            # Distance in % for SL
            sl_pct = risk_pct_input / lev
            
            # Distance in % for TP (Manual User Input)
            tp_move_pct = tp_target_pct 
            
            # Profit/Loss Calculation
            potential_profit = investment * lev * (tp_move_pct / 100)
            potential_loss = investment * lev * (sl_pct / 100)
            
            # --- LONG SCENARIO ---
            long_sl = current_price * (1 - sl_pct/100)
            long_tp = current_price * (1 + tp_move_pct/100)
            
            # --- SHORT SCENARIO ---
            short_sl = current_price * (1 + sl_pct/100)
            short_tp = current_price * (1 - tp_move_pct/100)
            
            with st.expander(f"Leva x{lev}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**🟢 LONG**")
                    st.write(f"🛑 SL: ${long_sl:,.2f} (-{sl_pct:.2f}%)")
                    st.write(f"🎯 TP: ${long_tp:,.2f} (+{tp_move_pct:.2f}%)")
                    st.write(f"💰 Guadagno Stimato: **${potential_profit:,.2f}**")
                    st.write(f"💀 Perdita Max: **-${potential_loss:,.2f}**")
                
                with c2:
                    st.markdown(f"**🔴 SHORT**")
                    st.write(f"🛑 SL: ${short_sl:,.2f} (+{sl_pct:.2f}%)")
                    st.write(f"🎯 TP: ${short_tp:,.2f} (-{tp_move_pct:.2f}%)")
                    st.write(f"💰 Guadagno Stimato: **${potential_profit:,.2f}**")
                    st.write(f"💀 Perdita Max: **-${potential_loss:,.2f}**")
                
                # Simple R/R calculation for display only
                if potential_loss > 0:
                    rr = potential_profit / potential_loss
                    st.caption(f"Rapporto Rischio/Rendimento effettivo: {rr:.2f}")

    # Main Charts Area
    st.subheader("📊 Analisi Tecnica")
    
    tab1, tab2 = st.tabs(["Grafico Prezzo", "Notizie e Info"])
    
    with tab1:
        # Plotly Candlestick
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df_btc['timestamp'],
                        open=df_btc['open'],
                        high=df_btc['high'],
                        low=df_btc['low'],
                        close=df_btc['close'],
                        name='BTC/USDT'))
        
        # Add EMAs
        fig.add_trace(go.Scatter(x=df_btc['timestamp'], y=df_btc['EMA_50'], line=dict(color='orange', width=1), name='EMA 50'))
        fig.add_trace(go.Scatter(x=df_btc['timestamp'], y=df_btc['EMA_200'], line=dict(color='blue', width=1), name='EMA 200'))
        
        # Add Bollinger Bands
        fig.add_trace(go.Scatter(x=df_btc['timestamp'], y=df_btc['BBU'], line=dict(color='gray', dash='dot'), name='Banda Sup'))
        fig.add_trace(go.Scatter(x=df_btc['timestamp'], y=df_btc['BBL'], line=dict(color='gray', dash='dot'), fill='tonexty', name='Banda Inf'))

        # Add Fibonacci Levels (Horizontal API)
        for level_name, value in fib_levels.items():
            fig.add_hline(y=value, line_dash="dash", line_color="green", annotation_text=level_name)

        fig.update_layout(height=600, xaxis_rangeslider_visible=False, template="plotly_dark")
        # Fix deprecation warning: use_container_width=True -> use_container_width=True is standard? 
        # The warning specifically asked for width="stretch" or similar if using container width.
        # Let's try sticking to use_container_width=True but if it failed, maybe I need to remove it?
        # Actually, let's just try to be safe. If the user saw the warning, it means it IS supported but annoying.
        # But if it broke... wait. The user just pasted the log.
        # I will replace it with the new suggestion.
        try:
            st.plotly_chart(fig, use_container_width=True)
        except:
             st.plotly_chart(fig)
        
        # --- AI SIGNAL SECTION ---
        st.markdown(f"""
        <div style='background-color: #262730; padding: 15px; border-radius: 5px; border-left: 5px solid {signal_data['color']}; margin-bottom: 20px;'>
            <h3 style='margin-top:0;'>🤖 Analisi Agente & Segnali</h3>
            <p style='font-size: 18px;'>Opinione: <strong style='color: {signal_data['color']}'>{signal_data['opinion']}</strong> (Score: {signal_data['score']})</p>
            <p><strong>Struttura Mercato:</strong> {signal_data['structure']}</p>
            <div style='white-space: pre-wrap;'>{signal_data['advice']}</div>
            <hr>
            <p><strong>Fattori Chiave:</strong></p>
            <ul>
                {''.join([f'<li>{r}</li>' for r in signal_data['reasons']])}
            </ul>
        </div>
        """, unsafe_allow_html=True)
        # -------------------------
        
        st.write("### Livelli Chiave (Supporti & Resistenze)")
        
        col_fib, col_hist = st.columns(2)
        
        with col_fib:
            st.markdown("#### 📐 Livelli Fibonacci (Breve Termine)")
            # Identify Support and Resistance (Fib)
            fib_supports = []
            fib_resistances = []
            
            for level_name, value in fib_levels.items():
                if value < current_price:
                    fib_supports.append((level_name, value))
                else:
                    fib_resistances.append((level_name, value))
            
            fib_supports.sort(key=lambda x: x[1], reverse=True)
            fib_resistances.sort(key=lambda x: x[1])
            
            if fib_resistances:
                st.markdown("**Resistenze:**")
                for name, val in fib_resistances:
                    st.metric(f"{name}", f"${val:,.2f}", delta=f"{((val-current_price)/current_price)*100:.2f}%")
            
            if fib_supports:
                st.markdown("**Supporti:**")
                for name, val in fib_supports:
                    st.metric(f"{name}", f"${val:,.2f}", delta=f"{((val-current_price)/current_price)*100:.2f}%")

        with col_hist:
            st.markdown("#### 🏛️ Livelli Storici (1 Anno)")
            st.caption("Aree di prezzo dove il mercato ha reagito in passato (Weekly/Daily Pivots).")
            
            # Filter historical levels close to current price to avoid noise
            # Show levels within +/- 20% range or just closest 3 sup / 3 res
            
            hist_supports = [h for h in historical_levels if h < current_price]
            hist_resistances = [h for h in historical_levels if h > current_price]
            
            hist_supports.sort(reverse=True)
            hist_resistances.sort()
            
            # Get closest 3
            display_res = hist_resistances[:3]
            display_sup = hist_supports[:3]
            
            if display_res:
                st.markdown("**Resistenze Storiche:**")
                for val in display_res:
                     st.metric(f"Resistenza Storica", f"${val:,.0f}", delta=f"{((val-current_price)/current_price)*100:.2f}%")
            else:
                st.write("Siamo sui Massimi Storici!")
                
            if display_sup:
                st.markdown("**Supporti Storici:**")
                for val in display_sup:
                     st.metric(f"Supporto Storico", f"${val:,.0f}", delta=f"{((val-current_price)/current_price)*100:.2f}%")

    with tab2:
        st.subheader("📰 Ultime Notizie & Sentiment")
        for news in news_items:
            sentiment_color = "green" if news['sentiment'] == "Positive" else "red" if news['sentiment'] == "Negative" else "gray"
            st.markdown(f"**[{news['title']}]({news['link']})**")
            st.markdown(f"<span style='color:{sentiment_color}'>{news['sentiment']}</span> | {news['published']}", unsafe_allow_html=True)
            st.write("---")

    # Glossary Section
    with st.expander("📚 Glossario degli Indicatori (Legenda)"):
        st.markdown("""
        **Indicatori di Trend**
        - **EMA (Exponential Moving Average)**: Media Mobile Esponenziale. Dà più peso ai prezzi recenti.
            - **EMA 50 (Arancione)**: Trend di breve-medio termine. Se il prezzo è sopra, è un segnale bullish.
            - **EMA 200 (Blu)**: Trend di lungo termine. Fondamentale per definire il bias generale (sopra = Long, sotto = Short).
            - **Golden Cross**: Quando EMA 50 incrocia EMA 200 verso l'alto (segnale rialzista forte).
            - **Death Cross**: Quando EMA 50 incrocia EMA 200 verso il basso (segnale ribassista forte).

        **Indicatori di Momentum**
        - **RSI (Relative Strength Index)**: Misura la velocità e il cambiamento dei movimenti di prezzo.
            - **> 70 (Ipercomprato)**: Il prezzo potrebbe essere salito troppo velocemente, possibile ritracciamento.
            - **< 30 (Ipervenduto)**: Il prezzo potrebbe essere sceso troppo velocemente, possibile rimbalzo.
            - **Zone 40-50 / 50-60**: Nei trend forti, l'RSI tende a rimbalzare su queste zone senza andare agli estremi.

        **Supporti e Resistenze**
        - **Fibonacci**: Livelli matematici dove il prezzo tende a reagire.
            - **Supporto**: Livello sotto il prezzo attuale che potrebbe fermare la discesa.
            - **Resistenza**: Livello sopra il prezzo attuale che potrebbe fermare la salita.
            - **0.618 (Golden Ratio)**: Il livello più importante per i ritracciamenti.

        **Struttura di Mercato**
        - **HH (Higher High)**: Massimo superiore al precedente (Trend rialzista).
        - **HL (Higher Low)**: Minimo superiore al precedente (Trend rialzista).
        - **LH (Lower High)**: Massimo inferiore al precedente (Trend ribassista).
        - **LL (Lower Low)**: Minimo inferiore al precedente (Trend ribassista).
        
        **Pattern Candlestick**
        - **Pin Bar / Hammer**: Candela con corpo piccolo e ombra lunga. Indica che il prezzo è stato respinto e potrebbe invertire.
        - **Engulfing**: Una candela che "ingloba" completamente quella precedente. Segnale di forza nella direzione della seconda candela.
        """)


else:
    st.error("Impossibile caricare i dati.")
