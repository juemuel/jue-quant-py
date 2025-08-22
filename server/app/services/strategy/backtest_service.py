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
        基于交易配对计算，而不是单独的买入或卖出
        """
        # 添加调试信息
        print(f"\n=== 调试信息 ===")
        print(f"总交易记录数: {len(self.trades_history)}")
        if self.trades_history:
            # 打印前几条交易记录
            print("\n前5条交易记录:")
            for i, trade in enumerate(self.trades_history[:5]):
                print(f"  {i+1}: {trade}")
            
            # 统计买卖交易数量
            buy_trades = [t for t in self.trades_history if t.get('action') == 'buy']
            sell_trades = [t for t in self.trades_history if t.get('action') == 'sell']
            print(f"\n买入交易数: {len(buy_trades)}")
            print(f"卖出交易数: {len(sell_trades)}")
        if not self.trades_history:
            return {
                'total_trades': 0,
                'completed_pairs': 0,
                'profitable_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'total_trading_costs': 0
            }
        
        # 获取完整的买卖配对
        trade_pairs = self._get_trade_pairs()
        
        if not trade_pairs:
            # 如果没有完成的配对，返回基础统计
            trades_df = pd.DataFrame(self.trades_history)
            total_costs = trades_df['trading_cost'].sum() if 'trading_cost' in trades_df.columns else 0
            
            return {
                'total_trades': len(self.trades_history),
                'completed_pairs': 0,
                'profitable_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'total_trading_costs': total_costs
            }
        
        # 基于配对计算统计 - 使用return_pct而不是net_pnl来判断盈亏
        profitable_pairs = [p for p in trade_pairs if p['return_pct'] > 0]
        losing_pairs = [p for p in trade_pairs if p['return_pct'] < 0]

        total_pairs = len(trade_pairs)
        win_rate = len(profitable_pairs) / total_pairs if total_pairs > 0 else 0

        # 计算平均盈利和亏损百分比
        avg_win_pct = np.mean([p['return_pct'] for p in profitable_pairs]) if profitable_pairs else 0
        avg_loss_pct = abs(np.mean([p['return_pct'] for p in losing_pairs])) if losing_pairs else 0
        
        # 计算盈亏比
        profit_factor = avg_win_pct / avg_loss_pct if avg_loss_pct > 0 else float('inf')
        
        # 计算总交易成本
        trades_df = pd.DataFrame(self.trades_history)
        total_costs = trades_df['trading_cost'].sum() if 'trading_cost' in trades_df.columns else 0
        
        # 在return语句之前添加
        print(f"\n=== _calculate_trade_statistics 返回值 ===")
        result = {
            'total_trades': len(self.trades_history),
            'completed_pairs': total_pairs,
            'profitable_trades': len(profitable_pairs),
            'losing_trades': len(losing_pairs),
            'win_rate': win_rate,
            'avg_win': avg_win_pct,
            'avg_loss': avg_loss_pct,
            'profit_factor': profit_factor,
            'total_trading_costs': total_costs
        }
        print(f"返回的统计数据: {result}")
        return result
    def _get_trade_pairs(self) -> List[Dict]:
        """
        将买卖交易配对，计算每对的盈亏
        使用FIFO（先进先出）方法配对
        """
        pairs = []
        positions = {}  # {symbol: [buy_trades]}
        
        for trade in self.trades_history:
            symbol = trade['symbol']
            if symbol not in positions:
                positions[symbol] = []
            
            if trade['action'] == 'buy':
                # 买入交易加入队列
                positions[symbol].append(trade)
            elif trade['action'] == 'sell':
                # 卖出交易与买入交易配对
                sell_qty = trade['shares']
                sell_price = trade['price']
                sell_cost = trade.get('trading_cost', 0)
                
                while sell_qty > 0 and positions[symbol]:
                    buy_trade = positions[symbol][0]
                    buy_price = buy_trade['price']
                    buy_cost = buy_trade.get('trading_cost', 0)
                    
                    # 计算这次配对的数量
                    pair_qty = min(sell_qty, buy_trade['shares'])
                    
                    # 计算盈亏
                    gross_pnl = (sell_price - buy_price) * pair_qty
                    
                    # 正确分摊交易成本
                    allocated_buy_cost = buy_cost * (pair_qty / buy_trade['shares'])
                    allocated_sell_cost = sell_cost * (pair_qty / trade['shares'])
                    net_pnl = gross_pnl - allocated_buy_cost - allocated_sell_cost
                    return_pct = ((sell_price - buy_price) / buy_price) * 100
                    
                    pairs.append({
                        'symbol': symbol,
                        'buy_date': buy_trade.get('date'),
                        'sell_date': trade.get('date'),
                        'buy_price': buy_price,
                        'sell_price': sell_price,
                        'quantity': pair_qty,
                        'gross_pnl': gross_pnl,
                        'net_pnl': net_pnl,
                        'return_pct': return_pct,
                        'holding_days': 0  # 可以后续计算
                    })
                    
                    # 更新剩余数量
                    buy_trade['shares'] -= pair_qty
                    sell_qty -= pair_qty
                    
                    # 如果买入交易完全配对，移除
                    if buy_trade['shares'] == 0:
                        positions[symbol].pop(0)
        print(f"\n=== 交易配对调试信息 ===")
        print(f"生成的配对数量: {len(pairs)}")
        
        if pairs:
            print("\n前3个配对详情:")
            for i, pair in enumerate(pairs[:3]):
                print(f"  配对{i+1}: {pair}")
            
            # 统计盈亏配对
            profitable = [p for p in pairs if p['net_pnl'] > 0]
            losing = [p for p in pairs if p['net_pnl'] < 0]
            print(f"\n盈利配对数: {len(profitable)}")
            print(f"亏损配对数: {len(losing)}")
            
            if profitable:
                avg_profit_pct = np.mean([p['return_pct'] for p in profitable])
                print(f"平均盈利百分比: {avg_profit_pct:.2f}%")
            
            if losing:
                avg_loss_pct = np.mean([p['return_pct'] for p in losing])
                print(f"平均亏损百分比: {avg_loss_pct:.2f}%")
        return pairs
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
            
            # 记录所有交易到历史（简化版本，不计算pnl）
            trade_record = trade.copy()
            trade_record['timestamp'] = trade.get('date')
            # 移除原来的pnl计算，让配对方法来处理
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