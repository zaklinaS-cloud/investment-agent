# Investment Agent v1

Prototype for research and paper trading only. No live-order code is included.

## Modules
- DayMomentum: short-horizon momentum + moving-average confirmation
- SwingTrend: medium trend/momentum
- LongTrend: long trend/momentum (fundamental scoring planned for v2)
- RiskManager: position sizing, exposure cap, portfolio drawdown kill-switch
- InvestmentAgent: portfolio, entries/exits, audit log

## Default safety limits
- Starting virtual capital: €10,000 equivalent
- Risk budget per trade: 0.5% of equity
- Max single position: 10% of equity
- Max gross exposure: 70%
- New trades disabled after 12% portfolio drawdown

These are research defaults, not claims of optimal settings.

## Next validation
1. Import historical stock/crypto bars.
2. Add fees, spread and slippage.
3. Walk-forward / out-of-sample testing.
4. Compare Day / Swing / Long separately and combined.
5. Only then connect to a paper-trading API.
