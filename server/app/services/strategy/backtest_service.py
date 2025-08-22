from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from core.logger import logger

@dataclass
class TradingCost:
    """交易成本模型"""
    commission_rate: float = 0.0003  # 手续费率
    stamp_tax_rate: float = 0.001    # 印花税率（仅卖出）
    transfer_fee_rate: float = 0.00002  # 过户费率
    min_commission: float = 5.0      # 最低手续费
    slippage_rate: float = 0.001     # 滑点率
    market_impact_factor: float = 0.1 # 市场冲击因子

@dataclass
class BacktestConfig:
    """回测配置"""
    initial_capital: float = 1000000
    trading_cost: TradingCost = None
    benchmark_symbol: str = '000300.SH'  # 沪深300作为基准
    risk_free_rate: float = 0.03
    max_position_size: float = 0.2  # 单个股票最大仓位
    rebalance_frequency: str = 'daily'  # 调仓频率
    
    def __post_init__(self):
        if self.trading_cost is None:
            self.trading_cost = TradingCost()

class EnhancedBacktestService:
    """增强版回测服务"""
    
    def __init__(self, config: BacktestConfig = None):
        self.config = config or BacktestConfig()
        self.trades_history = []
        self.portfolio_history = []
        
    def realistic_backtest(self, 
                          price_data: pd.DataFrame, 
                          signals: List[Dict],
                          benchmark_data: pd.DataFrame = None) -> Dict:
        """
        更真实的回测，包含完整的交易成本模型
        """
        logger.info("[Backtest]开始增强版回测")
        
        try:
            # 初始化
            portfolio = self._initialize_portfolio()
            daily_returns = []
            benchmark_returns = []
            
            # 按日期排序信号
            signals_df = pd.DataFrame(signals)
            if 'timestamp' in signals_df.columns:
                signals_df['date'] = pd.to_datetime(signals_df['timestamp']).dt.date
            
            # 遍历每个交易日
            total_days = len(price_data.index)
            signal_days = 0
            trade_days = 0
            
            for i, date in enumerate(price_data.index):
                # 获取当日信号
                daily_signals = self._get_daily_signals(signals_df, date)
                
                # 添加调试信息
                if daily_signals:
                    signal_days += 1
                    logger.info(f"[Backtest]日期 {date.date()}: 找到 {len(daily_signals)} 个信号")
                    for j, signal in enumerate(daily_signals):
                        logger.info(f"[Backtest]  信号{j+1}: {signal['action']} {signal['symbol']} 强度:{signal['strength']}")
                
                # 执行交易（考虑交易成本）
                trades = self._execute_trades_with_costs(daily_signals, price_data.loc[date], portfolio)
                
                # 添加交易调试信息
                if trades:
                    trade_days += 1
                    logger.info(f"[Backtest]日期 {date.date()}: 执行了 {len(trades)} 笔交易")
                    for j, trade in enumerate(trades):
                        logger.info(f"[Backtest]  交易{j+1}: {trade['action']} {trade['symbol']} {trade['shares']}股 @{trade['price']}")
                elif daily_signals:
                    logger.warning(f"[Backtest]日期 {date.date()}: 有信号但未执行交易")
                    logger.warning(f"[Backtest]  当前现金: {portfolio['cash']:.2f}")
                    logger.warning(f"[Backtest]  当前持仓: {list(portfolio['positions'].keys())}")
                
                # 更新投资组合
                portfolio = self._update_portfolio(portfolio, price_data.loc[date], trades)
                
                # 记录组合价值
                portfolio_value = self._calculate_portfolio_value(portfolio, price_data.loc[date])
                self.portfolio_history.append({
                    'date': date,
                    'value': portfolio_value,
                    'cash': portfolio['cash'],
                    'positions': portfolio['positions'].copy()
                })
                
                # 每50天打印一次进度
                if (i + 1) % 50 == 0 or i == total_days - 1:
                    logger.info(f"[Backtest]进度: {i+1}/{total_days} 天, 信号天数: {signal_days}, 交易天数: {trade_days}")
                
                # 计算日收益率
                if len(self.portfolio_history) > 1:
                    prev_value = self.portfolio_history[-2]['value']
                    daily_return = (portfolio_value - prev_value) / prev_value
                    daily_returns.append(daily_return)
                
                # 计算基准收益率
                if benchmark_data is not None and date in benchmark_data.index:
                    if len(benchmark_returns) == 0:
                        benchmark_returns.append(0)
                    else:
                        prev_benchmark = benchmark_data.loc[benchmark_data.index[len(benchmark_returns)-1], 'close']
                        curr_benchmark = benchmark_data.loc[date, 'close']
                        benchmark_return = (curr_benchmark - prev_benchmark) / prev_benchmark
                        benchmark_returns.append(benchmark_return)
            
            # 计算性能指标
            performance_metrics = self._calculate_enhanced_metrics(
                daily_returns, benchmark_returns, self.portfolio_history
            )
            
            return {
                'status': 'success',
                'data': {
                    'portfolio_history': self.portfolio_history,
                    'trades_history': self.trades_history,
                    'performance_metrics': performance_metrics,
                    'config': self.config.__dict__
                },
                'message': f'增强版回测完成，共{len(self.trades_history)}笔交易'
            }
            
        except Exception as e:
            logger.error(f"[Backtest]增强版回测失败: {e}")
            return {'status': 'error', 'message': f'回测失败: {e}'}
    
    def _calculate_trading_costs(self, trade_amount: float, price: float, trade_type: str) -> float:
        """
        计算交易成本
        """
        cost = self.config.trading_cost
        
        # 手续费
        commission = max(trade_amount * cost.commission_rate, cost.min_commission)
        
        # 印花税（仅卖出）
        stamp_tax = trade_amount * cost.stamp_tax_rate if trade_type == 'sell' else 0
        
        # 过户费
        transfer_fee = trade_amount * cost.transfer_fee_rate
        
        # 滑点成本
        slippage = trade_amount * cost.slippage_rate
        
        # 市场冲击成本（大额交易）
        market_impact = trade_amount * cost.market_impact_factor * 0.0001 if trade_amount > 100000 else 0
        
        total_cost = commission + stamp_tax + transfer_fee + slippage + market_impact
        
        return total_cost
    
    def _calculate_enhanced_metrics(self, returns: List[float], 
                                  benchmark_returns: List[float],
                                  portfolio_history: List[Dict]) -> Dict:
        """
        计算增强的性能指标
        """
        if not returns:
            return {}
        
        returns_series = pd.Series(returns)
        
        # 基础指标
        total_return = (portfolio_history[-1]['value'] / portfolio_history[0]['value']) - 1
        annual_return = (1 + total_return) ** (252 / len(returns)) - 1
        volatility = returns_series.std() * np.sqrt(252)
        sharpe_ratio = (annual_return - self.config.risk_free_rate) / volatility if volatility > 0 else 0
        
        # 最大回撤
        portfolio_values = [p['value'] for p in portfolio_history]
        peak = np.maximum.accumulate(portfolio_values)
        drawdown = (np.array(portfolio_values) - peak) / peak
        max_drawdown = np.min(drawdown)
        
        # 与基准对比
        benchmark_metrics = {}
        if benchmark_returns:
            benchmark_series = pd.Series(benchmark_returns)
            benchmark_total_return = (1 + benchmark_series).prod() - 1
            benchmark_volatility = benchmark_series.std() * np.sqrt(252)
            
            # 计算Alpha和Beta
            if len(returns) == len(benchmark_returns):
                covariance = np.cov(returns, benchmark_returns)[0][1]
                beta = covariance / (benchmark_volatility / np.sqrt(252)) ** 2 if benchmark_volatility > 0 else 0
                alpha = annual_return - (self.config.risk_free_rate + beta * (benchmark_total_return * 252 / len(benchmark_returns) - self.config.risk_free_rate))
                
                benchmark_metrics = {
                    'benchmark_return': benchmark_total_return,
                    'benchmark_volatility': benchmark_volatility,
                    'alpha': alpha,
                    'beta': beta,
                    'excess_return': total_return - benchmark_total_return
                }
        
        # 交易统计
        trade_stats = self._calculate_trade_statistics()
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'benchmark_metrics': benchmark_metrics,
            'trade_statistics': trade_stats
        }
    
    def _calculate_trade_statistics(self) -> Dict:
        """
        计算交易统计信息
        """
        if not self.trades_history:
            return {}
        
        trades_df = pd.DataFrame(self.trades_history)
        
        # 盈亏统计
        profitable_trades = trades_df[trades_df['pnl'] > 0]
        losing_trades = trades_df[trades_df['pnl'] < 0]
        
        win_rate = len(profitable_trades) / len(trades_df) if len(trades_df) > 0 else 0
        avg_win = profitable_trades['pnl'].mean() if len(profitable_trades) > 0 else 0
        avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        # 交易成本统计
        total_costs = trades_df['trading_cost'].sum() if 'trading_cost' in trades_df.columns else 0
        
        return {
            'total_trades': len(trades_df),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'total_trading_costs': total_costs
        }
    # 在EnhancedBacktestService类中添加以下缺失的方法

    def _get_daily_signals(self, signals_df: pd.DataFrame, date) -> List[Dict]:
        """
        获取指定日期的信号
        """
        if signals_df.empty:
            return []
        
        # 统一日期格式处理
        if hasattr(date, 'date'):
            target_date = date.date()
        elif hasattr(date, 'strftime'):
            target_date = date.date() if hasattr(date, 'date') else date
        else:
            target_date = pd.to_datetime(date).date()
        
        # 筛选当日信号
        if 'date' in signals_df.columns:
            # 确保date列是日期类型
            signals_df['date'] = pd.to_datetime(signals_df['date']).dt.date
            daily_signals = signals_df[signals_df['date'] == target_date]
        elif 'timestamp' in signals_df.columns:
            # 确保timestamp列是日期时间类型
            signals_df['timestamp'] = pd.to_datetime(signals_df['timestamp'])
            daily_signals = signals_df[signals_df['timestamp'].dt.date == target_date]
        else:
            return []
        
        return daily_signals.to_dict('records')
    def _execute_trades_with_costs(self, signals: List[Dict], price_data: pd.Series, portfolio: Dict) -> List[Dict]:
        """
        执行交易并计算交易成本
        """
        trades = []
        
        # 添加调试信息
        if signals:
            logger.debug(f"[Trade]处理 {len(signals)} 个信号, 当前现金: {portfolio['cash']:.2f}")
            logger.debug(f"[Trade]价格数据: {dict(price_data)}")
        
        for signal in signals:
            if signal.get('action') in ['buy', 'sell']:
                symbol = signal.get('symbol', '000001.SH')
                action = signal['action']
                strength = signal.get('strength', 0.5)
                
                logger.debug(f"[Trade]处理信号: {action} {symbol} 强度:{strength}")
                
                # 获取当前价格
                current_price = price_data.get('close', price_data.get('收盘价', 0))
                if current_price <= 0:
                    logger.warning(f"[Trade]无效价格 {current_price} for {symbol}")
                    continue
                
                logger.debug(f"[Trade]当前价格: {current_price}")
                
                # 计算交易数量
                if action == 'buy':
                    # 根据信号强度和可用资金计算买入数量
                    available_cash = portfolio['cash']
                    position_value = available_cash * strength * self.config.max_position_size
                    shares = int(position_value / current_price / 100) * 100  # 按手交易
                    
                    if shares > 0:
                        trade_amount = shares * current_price
                        trading_cost = self._calculate_trading_costs(trade_amount, current_price, 'buy')
                        
                        if available_cash >= trade_amount + trading_cost:
                            trade = {
                                'symbol': symbol,
                                'action': 'buy',
                                'shares': shares,
                                'price': current_price,
                                'amount': trade_amount,
                                'trading_cost': trading_cost,
                                'timestamp': price_data.name,
                                'signal_strength': strength
                            }
                            trades.append(trade)
                
                elif action == 'sell':
                    # 卖出现有持仓
                    if symbol in portfolio['positions']:
                        current_shares = portfolio['positions'][symbol]['shares']
                        sell_shares = int(current_shares * strength)
                        
                        if sell_shares > 0:
                            trade_amount = sell_shares * current_price
                            trading_cost = self._calculate_trading_costs(trade_amount, current_price, 'sell')
                            
                            trade = {
                                'symbol': symbol,
                                'action': 'sell',
                                'shares': sell_shares,
                                'price': current_price,
                                'amount': trade_amount,
                                'trading_cost': trading_cost,
                                'timestamp': price_data.name,
                                'signal_strength': strength
                            }
                            trades.append(trade)
        
        return trades

    def _update_portfolio(self, portfolio: Dict, price_data: pd.Series, trades: List[Dict]) -> Dict:
        """
        根据交易更新投资组合
        """
        updated_portfolio = portfolio.copy()
        updated_portfolio['positions'] = portfolio['positions'].copy()
        
        for trade in trades:
            symbol = trade['symbol']
            action = trade['action']
            shares = trade['shares']
            price = trade['price']
            trading_cost = trade['trading_cost']
            
            if action == 'buy':
                # 更新现金
                updated_portfolio['cash'] -= (trade['amount'] + trading_cost)
                
                # 更新持仓
                if symbol in updated_portfolio['positions']:
                    old_shares = updated_portfolio['positions'][symbol]['shares']
                    old_avg_price = updated_portfolio['positions'][symbol]['avg_price']
                    new_shares = old_shares + shares
                    new_avg_price = (old_shares * old_avg_price + shares * price) / new_shares
                    updated_portfolio['positions'][symbol] = {
                        'shares': new_shares,
                        'avg_price': new_avg_price
                    }
                else:
                    updated_portfolio['positions'][symbol] = {
                        'shares': shares,
                        'avg_price': price
                    }
            
            elif action == 'sell':
                # 更新现金
                updated_portfolio['cash'] += (trade['amount'] - trading_cost)
                
                # 更新持仓
                if symbol in updated_portfolio['positions']:
                    updated_portfolio['positions'][symbol]['shares'] -= shares
                    
                    # 如果持仓为0，删除该持仓
                    if updated_portfolio['positions'][symbol]['shares'] <= 0:
                        del updated_portfolio['positions'][symbol]
            
            # 记录交易历史
            trade_record = trade.copy()
            if action == 'sell' and symbol in portfolio['positions']:
                # 计算盈亏
                avg_cost = portfolio['positions'][symbol]['avg_price']
                trade_record['pnl'] = (price - avg_cost) * shares - trading_cost
            else:
                trade_record['pnl'] = -trading_cost  # 买入时的成本
            
            self.trades_history.append(trade_record)
        
        return updated_portfolio

    def _calculate_portfolio_value(self, portfolio: Dict, price_data: pd.Series) -> float:
        """
        计算投资组合总价值
        """
        total_value = portfolio['cash']
        current_price = price_data.get('close', price_data.get('收盘价', 0))
        
        # 计算持仓价值
        for symbol, position in portfolio['positions'].items():
            # 这里简化处理，假设所有持仓都是同一只股票
            position_value = position['shares'] * current_price
            total_value += position_value
        
        return total_value
    # 其他辅助方法...
    def _initialize_portfolio(self) -> Dict:
        return {
            'cash': self.config.initial_capital,
            'positions': {},  # {symbol: {'shares': int, 'avg_price': float}}
            'total_value': self.config.initial_capital
        }