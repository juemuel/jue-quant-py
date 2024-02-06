import tushare as ts # https://tushare.pro/document/1 https://tushare.pro/document/2
ts.set_token("a1533fd58c006f92b96286c3af7f044ad853d51cf2dec60e8f32b33e")
pro = ts.pro_api()
#行情数据（日、周、月）
df = pro.daily(ts_code='000001.SZ,600000.SH', start_date='20180701', end_date='20180718')