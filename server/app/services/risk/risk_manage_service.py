from core.logger import logger
from data_providers import get_data_provider
from common.utils import clean_numeric_data, safe_convert_to_dict, debug_dataframe
import pandas as pd
import numpy as np
import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
# ============ 风险指标计算 ============
def calculate_volatility(returns, period=252):
    """
    计算波动率
    :param returns: 收益率序列
    :param period: 年化周期（默认252个交易日）
    :return: 波动率指标
    """
    logger.info(f"[Risk]计算波动率，年化周期: {period}")
    try:
        if isinstance(returns, list):
            returns = pd.Series(returns)
        
        # 计算日波动率
        daily_volatility = returns.std()
        
        # 年化波动率
        annualized_volatility = daily_volatility * np.sqrt(period)
        
        return {
            "status": "success",
            "data": {
                "daily_volatility": daily_volatility,
                "annualized_volatility": annualized_volatility
            },
            "message": "波动率计算完成"
        }
    except Exception as e:
        logger.error(f"[Risk]计算波动率失败: {e}")
        return {"status": "error", "message": f"计算失败: {e}"}

def calculate_max_drawdown(portfolio_values):
    """
    计算最大回撤
    :param portfolio_values: 组合价值序列
    :return: 最大回撤指标
    """
    logger.info("[Risk]计算最大回撤")
    try:
        if isinstance(portfolio_values, list):
            portfolio_values = pd.Series(portfolio_values)
        
        # 计算累计收益
        cumulative = portfolio_values / portfolio_values.iloc[0]
        
        # 计算历史最高点
        running_max = cumulative.expanding().max()
        
        # 计算回撤
        drawdown = (cumulative - running_max) / running_max
        
        # 最大回撤
        max_drawdown = drawdown.min()
        
        # 最大回撤开始和结束时间
        max_dd_end = drawdown.idxmin()
        max_dd_start = cumulative.loc[:max_dd_end].idxmax()
        
        return {
            "status": "success",
            "data": {
                "max_drawdown": max_drawdown,
                "max_drawdown_pct": max_drawdown * 100,
                "drawdown_start": max_dd_start,
                "drawdown_end": max_dd_end,
                "current_drawdown": drawdown.iloc[-1]
            },
            "message": "最大回撤计算完成"
        }
    except Exception as e:
        logger.error(f"[Risk]计算最大回撤失败: {e}")
        return {"status": "error", "message": f"计算失败: {e}"}

def calculate_sharpe_ratio(returns, risk_free_rate=0.03, period=252):
    """
    计算夏普比率
    :param returns: 收益率序列
    :param risk_free_rate: 无风险利率
    :param period: 年化周期
    :return: 夏普比率
    """
    logger.info(f"[Risk]计算夏普比率，无风险利率: {risk_free_rate}")
    try:
        if isinstance(returns, list):
            returns = pd.Series(returns)
        
        # 计算超额收益
        excess_returns = returns - risk_free_rate / period
        
        # 计算夏普比率
        sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(period)
        
        return {
            "status": "success",
            "data": {
                "sharpe_ratio": sharpe_ratio,
                "annualized_return": returns.mean() * period,
                "annualized_volatility": returns.std() * np.sqrt(period)
            },
            "message": "夏普比率计算完成"
        }
    except Exception as e:
        logger.error(f"[Risk]计算夏普比率失败: {e}")
        return {"status": "error", "message": f"计算失败: {e}"}

def calculate_var(returns, confidence_level=0.05):
    """
    计算风险价值(VaR)
    :param returns: 收益率序列
    :param confidence_level: 置信水平
    :return: VaR值
    """
    logger.info(f"[Risk]计算VaR，置信水平: {confidence_level}")
    try:
        if isinstance(returns, list):
            returns = pd.Series(returns)
        
        # 历史模拟法计算VaR
        var = np.percentile(returns, confidence_level * 100)
        
        # 条件VaR (CVaR)
        cvar = returns[returns <= var].mean()
        
        return {
            "status": "success",
            "data": {
                "var": var,
                "var_pct": var * 100,
                "cvar": cvar,
                "cvar_pct": cvar * 100,
                "confidence_level": confidence_level
            },
            "message": "VaR计算完成"
        }
    except Exception as e:
        logger.error(f"[Risk]计算VaR失败: {e}")
        return {"status": "error", "message": f"计算失败: {e}"}

def calculate_win_rate(trades):
    """
    计算交易胜率
    :param trades: 交易记录列表
    :return: 胜率（0-1之间的浮点数）
    """
    if not trades:
        return 0
    
    buy_trades = [t for t in trades if t.get('action') == 'buy']
    sell_trades = [t for t in trades if t.get('action') == 'sell']
    
    if len(buy_trades) != len(sell_trades):
        # 如果有未平仓的交易，只计算已完成的交易对
        completed_pairs = min(len(buy_trades), len(sell_trades))
        buy_trades = buy_trades[:completed_pairs]
        sell_trades = sell_trades[:completed_pairs]
    
    if not sell_trades:
        return 0
    
    profitable_trades = 0
    for i in range(len(sell_trades)):
        buy_price = buy_trades[i]['price']
        sell_price = sell_trades[i]['price']
        if sell_price > buy_price:
            profitable_trades += 1
    
    return profitable_trades / len(sell_trades)
# ============ 仓位管理 ============
def calculate_position_size(capital, risk_per_trade, entry_price, stop_loss):
    """
    计算仓位大小
    :param capital: 总资金
    :param risk_per_trade: 单笔交易风险比例
    :param entry_price: 入场价格
    :param stop_loss: 止损价格
    :return: 建议仓位大小
    """
    logger.info(f"[Risk]计算仓位大小，风险比例: {risk_per_trade}")
    try:
        # 风险金额
        risk_amount = capital * risk_per_trade
        
        # 每股风险
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk == 0:
            return {"status": "error", "message": "入场价格与止损价格不能相同"}
        
        # 计算仓位大小
        position_size = risk_amount / price_risk
        
        # 计算仓位价值
        position_value = position_size * entry_price
        
        # 仓位占比
        position_ratio = position_value / capital
        
        return {
            "status": "success",
            "data": {
                "position_size": int(position_size),
                "position_value": position_value,
                "position_ratio": position_ratio,
                "position_ratio_pct": position_ratio * 100,
                "risk_amount": risk_amount,
                "price_risk": price_risk
            },
            "message": "仓位计算完成"
        }
    except Exception as e:
        logger.error(f"[Risk]计算仓位大小失败: {e}")
        return {"status": "error", "message": f"计算失败: {e}"}

# ============ 绩效分析 ============
def comprehensive_performance_analysis(portfolio_values, trades, returns=None, risk_free_rate=0.03):
    """
    综合绩效分析
    :param portfolio_values: 组合价值序列
    :param trades: 交易记录
    :param returns: 收益率序列（可选，如果不提供会自动计算）
    :param risk_free_rate: 无风险利率
    :return: 完整的绩效分析结果
    """
    try:
        if returns is None:
            portfolio_series = pd.Series(portfolio_values)
            returns = portfolio_series.pct_change().dropna()
        
        analysis_result = {
            "status": "success",
            "data": {
                "win_rate": calculate_win_rate(trades),
                "volatility": calculate_volatility(returns),
                "max_drawdown": calculate_max_drawdown(portfolio_values),
                "sharpe_ratio": calculate_sharpe_ratio(returns, risk_free_rate),
                "var": calculate_var(returns)
            }
        }
        
        return analysis_result
    except Exception as e:
        logger.error(f"[Risk]综合绩效分析失败: {e}")
        return {"status": "error", "message": f"分析失败: {e}"}


# ============ 抽象基类 ============
class RiskManager(ABC):
    """风控管理器抽象基类"""
    
    @abstractmethod
    def should_enter_position(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """判断是否可以开仓"""
        pass
    
    @abstractmethod
    def should_exit_position(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """判断是否应该平仓"""
        pass
    
    @abstractmethod
    def get_stop_loss_price(self, entry_price: float, context: Dict[str, Any]) -> float:
        """获取止损价格"""
        pass

class PositionManager(ABC):
    """仓位管理器抽象基类"""
    @abstractmethod
    def calculate_position_size(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """计算仓位大小"""
        pass
    
    @abstractmethod
    def adjust_position(self, current_position: int, context: Dict[str, Any]) -> Dict[str, Any]:
        """调整仓位"""
        pass

# ============ 具体实现 ============
class BasicRiskManager(RiskManager):
    """基础风控管理器"""
    def __init__(self, max_position_ratio=0.3, stop_loss_pct=0.05, max_drawdown=0.15):
        self.max_position_ratio = max_position_ratio
        self.stop_loss_pct = stop_loss_pct
        self.max_drawdown = max_drawdown
    
    def should_enter_position(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """基础开仓风控检查"""
        try:
            portfolio_value = context.get('portfolio_value', 0)
            current_drawdown = context.get('current_drawdown', 0)
            
            # 检查最大回撤
            if current_drawdown > self.max_drawdown:
                return {
                    "status": "reject",
                    "reason": f"当前回撤{current_drawdown:.2%}超过最大允许回撤{self.max_drawdown:.2%}"
                }
            
            # 检查资金充足性
            if portfolio_value <= 0:
                return {
                    "status": "reject",
                    "reason": "资金不足"
                }
            
            return {"status": "approve", "reason": "风控检查通过"}
            
        except Exception as e:
            return {"status": "error", "reason": f"风控检查失败: {e}"}
    
    def should_exit_position(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """基础平仓风控检查"""
        try:
            current_price = context.get('current_price', 0)
            entry_price = context.get('entry_price', 0)
            stop_loss_price = context.get('stop_loss_price', 0)
            
            # 检查止损
            if current_price <= stop_loss_price:
                return {
                    "status": "force_exit",
                    "reason": "触发止损",
                    "exit_type": "stop_loss"
                }
            
            return {"status": "hold", "reason": "继续持有"}
            
        except Exception as e:
            return {"status": "error", "reason": f"平仓检查失败: {e}"}
    
    def get_stop_loss_price(self, entry_price: float, context: Dict[str, Any]) -> float:
        """计算止损价格"""
        return entry_price * (1 - self.stop_loss_pct)

class FixedRatioPositionManager(PositionManager):
    """固定比例仓位管理器"""
    
    def __init__(self, risk_per_trade=0.02):
        self.risk_per_trade = risk_per_trade
    
    def calculate_position_size(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """基于固定风险比例计算仓位"""
        try:
            capital = context.get('capital', 0)
            entry_price = context.get('entry_price', 0)
            stop_loss_price = context.get('stop_loss_price', 0)
            commission = context.get('commission', 0.001)
            
            return calculate_position_size(
                capital=capital,
                risk_per_trade=self.risk_per_trade,
                entry_price=entry_price,
                stop_loss=stop_loss_price
            )
            
        except Exception as e:
            return {"status": "error", "message": f"仓位计算失败: {e}"}
    
    def adjust_position(self, current_position: int, context: Dict[str, Any]) -> Dict[str, Any]:
        """调整仓位（固定比例管理器不调整）"""
        return {
            "status": "success",
            "action": "hold",
            "new_position": current_position,
            "reason": "固定比例管理器不调整仓位"
        }

class DynamicPositionManager(PositionManager):
    """动态仓位管理器（基于市场波动率调整）"""
    
    def __init__(self, base_risk=0.02, volatility_adjustment=True):
        self.base_risk = base_risk
        self.volatility_adjustment = volatility_adjustment
    
    def calculate_position_size(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """基于市场波动率动态计算仓位"""
        try:
            capital = context.get('capital', 0)
            entry_price = context.get('entry_price', 0)
            stop_loss_price = context.get('stop_loss_price', 0)
            market_volatility = context.get('market_volatility', 0.2)  # 默认20%波动率
            
            # 根据波动率调整风险比例
            adjusted_risk = self.base_risk
            if self.volatility_adjustment:
                # 波动率越高，仓位越小
                volatility_factor = min(0.2 / market_volatility, 2.0)  # 限制调整倍数
                adjusted_risk = self.base_risk * volatility_factor
            
            return calculate_position_size(
                capital=capital,
                risk_per_trade=adjusted_risk,
                entry_price=entry_price,
                stop_loss=stop_loss_price
            )
            
        except Exception as e:
            return {"status": "error", "message": f"动态仓位计算失败: {e}"}
    
    def adjust_position(self, current_position: int, context: Dict[str, Any]) -> Dict[str, Any]:
        """根据市场情况动态调整仓位"""
        try:
            market_volatility = context.get('market_volatility', 0.2)
            profit_ratio = context.get('profit_ratio', 0)
            
            # 盈利时可以适当加仓，亏损时减仓
            if profit_ratio > 0.1:  # 盈利超过10%
                return {
                    "status": "success",
                    "action": "increase",
                    "adjustment_ratio": 1.2,
                    "reason": "盈利状态，适当加仓"
                }
            elif profit_ratio < -0.05:  # 亏损超过5%
                return {
                    "status": "success",
                    "action": "decrease",
                    "adjustment_ratio": 0.8,
                    "reason": "亏损状态，适当减仓"
                }
            
            return {
                "status": "success",
                "action": "hold",
                "new_position": current_position,
                "reason": "维持当前仓位"
            }
            
        except Exception as e:
            return {"status": "error", "message": f"仓位调整失败: {e}"}

# ============ 工厂类 ============
class ManagerFactory:
    """管理器工厂类"""
    
    _risk_managers = {
        'basic': BasicRiskManager,
    }
    
    _position_managers = {
        'fixed_ratio': FixedRatioPositionManager,
        'dynamic': DynamicPositionManager,
    }
    
    @classmethod
    def create_risk_manager(cls, manager_type: str, **kwargs) -> RiskManager:
        """创建风控管理器"""
        if manager_type not in cls._risk_managers:
            raise ValueError(f"未知的风控管理器类型: {manager_type}")
        return cls._risk_managers[manager_type](**kwargs)
    
    @classmethod
    def create_position_manager(cls, manager_type: str, **kwargs) -> PositionManager:
        """创建仓位管理器"""
        if manager_type not in cls._position_managers:
            raise ValueError(f"未知的仓位管理器类型: {manager_type}")
        return cls._position_managers[manager_type](**kwargs)
    
    @classmethod
    def register_risk_manager(cls, name: str, manager_class):
        """注册新的风控管理器"""
        cls._risk_managers[name] = manager_class
    
    @classmethod
    def register_position_manager(cls, name: str, manager_class):
        """注册新的仓位管理器"""
        cls._position_managers[name] = manager_class
    
    @classmethod
    def list_managers(cls) -> Dict[str, Any]:
        """列出所有可用的管理器"""
        return {
            "risk_managers": list(cls._risk_managers.keys()),
            "position_managers": list(cls._position_managers.keys())
        }

# def auto_register_risk_manager(name: str):
#     """自动注册风控管理器装饰器"""
#     def decorator(cls):
#         ManagerFactory.register_risk_manager(name, cls)
#         return cls
#     return decorator

# def auto_register_position_manager(name: str):
#     """自动注册仓位管理器装饰器"""
#     def decorator(cls):
#         ManagerFactory.register_position_manager(name, cls)
#         return cls
#     return decorator
