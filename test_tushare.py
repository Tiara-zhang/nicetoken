import os, sys
for k in list(os.environ):
    if 'proxy' in k.lower():
        del os.environ[k]
import socket
_orig = socket.create_connection
def _no_proxy(addr, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None, **kw):
    return _orig(addr, timeout, source_address)
socket.create_connection = _no_proxy

import tushare as ts
ts.set_token("7600fe8922dca5889a1355e653ca003bf7450673bb2c79bef865c337")
pro = ts.pro_api()

print("=== 指数测试 ===")
df = pro.index_daily(ts_code="000001.SH", start_date="20260520", end_date="20260602")
print(df.head(3).to_string())

print()
print("=== 板块测试 ===")
try:
    df2 = pro.ths_daily(trade_date="20260602")
    if df2 is not None and not df2.empty:
        print(df2.head(5).to_string())
    else:
        print("ths_daily empty")
except Exception as e:
    print(f"ths_daily error: {e}")

# 看看有哪些板块函数
print()
# 看当前积分能用的接口
print()
print("=== 试免费接口 ===")
funcs_to_try = ['daily', 'trade_cal', 'stock_basic', 'namechange', 'hs_const', 'stock_company']
for f in funcs_to_try:
    try:
        fn = getattr(pro, f)
        df = fn()
        print(f'{f}: OK ({len(df)} rows)')
    except Exception as e:
        print(f'{f}: ERR {str(e)[:60]}')

print()
print("=== 所有 pro 接口 ===")
all_funcs = [x for x in dir(pro) if not x.startswith('_')]
print(all_funcs)
