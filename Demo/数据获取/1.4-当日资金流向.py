from common import *

df = ak.stock_hsgt_fund_flow_summary_em()
print(tabulate(df, headers='keys', tablefmt='psql'))
# PYTHON Tips01：根据列值为北向 取出行
northward = df[df['资金方向'] == '北向']
# PYTHON Tips02：
hg_net = round(northward[northward['板块'] == '沪股通']['成交净买额'].sum(), 4)
sg_net = round(northward[northward['板块'] == '深股通']['成交净买额'].sum(), 4)
bx_net = round(hg_net + sg_net)

bx_txt = f"买入 {bx_net}" if bx_net > 0 else f"卖出 {abs(bx_net)}"
hg_txt = f"买入 {hg_net}" if hg_net > 0 else f"卖出 {abs(hg_net)}"
sg_txt = f"买入 {sg_net}" if sg_net > 0 else f"卖出 {abs(sg_net)}"
'''
任务：打印出 北向资金全天净 XX 亿元，其中沪股通净 XX 亿元，深股通净 XX 亿元
'''
print(f"北向资金全天净 {bx_txt} 亿元，其中沪股通净 {hg_txt} 亿元，深股通净 {sg_txt} 亿元")

'''
概念股资金流向
'''
# “即时”, "3日排行", "5日排行", "10日排行", "20日排行"
df = ak.stock_fund_flow_concept(symbol="即时")
gainian_df = df.sort_values(by="行业-涨跌幅", ascending=False)
print(tabulate(gainian_df, headers='keys', tablefmt='psql'))

'''
行业资金流
'''
df = ak.stock_fund_flow_industry(symbol="5日排行")
hangye_df = df.sort_values(by="净额", ascending=False)
print(tabulate(hangye_df, headers='keys', tablefmt='psql'))