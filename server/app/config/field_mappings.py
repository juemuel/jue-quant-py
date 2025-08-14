"""
数据字段映射配置
"""
# 数据源字段映射（接口原始字段名 -> 标准字段名）
DATA_SOURCE_MAPPINGS = {
    'akshare': {
        # 1.1.1 股票列表映射
        'stock_list': {
            'code': 'symbol_code',
            'name': 'symbol_name',
        },
        # 1.1.2 概念板块列表映射
        'concept_data': {
            '排名': 'rank',
            '板块名称': 'concept_name',
            '板块代码': 'concept_code',
            '最新价': 'current_price',
            '涨跌额': 'change_amount',
            '涨跌幅': 'change_percent',
            '总市值': 'total_market_value',
            '换手率': 'turnover_rate',
            '上涨家数': 'rise_count',
            '下跌家数': 'fall_count',
            '领涨股票': 'leading_stock',
            '领涨股票-涨跌幅': 'leading_stock_change_percent'
        },
        # 1.1.3 概念成分股映射
        'concept_constituent_stocks': {
            '代码': 'symbol_code',
            '名称': 'symbol_name', 
            '最新价': 'current_price',
            '涨跌幅': 'change_percent',
            '涨跌额': 'change_amount',
            '成交量': 'volume',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '最高': 'high',
            '最低': 'low',
            '今开': 'open',
            '昨收': 'prev_close',
            '换手率': 'turnover_rate',
            '市盈率-动态': 'pe_ratio',
            '市净率': 'pb_ratio'
        },
        # 1.2.1 股票历史数据映射
        'stock_history': {
            '股票代码': 'symbol',
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '涨跌幅': 'change_percent',
            '涨跌额': 'change_amount',
            '换手率': 'turnover_rate'
        },
        # 1.3.1 股票实时行情映射
        'realtime_quotes': {
            '序号': 'row_number',
            '代码': 'symbol',
            '名称': 'name',
            '最新价': 'current_price',
            '涨跌幅': 'change_percent',
            '涨跌额': 'change_amount',
            '成交量': 'volume',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '最高': 'high',
            '最低': 'low',
            '今开': 'open',
            '昨收': 'prev_close',
            '量比': 'volume_ratio',
            '换手率': 'turnover_rate',
            '市盈率-动态': 'pe_ratio',
            '市净率': 'pb_ratio',
            '总市值': 'total_market_value',
            '流通市值': 'circulating_market_value',
            '涨速': 'rise_speed',
            '5分钟涨跌': 'change_5min',
            '60日涨跌幅': 'change_60d',
            '年初至今涨跌幅': 'change_ytd'
        },
        # 2.1 宏观数据映射
        # 2.1 宏观数据映射 - 按指标分类
        'macro_gdp': {
            '季度': 'period',
            '国内生产总值-绝对值': 'gdp_absolute_value',
            '国内生产总值-同比增长': 'gdp_yoy_growth',
            '第一产业-绝对值': 'primary_industry_absolute',
            '第一产业-同比增长': 'primary_industry_yoy',
            '第二产业-绝对值': 'secondary_industry_absolute',
            '第二产业-同比增长': 'secondary_industry_yoy',
            '第三产业-绝对值': 'tertiary_industry_absolute',
            '第三产业-同比增长': 'tertiary_industry_yoy',
        },
        'macro_cpi': {
            '商品': 'category',
            '日期': 'date',
            '今值': 'current_value',
            '预测值': 'forecast_value',
            '前值': 'previous_value',
        },
        'macro_ppi': {
            '商品': 'category',
            '日期': 'date', 
            '今值': 'current_value',
            '预测值': 'forecast_value',
            '前值': 'previous_value',
        },
        'macro_pmi': {
            '月份': 'month',
            '制造业-指数': 'manufacturing_index',
            '制造业-同比增长': 'manufacturing_yoy',
            '非制造业-指数': 'non_manufacturing_index',
            '非制造业-同比增长': 'non_manufacturing_yoy'
        },
        # 2.2 财务报告数据映射
        'financial_report': {
            # 基本信息
            'SECURITY_CODE': 'symbol_code',
            'SECURITY_NAME_ABBR': 'symbol_abbr',
            'REPORT_DATE': 'report_date',
            'REPORT_TYPE': 'report_type',
            
            # 资产类
            'TOTAL_ASSETS': 'total_assets',
            'FIXED_ASSET': 'fixed_assets',
            'INTANGIBLE_ASSET': 'intangible_assets',
            'GOODWILL': 'goodwill',
            'LONG_EQUITY_INVEST': 'long_term_equity_investment',
            'ACCOUNTS_RECE': 'accounts_receivable',
            'INVEST_RECE': 'investment_receivable',
            
            # 负债类
            'TOTAL_LIABILITIES': 'total_liabilities',
            'ACCOUNTS_PAYABLE': 'accounts_payable',
            'SHORT_FIN_PAYABLE': 'short_term_borrowing',
            'BOND_PAYABLE': 'bonds_payable',
            'STAFF_SALARY_PAYABLE': 'staff_salary_payable',
            'TAX_PAYABLE': 'tax_payable',
            
            # 所有者权益类
            'TOTAL_EQUITY': 'total_equity',
            'SHARE_CAPITAL': 'share_capital',
            'CAPITAL_RESERVE': 'capital_reserve',
            'SURPLUS_RESERVE': 'surplus_reserve',
            'UNASSIGN_RPOFIT': 'retained_earnings',
            'TOTAL_PARENT_EQUITY': 'parent_equity',
            'MINORITY_EQUITY': 'minority_equity',
            
            # 同比增长率字段
            'TOTAL_ASSETS_YOY': 'total_assets_yoy',
            'TOTAL_LIABILITIES_YOY': 'total_liabilities_yoy',
            'TOTAL_EQUITY_YOY': 'total_equity_yoy',
        },
        # 3.1 资金流向数据映射
        'fund_flow': {
            "序号": "rank",
            "代码": "code",
            "名称": "name",
            "最新价": "latest_price",
            "今日涨跌幅": "change_pct",
            "今日主力净流入-净额": "main_net_inflow_amount",
            "今日主力净流入-净占比": "main_net_inflow_pct",
            "今日超大单净流入-净额": "super_large_net_inflow_amount",
            "今日超大单净流入-净占比": "super_large_net_inflow_pct",
            "今日大单净流入-净额": "large_net_inflow_amount",
            "今日大单净流入-净占比": "large_net_inflow_pct",
            "今日中单净流入-净额": "medium_net_inflow_amount",
            "今日中单净流入-净占比": "medium_net_inflow_pct",
            "今日小单净流入-净额": "small_net_inflow_amount",
            "今日小单净流入-净占比": "small_net_inflow_pct"
        },
        # 3.2 龙虎榜数据映射
        'dragon_tiger': {
            '序号': 'row_number',
            '代码': 'symbol_code',
            '名称': 'symbol_name',
            '上榜日': 'list_date',
            '解读': 'reason',
            '收盘价': 'close_price',
            '涨跌幅': 'change_percent',
            '龙虎榜净买额': 'net_buy_amount',
            '龙虎榜买入额': 'buy_amount',
            '龙虎榜卖出额': 'sell_amount',
            '龙虎榜成交额': 'turnover_amount',
            '市场总成交额': 'market_total_amount',
            '净买额占总成交比': 'net_buy_ratio',
            '成交额占总成交比': 'turnover_ratio',
            '换手率': 'turnover_rate',
            '流通市值': 'circulating_market_value',
            '上榜原因': 'listing_reason',
            '上榜后1日': 'after_1_day',
            '上榜后2日': 'after_2_day',
            '上榜后5日': 'after_5_day',
            '上榜后10日': 'after_10_day'
        },
        # 4.1 新闻情感数据映射
        'news_sentiment': {
            '新闻标题': 'news_title',
            '新闻内容': 'news_content',
            '发布时间': 'publish_time',
            '文章来源': 'news_source',
            '新闻链接': 'news_url',
            # '关键词': 'keywords',
            # '情感得分': 'sentiment_score',
            # '情感分类': 'sentiment_category'
        }
    },
    
    'tushare': {
    },
    
    'yfinance': {
       
    }
}

# 核心字段配置（默认仅返回核心字段）
CORE_FIELDS = {
    'stock_list': ['symbol_code', 'symbol_name'],
    'concept_data': ['rank', 'concept_code', 'concept_name', 'current_price', 'change_percent', 'total_market_value'],
    'concept_constituent_stocks': ['rank', 'symbol_code', 'symbol_name', 'current_price', 'change_percent', 'volume', 'amount', 'turnover_rate'],
    'stock_history': ['symbol', 'date', 'open', 'close', 'high', 'low', 'volume', 'change_percent', 'turnover_rate'],
    'realtime_quotes': ['row_number', 'symbol', 'name', 'current_price', 'change_percent', 'volume', 'amount'],
    'macro_gdp': [
        'period', 'gdp_absolute_value', 'gdp_yoy_growth', 
        'primary_industry_yoy', 'secondary_industry_yoy', 'tertiary_industry_yoy'
    ],
    'macro_cpi': [
        'date', 'category', 'current_value', 'forecast_value', 'previous_value'
    ],
    'macro_ppi': [
        'date', 'category', 'current_value', 'forecast_value', 'previous_value'
    ],
    'macro_pmi': [
        'month', 'manufacturing_index', 'manufacturing_yoy', 
        'non_manufacturing_index', 'non_manufacturing_yoy'
    ],
    'financial_report': [
        'symbol_code', 'symbol_abbr', 'report_date', 'report_type',
        'total_assets', 'total_liabilities', 'total_equity', 'share_capital',
        'capital_reserve', 'retained_earnings', 'parent_equity',
        'total_assets_yoy', 'total_liabilities_yoy', 'total_equity_yoy'
    ],
    "fund_flow": ["code", "name", "latest_price", "change_pct", "main_net_inflow_amount", "main_net_inflow_pct"],
    'dragon_tiger': [
        'row_number', 'symbol_code', 'symbol_name', 'list_date', 'reason', 
        'close_price', 'change_percent', 'net_buy_amount', 'buy_amount', 
        'sell_amount', 'turnover_amount', 'net_buy_ratio', 'turnover_ratio'
    ],
    'news_sentiment': [
        'news_title', 'news_content', 'publish_time', 'news_source',  'news_url'
    ]
}
# 标准字段定义转中文（作为统一的输出格式）
STANDARD_FIELDS = {
    # 股票列表
    'symbol_code': '证券代码',
    'symbol_name': '证券名称',
    # 概念数据
    'rank': '排名',
    'concept_code': '板块代码',
    'concept_name': '板块名称',
    'current_price': '最新价',
    'change_amount': '涨跌额',
    'change_percent': '涨跌幅',
    'total_market_value': '总市值',
    'turnover_rate': '换手率',
    'rise_count': '上涨家数',
    'fall_count': '下跌家数',
    'leading_stock': '领涨股票',
    'leading_stock_change_percent': '领涨股票涨跌幅',
    # 概念成分数据（仅补充未定义内容）
    'prev_close': '昨收价',
    # 股票历史数据
    'symbol': '证券代码',
    'date': '日期',
    'open': '开盘价',
    'close': '收盘价',
    'high': '最高价',
    'low': '最低价',
    'volume': '成交量',
    'amount': '成交额',
    'amplitude': '振幅',
    'change_percent': '涨跌幅',
    'change_amount': '涨跌额',
    'turnover_rate': '换手率',
    # 实时行情
    'row_number': '序号',
    'name': '证券名称',
    'open': '今开价',
    'prev_close': '昨收价',
    'rise_speed': '涨速',
    'change_5min': '5分钟涨跌',
    'change_60d': '60日涨跌幅',
    'change_ytd': '年初至今涨跌幅',
    'current_price': '最新价',
    'volume_ratio': '量比',
    'pe_ratio': '市盈率',
    'pb_ratio': '市净率',
    'total_market_value': '总市值',
    'circulating_market_value': '流通市值',

    # 宏观经济数据
    'period': '时期',
    'date': '日期',
    'month': '月份',
    'gdp_absolute_value': 'GDP绝对值',
    'gdp_yoy_growth': 'GDP同比增长',
    'primary_industry_absolute': '第一产业绝对值',
    'primary_industry_yoy': '第一产业同比增长',
    'secondary_industry_absolute': '第二产业绝对值',
    'secondary_industry_yoy': '第二产业同比增长',
    'tertiary_industry_absolute': '第三产业绝对值',
    'tertiary_industry_yoy': '第三产业同比增长',
    'current_value': '当前值',
    'forecast_value': '预测值',
    'previous_value': '前值',
    'category': '类别',
    'manufacturing_index': '制造业指数',
    'manufacturing_yoy': '制造业同比增长',
    'non_manufacturing_index': '非制造业指数',
    'non_manufacturing_yoy': '非制造业同比增长',

    # 财务报告数据-基本信息
    'symbol_code': '证券代码',
    'symbol_name': '证券名称', 
    'symbol_abbr': '证券简称',
    'report_date': '报告日期',
    'report_type': '报告类型',
    'trade_date': '交易日期',
    'publish_time': '发布时间',
    'latest_price': '最新价格',
    'close_price': '收盘价',
    'price_change_pct': '涨跌幅',
    
    # 财务报告数据-资产类
    'total_assets': '资产总计',
    'fixed_assets': '固定资产',
    'intangible_assets': '无形资产',
    'goodwill': '商誉',
    'long_term_equity_investment': '长期股权投资',
    'accounts_receivable': '应收账款',
    'investment_receivable': '应收投资款',
    
    # 财务报告数据-负债类
    'total_liabilities': '负债合计',
    'accounts_payable': '应付账款',
    'short_term_borrowing': '短期借款',
    'bonds_payable': '应付债券',
    'staff_salary_payable': '应付职工薪酬',
    'tax_payable': '应交税费',
    
    # 财务报告数据-所有者权益类
    'total_equity': '所有者权益合计',
    'share_capital': '股本',
    'capital_reserve': '资本公积',
    'surplus_reserve': '盈余公积',
    'retained_earnings': '未分配利润',
    'parent_equity': '归属于母公司所有者权益合计',
    'minority_equity': '少数股东权益',
    
    # 财务报告数据-同比增长率
    'total_assets_yoy': '资产总计同比增长率',
    'total_liabilities_yoy': '负债合计同比增长率',
    'total_equity_yoy': '所有者权益合计同比增长率',
    
    # 财务报告数据-损益类
    'revenue': '营业收入',
    'net_profit': '净利润',
    'gross_profit': '毛利润',
    'operating_profit': '营业利润',
    
    # 资金流向
    "rank": "排名",
    "code": "股票代码",
    "name": "股票名称",
    "latest_price": "最新价",
    "change_pct": "涨跌幅",
    "main_net_inflow_amount": "主力净流入金额",
    "main_net_inflow_pct": "主力净流入占比",
    "super_large_net_inflow_amount": "超大单净流入金额",
    "super_large_net_inflow_pct": "超大单净流入占比",
    "large_net_inflow_amount": "大单净流入金额",
    "large_net_inflow_pct": "大单净流入占比",
    "medium_net_inflow_amount": "中单净流入金额",
    "medium_net_inflow_pct": "中单净流入占比",
    "small_net_inflow_amount": "小单净流入金额",
    "small_net_inflow_pct": "小单净流入占比",
    
    # 龙虎榜字段
    'rank': '排名',
    'symbol_code': '证券代码',
    'symbol_name': '证券名称',
    'list_date': '上榜日',
    'reason': '解读',
    'close_price': '收盘价',
    'change_percent': '涨跌幅',
    'net_buy_amount': '龙虎榜净买额',
    'buy_amount': '龙虎榜买入额',
    'sell_amount': '龙虎榜卖出额',
    'turnover_amount': '龙虎榜成交额',
    'market_total_amount': '市场总成交额',
    'net_buy_ratio': '净买额占总成交比',
    'turnover_ratio': '成交额占总成交比',
    'turnover_rate': '换手率',
    'circulating_market_value': '流通市值',
    'listing_reason': '上榜原因',
    'after_1_day': '上榜后1日',
    'after_2_day': '上榜后2日',
    'after_5_day': '上榜后5日',
    'after_10_day': '上榜后10日',

    # 新闻情感
    'news_title': '新闻标题',
    'news_content': '新闻内容',
    'publish_time': '发布时间',
    'news_source': '文章来源',
    'news_url': '新闻链接',
    # 'sentiment_score': '情感得分',
    # 'keywords': '关键词',
    # 'sentiment_category': '情感分类',
    # 'related_stocks': '相关股票',
}
# 报告类型映射
REPORT_TYPE_MAPPING = {
    'annual': '年报',
    'quarterly': '一季报', 
    'semi_annual': '中报',
    'third_quarter': '三季报'
}
