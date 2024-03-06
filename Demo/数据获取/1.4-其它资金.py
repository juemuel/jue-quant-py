import akshare as ak
import pandas as pd
# 显示完成列
pd.set_option('display.max_columns', None)
# 显示完成行
pd.set_option('display.max_rows', None)
# 输出不折行
pd.set_option('expand_frame_repr', False)

'''
沪深通资金流向
'''
df = ak.stock_hsgt_fund_flow_summary_em()
# print(df)
# 根据条件进行筛选，从资金方向选择北向，选择板块为沪股通、深股通
northward = df[df['资金方向'] == '北向']
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
# df = ak.stock_fund_flow_concept(symbol="即时")
# print(df.sort_values(by="净额", ascending=False))

'''
行业资金流
'''
# df = ak.stock_fund_flow_industry(symbol="5日排行")
# print(df.sort_values(by="净额", ascending=False))