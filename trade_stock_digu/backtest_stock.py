from vnpy.app.cta_strategy.backtesting import BacktestingEngine, OptimizationSetting
# from vnpy.app.cta_strategy.strategies.atr_rsi_strategy import AtrRsiStrategy
from strategy.strategy_zz500 import ZZ500Strategy
from datetime import datetime

engine = BacktestingEngine()
engine.set_parameters(
    vt_symbol="000905_SH.SSE",
    interval="d",
    start=datetime(2013, 1, 1),
    end=datetime(2019, 12, 31),
    rate=0.1/10000,
    slippage=0.1,
    size=300,
    pricetick=0.2,
    capital=1_000_000,
)
engine.add_strategy(ZZ500Strategy, {})

engine.load_data()
engine.run_backtesting()
print(ZZ500Strategy.c1)
print(ZZ500Strategy.c2)
print(ZZ500Strategy.c3)
print(ZZ500Strategy.c4)
print(ZZ500Strategy.c5)
print(ZZ500Strategy.c6)
df = engine.calculate_result()
engine.calculate_statistics()
engine.show_chart()

setting = OptimizationSetting()
setting.set_target("sharpe_ratio")
setting.add_parameter("atr_length", 3, 39, 1)
setting.add_parameter("atr_ma_length", 10, 30, 1)

# engine.run_ga_optimization(setting)
