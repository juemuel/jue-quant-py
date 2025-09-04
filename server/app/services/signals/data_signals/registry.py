from typing import Dict, Optional, List, Callable
from .core import SignalRuleFunc, FilterRuleFunc
from .basic_rules import BASIC_RULES_METADATA
from .filter_rules import FILTER_RULES_METADATA
from .parameterized_rules import PARAMETERIZED_RULE_CREATORS

class SignalRuleRegistry:
    """信号规则注册表 - 统一管理所有信号规则及其所需指标"""
    
    def __init__(self):
        self._signal_rules = {}
        self._filter_rules = {}
        self._rule_indicators = {}
        self._rule_categories = {}
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """初始化默认规则"""
        # 注册基础信号规则
        for name, metadata in BASIC_RULES_METADATA.items():
            self.register_signal_rule(name, metadata)
        
        # 注册过滤规则
        for name, metadata in FILTER_RULES_METADATA.items():
            self.register_filter_rule(name, metadata)
    
    def register_signal_rule(self, name: str, metadata: Dict):
        """注册信号规则"""
        self._signal_rules[name] = {
            'func': metadata['func'],
            'chinese_name': metadata['chinese_name'],
            'category': metadata['category'],
            'description': metadata.get('description', ''),
            'type': 'signal'
        }
        
        self._rule_indicators[name] = {
            'required': metadata.get('required_indicators', []),
            'optional': metadata.get('optional_indicators', [])
        }
        
        self._add_to_category(metadata['category'], name)
    
    def register_filter_rule(self, name: str, metadata: Dict):
        """注册过滤规则"""
        self._filter_rules[name] = {
            'func': metadata['func'],
            'chinese_name': metadata['chinese_name'],
            'category': metadata['category'],
            'description': metadata.get('description', ''),
            'type': 'filter'
        }
        
        self._add_to_category(metadata['category'], name)
    
    def create_parameterized_rule(self, rule_type: str, name: str, **params) -> str:
        """创建参数化规则实例"""
        if rule_type not in PARAMETERIZED_RULE_CREATORS:
            raise ValueError(f"Unknown parameterized rule type: {rule_type}")
        
        creator = PARAMETERIZED_RULE_CREATORS[rule_type]
        rule_func = creator(**params)
        
        # 生成唯一实例名称
        param_str = '_'.join([f"{k}{v}" for k, v in params.items()])
        instance_name = f"{name}_{param_str}"
        
        # 注册规则实例
        metadata = rule_func.metadata
        self.register_signal_rule(instance_name, {
            'func': rule_func,
            'chinese_name': metadata['chinese_name'],
            'category': metadata['category'],
            'required_indicators': metadata['required_indicators'],
            'parameters': metadata['parameters'],
            'description': f"参数化规则: {metadata['parameters']}"
        })
        
        return instance_name
    def get_rule(self, name: str) -> Optional[Dict]:
        """获取规则完整信息（包含函数和元数据）"""
        return self._signal_rules.get(name)
    def get_signal_rule(self, name: str) -> Optional[SignalRuleFunc]:
        """获取信号规则函数"""
        rule_info = self._signal_rules.get(name)
        return rule_info['func'] if rule_info else None
    def get_signal_rule_with_metadata(self, name: str) -> Optional[SignalRuleFunc]:
        """获取带有metadata属性的信号规则函数"""
        rule_info = self._signal_rules.get(name)
        if not rule_info:
            return None
            
        func = rule_info['func']
        
        # 如果函数已经有metadata，直接返回
        if hasattr(func, 'metadata'):
            return func
            
        # 否则添加metadata属性
        func.metadata = {
            'chinese_name': rule_info['chinese_name'],
            'category': rule_info['category'],
            'description': rule_info['description']
        }
        
        return func
    def get_filter_rule(self, name: str) -> Optional[FilterRuleFunc]:
        """获取过滤规则函数"""
        rule_info = self._filter_rules.get(name)
        return rule_info['func'] if rule_info else None
    
    def get_rule_indicators(self, name: str) -> Optional[Dict]:
        """获取规则所需指标"""
        return self._rule_indicators.get(name)
    
    def get_all_required_indicators(self, rule_names: List[str]) -> List[str]:
        """获取多个规则的所有必需指标"""
        all_indicators = set()
        for rule_name in rule_names:
            indicators = self.get_rule_indicators(rule_name)
            if indicators:
                all_indicators.update(indicators['required'])
        return list(all_indicators)
    
    def get_all_indicators(self, rule_names: List[str]) -> Dict[str, List[str]]:
        """获取多个规则的所有指标（必需+可选）"""
        required = set()
        optional = set()
        
        for rule_name in rule_names:
            indicators = self.get_rule_indicators(rule_name)
            if indicators:
                required.update(indicators['required'])
                optional.update(indicators['optional'])
        
        return {
            'required': list(required),
            'optional': list(optional),
            'all': list(required | optional)
        }
    
    def list_signal_rules(self) -> Dict[str, Dict]:
        """列出所有信号规则"""
        return self._signal_rules.copy()
    
    def list_filter_rules(self) -> Dict[str, Dict]:
        """列出所有过滤规则"""
        return self._filter_rules.copy()
    
    def get_rules_by_category(self, category: str) -> List[str]:
        """按类别获取规则"""
        return self._rule_categories.get(category, [])
    
    def list_categories(self) -> List[str]:
        """列出所有类别"""
        return list(self._rule_categories.keys())
    
    def get_rule_summary(self) -> Dict:
        """获取规则摘要信息"""
        return {
            'total_signal_rules': len(self._signal_rules),
            'total_filter_rules': len(self._filter_rules),
            'categories': {cat: len(rules) for cat, rules in self._rule_categories.items()},
            'rules_by_category': self._rule_categories.copy()
        }
    
    def _add_to_category(self, category: str, rule_name: str):
        """添加规则到分类"""
        if category not in self._rule_categories:
            self._rule_categories[category] = []
        self._rule_categories[category].append(rule_name)

# 创建全局注册表实例
rule_registry = SignalRuleRegistry()