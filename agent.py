from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List
import json, math, statistics

class Action(str, Enum):
    BUY='BUY'; SELL='SELL'; HOLD='HOLD'

@dataclass
class Signal:
    symbol: str
    strategy: str
    action: Action
    confidence: float
    price: float
    stop_loss: float
    take_profit: float
    reason: str

@dataclass
class Position:
    symbol: str
    strategy: str
    qty: float
    entry: float
    stop_loss: float
    take_profit: float

class RiskManager:
    def __init__(self, risk_per_trade=0.005, max_position_pct=0.10,
                 max_total_exposure=0.70, max_drawdown=0.12):
        self.risk_per_trade = risk_per_trade
        self.max_position_pct = max_position_pct
        self.max_total_exposure = max_total_exposure
        self.max_drawdown = max_drawdown

    def size(self, equity, price, stop_loss):
        risk_per_unit = abs(price - stop_loss)
        if risk_per_unit <= 0: return 0.0
        by_risk = equity * self.risk_per_trade / risk_per_unit
        by_position = equity * self.max_position_pct / price
        return max(0.0, min(by_risk, by_position))

    def allow_new_trade(self, equity, peak_equity, exposure):
        dd = 1 - equity / peak_equity if peak_equity else 0
        return dd < self.max_drawdown and exposure < self.max_total_exposure

class Strategy:
    name='base'
    def signal(self, symbol, bars): raise NotImplementedError

class DayMomentum(Strategy):
    name='day'
    def signal(self, symbol, bars):
        if len(bars) < 21: return None
        p=bars[-1]; ma5=sum(bars[-5:])/5; ma20=sum(bars[-20:])/20
        mom=p/bars[-6]-1
        if ma5>ma20 and mom>0.003:
            return Signal(symbol,self.name,Action.BUY,min(.95,.55+mom*10),p,p*.985,p*1.03,'short momentum + MA confirmation')
        return None

class SwingTrend(Strategy):
    name='swing'
    def signal(self, symbol, bars):
        if len(bars) < 51: return None
        p=bars[-1]; ma20=sum(bars[-20:])/20; ma50=sum(bars[-50:])/50
        mom20=p/bars[-21]-1
        if p>ma20>ma50 and mom20>0.02:
            return Signal(symbol,self.name,Action.BUY,min(.95,.55+mom20*2),p,p*.94,p*1.12,'20/50 trend + 20-period momentum')
        return None

class LongTrend(Strategy):
    name='long'
    def signal(self, symbol, bars):
        if len(bars) < 201: return None
        p=bars[-1]; ma50=sum(bars[-50:])/50; ma200=sum(bars[-200:])/200
        mom=p/bars[-126]-1 if len(bars)>=126 else 0
        if p>ma50>ma200 and mom>0:
            return Signal(symbol,self.name,Action.BUY,min(.90,.55+mom),p,p*.85,p*1.30,'long trend + 6m momentum; fundamentals added in v2')
        return None

class InvestmentAgent:
    def __init__(self, cash=10000.0):
        self.cash=cash; self.initial=cash; self.peak=cash
        self.positions: Dict[str,Position]={}; self.log=[]
        self.risk=RiskManager(); self.strategies=[DayMomentum(),SwingTrend(),LongTrend()]

    def equity(self, prices):
        return self.cash + sum(p.qty*prices.get(p.symbol,p.entry) for p in self.positions.values())

    def exposure(self, prices):
        eq=self.equity(prices)
        gross=sum(abs(p.qty*prices.get(p.symbol,p.entry)) for p in self.positions.values())
        return gross/eq if eq else 1

    def step(self, histories: Dict[str,List[float]]):
        prices={s:b[-1] for s,b in histories.items() if b}
        eq=self.equity(prices); self.peak=max(self.peak,eq)
        # exits first
        for key,p in list(self.positions.items()):
            px=prices.get(p.symbol)
            if px is not None and (px<=p.stop_loss or px>=p.take_profit):
                self.cash += p.qty*px
                self.log.append({'event':'EXIT','symbol':p.symbol,'strategy':p.strategy,'price':px,'qty':p.qty})
                del self.positions[key]
        eq=self.equity(prices); self.peak=max(self.peak,eq)
        for symbol, bars in histories.items():
    print("DEBUG SYMBOL:", symbol, "OPEN:", [(p.symbol, p.strategy) for p in self.positions.values()])

    # Nie otwieraj kolejnej pozycji na tym samym instrumencie
    if any(p.symbol == symbol for p in self.positions.values()):
        continue

    # Zbierz sygnały ze wszystkich strategii
    signals = []

    for strat in self.strategies:
        sig = strat.signal(symbol, bars)

        if sig and sig.confidence >= 0.60:
            signals.append(sig)

    # Jeśli żadna strategia nie daje sygnału, przejdź dalej
    if not signals:
        continue

    # Wybierz tylko strategię z najwyższym confidence
    sig = max(signals, key=lambda s: s.confidence)

    if not self.risk.allow_new_trade(
        eq, self.peak, self.exposure(prices)
    ):
        continue

    qty = self.risk.size(
        eq, sig.price, sig.stop_loss
    )

    cost = qty * sig.price

    if qty > 0 and cost <= self.cash:
        self.cash -= cost

        key = f'{sig.strategy}:{symbol}'

        self.positions[key] = Position(
            symbol,
            sig.strategy,
            qty,
            sig.price,
            sig.stop_loss,
            sig.take_profit
        )

        self.log.append({
            'event': 'ENTRY',
            **asdict(sig),
            'action': sig.action.value,
            'qty': qty
        })
    return {'equity':self.equity(prices),'cash':self.cash,'positions':len(self.positions)}

if __name__=='__main__':
    print('Investment Agent v1 core ready. Feed historical price arrays into InvestmentAgent.step().')
