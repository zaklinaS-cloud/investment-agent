import streamlit as st
import math, random
from agent import InvestmentAgent

st.set_page_config(page_title='Investment Agent', page_icon='📈', layout='centered')
st.markdown('''<style>
.block-container{padding-top:1.2rem;max-width:760px}.stButton button{width:100%;height:3.2rem;font-weight:700}
[data-testid="stMetricValue"]{font-size:1.7rem}
</style>''', unsafe_allow_html=True)

st.title('📈 Investment Agent')
st.caption('Wersja treningowa • wirtualny portfel • bez realnych zleceń')

if 'agent' not in st.session_state:
    st.session_state.agent = InvestmentAgent(10000.0)
    st.session_state.histories = {}
    st.session_state.day = 0
    st.session_state.last_prices = {}

agent=st.session_state.agent

def make_market(days=260):
    import yfinance as yf

    tickers = {
        "SPY": "SPY",
        "AAPL": "AAPL",
        "MSFT": "MSFT",
        "BTC/USD": "BTC-USD",
        "ETH/USD": "ETH-USD",
    }

    data = {}

    for symbol, ticker in tickers.items():
        df = yf.download(
            ticker,
            period="1y",
            interval="1d",
            auto_adjust=True,
            progress=False
        )

        if not df.empty:
            prices = df["Close"].dropna().tail(days)
            data[symbol] = [float(x) for x in prices.to_numpy().flatten()]

    return data

if not st.session_state.histories:
    st.session_state.histories=make_market()

prices={s:v[-1] for s,v in st.session_state.histories.items()}
eq=agent.equity(prices)
pnl=eq-agent.initial
c1,c2=st.columns(2)
c1.metric('Portfel', f'€{eq:,.2f}', f'{pnl:+,.2f} €')
c2.metric('Gotówka', f'€{agent.cash:,.2f}')

st.progress(min(1.0, max(0.0, agent.exposure(prices))), text=f'Ekspozycja portfela: {agent.exposure(prices)*100:.1f}%')

st.subheader('Sterowanie')
if st.button('▶️ Uruchom analizę rynku'):
    result=agent.step(st.session_state.histories)
    st.session_state.day += 1
    st.success(f"Analiza zakończona. Portfel: €{result['equity']:,.2f} • Pozycje: {result['positions']}")
    st.rerun()

if st.button('🔄 Resetuj symulację'):
    st.session_state.agent=InvestmentAgent(10000.0)
    st.session_state.histories=make_market()
    st.session_state.day=0
    st.rerun()

st.subheader('Strategie')
for name,desc in [('Day Trading','krótkoterminowe momentum'),('Swing','trend dni–tygodnie'),('Long Term','trend długoterminowy')]:
    st.write(f'**{name}** — {desc}')

st.subheader('Otwarte pozycje')
if not agent.positions:
    st.info('Brak otwartych pozycji.')
else:
    for p in agent.positions.values():
        px=prices.get(p.symbol,p.entry); value=p.qty*px; pl=p.qty*(px-p.entry)
        st.write(f'**{p.symbol}** · {p.strategy.upper()} · wartość €{value:,.2f} · P/L {pl:+,.2f} €')
        st.caption(f'Wejście {p.entry:.2f} • Stop {p.stop_loss:.2f} • Take profit {p.take_profit:.2f}')

st.subheader('Dziennik decyzji')
if not agent.log:
    st.caption('Agent nie wykonał jeszcze żadnej decyzji transakcyjnej.')
else:
    for item in reversed(agent.log[-20:]):
        st.json(item, expanded=False)

st.divider()
st.caption('⚠️ To środowisko symulacyjne. Wyniki nie gwarantują przyszłych zysków. Dane demonstracyjne nie są bieżącymi notowaniami.')
