from comm import *

# 股东变动
zh_a_gdhs_df = ak.stock_zh_a_gdhs(symbol='20230609')
print(zh_a_gdhs_df)

'''
任务：使用tabulate打印markdown结果
'''
print('*' * 100)
print(tabulate(zh_a_gdhs_df, tablefmt='github'))
print('*' * 100)
print(tabulate(zh_a_gdhs_df, headers='keys', tablefmt='github'))
# 股东户数详情
# zh_a_gdhs_detail_em_df = ak.stock_zh_a_gdhs_detail_em(symbol='')

# 股东增减持
# ak.stock_ggcg_em(symbol='股东增持')

# 十大流通股东
# ak.stock_gdfx_free_top_10_em(date='20230609')

# 十大流通股东持股明细
# ak.stock_gdfx_free_holding_detail_em(date='20230609')

# 股东协同-十大股东
# ak.stock_gdfx_holding_teamwork_em()
