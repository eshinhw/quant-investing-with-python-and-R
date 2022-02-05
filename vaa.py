"""
Vigilant Asset Allocation (VAA) Implementation Source Codes
"""

import numpy as np
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import fmp.fmp_prices as FMP_PRICES

## Portfolio Assets

OFFENSIVE_ASSETS = ['SPY', 'VEA', 'VWO', 'AGG']
DEFENSIVE_ASSETS = ['SHY', 'IEF', 'LQD']
MOMENTUM_PERIODS = [1,3,6,12]
MOMENTUM_WEIGHTS = np.array([12,4,2,1])


## Offensive assets momentum

offensive_momentum_data = {'1M': [], '3M': [], '6M': [], '12M': []}
offensive_mom = []
for symbol in OFFENSIVE_ASSETS:
    for period in MOMENTUM_PERIODS:        
        offensive_momentum_data[str(period)+'M'].append(FMP_PRICES.historical_monthly_momentum(symbol,period))
offensive_momentum = pd.DataFrame(offensive_momentum_data, index=OFFENSIVE_ASSETS)
offensive_momentum['Score'] = offensive_momentum.dot(MOMENTUM_WEIGHTS)


## Defensive Assets Momentum

defensive_momentum_data = {'1M': [], '3M': [], '6M': [], '12M': []}

for symbol in DEFENSIVE_ASSETS:
    for period in MOMENTUM_PERIODS:        
        defensive_momentum_data[str(period)+'M'].append(FMP_PRICES.historical_monthly_momentum(symbol,period))

defensive_momentum = pd.DataFrame(defensive_momentum_data, index=DEFENSIVE_ASSETS)
defensive_momentum['Score'] = defensive_momentum.dot(MOMENTUM_WEIGHTS)


print(defensive_momentum)

## Investment decision based on strategy algorithm

if (offensive_momentum['Score'] < 0).any():
    if (defensive_momentum['Score'] < 0).any():
        print('hold cash')
    else:
        first = defensive_momentum.sort_values(by='Score', ascending=False).index[0]
        print('invest in ' + first)
else:
    first = offensive_momentum.sort_values(by='Score', ascending=False).index[0]
    print('invest in ' + first)



"""
## Backtesting
### VAA (Original Version: Offensive + Defensive)
#### Trading Logics

def vaa_returns(x):
    m1 = x / x.shift(1) - 1
    m3 = x / x.shift(3) - 1
    m6 = x / x.shift(6) - 1
    m12 = x / x.shift(12) - 1
    return (12 * m1 + 4 * m3 + 2 * m6 + 1 * m12) / 4

    
vaa_assets = ['SPY', 'VEA', 'VWO', 'AGG', 'SHY', 'IEF', 'LQD']
vaa_monthly_prices = pd.DataFrame()

for asset in vaa_assets:
    vaa_monthly_prices[asset] = fmp.get_monthly_prices(asset)[asset]
vaa_monthly_prices.head(10)
vaa_monthly_mom = vaa_monthly_prices.copy()
vaa_monthly_mom = vaa_monthly_mom.apply(vaa_returns, axis=0)
vaa_monthly_mom.dropna(inplace=True)
for date in vaa_monthly_mom.index:
    if (vaa_monthly_mom.loc[date,['SPY', 'VEA', 'VWO', 'AGG']] < 0).any():
        # check defensive assets
        vaa_monthly_mom.loc[date, 'SPY'] = 0
        vaa_monthly_mom.loc[date, 'VEA'] = 0
        vaa_monthly_mom.loc[date, 'VWO'] = 0
        vaa_monthly_mom.loc[date, 'AGG'] = 0
        if (vaa_monthly_mom.loc[date,['SHY', 'IEF', 'LQD']] < 0).any():
            # hold cash
            vaa_monthly_mom.loc[date, 'SHY'] = 0
            vaa_monthly_mom.loc[date, 'IEF'] = 0
            vaa_monthly_mom.loc[date, 'LQD'] = 0
    else:
        # invest offensive asset
        vaa_monthly_mom.loc[date, 'SHY'] = 0
        vaa_monthly_mom.loc[date, 'IEF'] = 0
        vaa_monthly_mom.loc[date, 'LQD'] = 0
vaa_monthly_mom
mom_rank = vaa_monthly_mom.rank(axis=1, ascending=False)
for symbol in mom_rank.columns:
    mom_rank[symbol] = np.where(mom_rank[symbol] == 1, 1, 0)
mom_rank
# we have to shift the returns upward by one to align with momentum signal above.
vaa_monthly_rets = vaa_monthly_prices.pct_change()
vaa_monthly_rets.dropna(inplace=True)
vaa_monthly_rets = vaa_monthly_rets[mom_rank.index[0]:].shift(-1)
vaa_monthly_rets
vaa_port = np.multiply(mom_rank, vaa_monthly_rets)
vaa_port_returns = vaa_port.sum(axis=1)
vaa_port_cum_returns = np.exp(np.log1p(vaa_port_returns).cumsum())[:-1]




### 60/40 Benchmark
assets = ['BND', 'SPY']

sixtyForty = pd.DataFrame()

for symbol in assets:
    sixtyForty[symbol] = fmp.get_monthly_prices(symbol)[symbol]
sixtyForty_returns = sixtyForty.pct_change()
sixtyForty_returns = sixtyForty_returns[mom_rank.index[0]:].shift(-1)
sixtyForty_weights = np.array([0.4, 0.6])
sixtyForty_returns['port'] = sixtyForty_returns.dot(sixtyForty_weights)
sixtyForty_returns.tail()
sixtyForty_cum_returns = np.exp(np.log1p(sixtyForty_returns['port']).cumsum())[:-1]
sixtyForty_cum_returns.tail()

### SPY (S&P 500)
benchmark_prices = fmp.get_monthly_prices('SPY')
benchmark_returns = benchmark_prices.pct_change()
benchmark_returns = benchmark_returns[mom_rank.index[0]:].shift(-1)
benchmark_cum_returns = np.exp(np.log1p(benchmark_returns).cumsum())[:-1]
benchmark_cum_returns.tail()
combined_df = pd.DataFrame()
combined_df['VAA/Original'] = vaa_port_cum_returns
combined_df['VAA/Relative_Offensive'] = offensive_port_cum_returns
combined_df['VAA/Dual_Offensive'] = dual_offensive_port_cum_returns
combined_df['60/40'] = sixtyForty_cum_returns
combined_df['SPY'] = benchmark_cum_returns
combined_df.iloc[0] = 1
combined_df.index = pd.to_datetime(combined_df.index)
combined_df
stats_summary = pd.DataFrame(columns = ['Portfolio', 'CAGR (%)', 'MDD (%)', 'CAGR/MDD'])
beginning_month = combined_df.index[0].year

for col in combined_df.columns:
    # compute CAGR
    first_value = combined_df[col][0]
    last_value = combined_df[col][-1]  
    years = len(combined_df[col].index)/12    
    cagr = (last_value/first_value)**(1/years) - 1
    
    # compute MDD
    cumulative_returns = combined_df[col]
    previous_peaks = cumulative_returns.cummax()
    drawdown = (cumulative_returns - previous_peaks) / previous_peaks
    portfolio_mdd = drawdown.min()
    
    # save CAGR and MDD for each portfolio    
    stats_summary = stats_summary.append({'Portfolio': col,
                                         'CAGR (%)': cagr * 100,
                                         'MDD (%)': portfolio_mdd * 100,
                                         'CAGR/MDD': abs(cagr / portfolio_mdd).round(2)}, ignore_index=True) 
stats_summary.set_index('Portfolio', inplace=True)
stats_summary.sort_values('CAGR/MDD', ascending=False, inplace=True)
stats_summary
### Backtesting Performance Comparison (All Portfolios)
plt.figure(figsize=(15,10))
plt.plot(combined_df)
plt.legend(combined_df.columns)
plt.xlabel('Date')
plt.ylabel('Returns')
plt.title('Portfolio Performance Comparison')
### Backtesting Performance Comparison (Original VAA, 60/40, SPY)
sub_df = combined_df[['VAA/Original', '60/40', 'SPY']]
plt.figure(figsize=(15,10))
plt.plot(sub_df)
plt.legend(sub_df.columns)
plt.xlabel('Date')
plt.ylabel('Returns')
plt.title('Portfolio Performance Comparison')



"""
# ===============================================================================================
"""
### VAA (Modified: Relative Momentum Offensive Only)
#### Trading Logics


offensive_monthly_mom = offensive_monthly.copy()
offensive_monthly_mom = offensive_monthly_mom.apply(vaa_returns, axis=0)
offensive_monthly_mom.dropna(inplace=True)

# print(offensive_monthly_mom)

off_mom_rank = offensive_monthly_mom.rank(axis=1, ascending=False)
for symbol in off_mom_rank.columns:
    off_mom_rank[symbol] = np.where(off_mom_rank[symbol] < 2, 1, 0)
    
print(off_mom_rank)
    
offensive_monthly_rets = offensive_monthly.pct_change()
offensive_monthly_rets.dropna(inplace=True)
offensive_monthly_rets = offensive_monthly_rets[off_mom_rank.index[0]:].shift(-1)

offensive_port = np.multiply(off_mom_rank, offensive_monthly_rets)
offensive_port_returns = offensive_port.sum(axis=1)
offensive_port_cum_returns = np.exp(np.log1p(offensive_port_returns).cumsum())[:-1]
offensive_port_cum_returns.tail()


### VAA (Modified: Dual momentum Offensive Only)
#### Trading Logics

dual_offensive_monthly_mom = offensive_monthly.copy()
dual_offensive_monthly_mom = dual_offensive_monthly_mom.apply(vaa_returns, axis=0)
dual_offensive_monthly_mom.dropna(inplace=True)

print(dual_offensive_monthly_mom)

for date in dual_offensive_monthly_mom.index:
    if (dual_offensive_monthly_mom.loc[date] < 0).any():
        # print(date, ' negative')
        # check defensive assets
        dual_offensive_monthly_mom.loc[date, 'SPY'] = 0
        dual_offensive_monthly_mom.loc[date, 'VEA'] = 0
        dual_offensive_monthly_mom.loc[date, 'VWO'] = 0
        dual_offensive_monthly_mom.loc[date, 'AGG'] = 0

print(dual_offensive_monthly_mom)

dual_off_mom_rank = dual_offensive_monthly_mom.rank(axis=1, ascending=False)

print(dual_off_mom_rank)
for symbol in dual_off_mom_rank.columns:
    dual_off_mom_rank[symbol] = np.where(dual_off_mom_rank[symbol] == 1, 1, 0)
    
dual_offensive_monthly_rets = offensive_monthly.pct_change()
dual_offensive_monthly_rets.dropna(inplace=True)
dual_offensive_monthly_rets = dual_offensive_monthly_rets[dual_off_mom_rank.index[0]:].shift(-1)

dual_offensive_port = np.multiply(dual_off_mom_rank, dual_offensive_monthly_rets)
dual_offensive_port_returns = dual_offensive_port.sum(axis=1)
dual_offensive_port_cum_returns = np.exp(np.log1p(dual_offensive_port_returns).cumsum())[:-1]
dual_offensive_port_cum_returns

"""