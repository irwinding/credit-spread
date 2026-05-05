# import time
# from moomoo import *
# class OrderBookTest(OrderBookHandlerBase):
#     def on_recv_rsp(self, rsp_pb):
#         ret_code, data = super(OrderBookTest,self).on_recv_rsp(rsp_pb)
#         if ret_code != RET_OK:
#             print("OrderBookTest: error, msg: %s" % data)
#             return RET_ERROR, data
#         print("OrderBookTest ", data) # OrderBookTest 自己的处理逻辑
#         return RET_OK, data
# quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11112)
# handler = OrderBookTest()
# quote_ctx.set_handler(handler)  # 设置实时摆盘回调
# quote_ctx.subscribe(['HK.HSImain'], [SubType.ORDER_BOOK, SubType.QUOTE])  # 订阅买卖摆盘类型，OpenD 开始持续收到服务器的推送
# time.sleep(15000)  #  设置脚本接收 OpenD 的推送持续时间为15秒
# quote_ctx.close()  # 关闭当条连接，OpenD 会在1分钟后自动取消相应股票相应类型的订阅


            # from moomoo import *
# pwd_unlock = '123456'
# trd_ctx = OpenSecTradeContext(filter_trdmarket=TrdMarket.US, host='127.0.0.1', port=11111, security_firm=SecurityFirm.FUTUINC)
# ret, data = trd_ctx.unlock_trade(pwd_unlock)  # 若使用真实账户下单，需先对账户进行解锁。此处示例为模拟账户下单，也可省略解锁。
# if ret == RET_OK:
#     ret, data = trd_ctx.place_order(price=63.0, qty=100, code="US.FUTU", trd_side=TrdSide.BUY, trd_env=TrdEnv.REAL)
#     if ret == RET_OK:
#         print(data)
#         print(data['order_id'][0])  # 获取下单的订单号
#         print(data['order_id'].values.tolist())  # 转为 list
#     else:
#         print('place_order error: ', data)
# else:
#     print('unlock_trade failed: ', data)
# trd_ctx.close()

# from moomoo import *
# trd_ctx = OpenSecTradeContext(filter_trdmarket=TrdMarket.HK, host='127.0.0.1', port=11111, security_firm=SecurityFirm.FUTUSECURITIES)
# ret, data = trd_ctx.get_acc_list()
# if ret == RET_OK:
#     print(data)
#     print(data['acc_id'][0])  # 取第一个账号
#     print(data['acc_id'].values.tolist())  # 转为 list
# else:
#     print('get_acc_list error: ', data)
# trd_ctx.close()

# from moomoo import *
# trd_ctx = OpenSecTradeContext(filter_trdmarket=TrdMarket.NONE, host='127.0.0.1', port=11111, security_firm=SecurityFirm.FUTUSECURITIES)
# ret, data = trd_ctx.accinfo_query()
# if ret == RET_OK:
#     print(data)
#     print(data['power'][0])  # 取第一行的购买力
#     print(data['power'].values.tolist())  # 转为 list
# else:
#     print('accinfo_query error: ', data)
# trd_ctx.close()  # 关闭当条连接
#
# from moomoo import *
# quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111,ai_type=0)
# ret, data, page_req_key = quote_ctx.request_history_kline('HK.00700', start='2019-09-11', end='2019-09-18', max_count=5, session=Session.ALL)  # 每页5个，请求第一页
# if ret == RET_OK:
#     print(data)
#     print(data['code'][0])    # 取第一条的股票代码
#     print(data['close'].values.tolist())   # 第一页收盘价转为 list
# else:
#     print('error:', data)
# while page_req_key != None:  # 请求后面的所有结果
#     print('*************************************')
#     ret, data, page_req_key = quote_ctx.request_history_kline('HK.00700', start='2019-09-11', end='2019-09-18', max_count=5, page_req_key=page_req_key, session=Session.ALL) # 请求翻页后的数据
#     if ret == RET_OK:
#         print(data)
#     else:
#         print('error:', data)
# print('All pages are finished!')
# quote_ctx.close() # 结束后记得关闭当条连接，防止连接条数用尽

# from moomoo import *
# pwd_unlock = '123456'
# trd_ctx = OpenSecTradeContext(filter_trdmarket=TrdMarket.HK, host='127.0.0.1', port=11111, security_firm=SecurityFirm.FUTUSECURITIES)
# ret, data = trd_ctx.unlock_trade(pwd_unlock)
# if ret == RET_OK:
#     print('unlock success!')
# else:
#     print('unlock_trade failed: ', data)
# trd_ctx.close()

# from moomoo import *
# quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
#
# ret, data = quote_ctx.get_technical_unusual('HK.00700',7)
# if ret == RET_OK:
#     print(data)
#     print(data['code'][0])    # 取第一条的股票代码
#     print(data['code'].values.tolist())   # 转为 list
# else:
#     print('error:', data)
# quote_ctx.close() # 结束后记得关闭当条连接，防止连接条数用尽


# from moomoo import *
# trd_ctx = OpenSecTradeContext(filter_trdmarket=TrdMarket.HK, host='127.0.0.1', port=11111, security_firm=SecurityFirm.FUTUSECURITIES,ai_type=1)
# ret, data = trd_ctx.accinfo_query()
# if ret == RET_OK:
#     print(data)
#     print(data['power'][0])  # 取第一行的购买力
#     print(data['power'].values.tolist())  # 转为 list
# else:
#     print('accinfo_query error: ', data)
# trd_ctx.close()  # 关闭当条连接


# from moomoo import *
# quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
#
# ret, data = quote_ctx.get_market_state(['SZ.000001', 'HK.00700'])
# if ret == RET_OK:
#     print(data)
# else:
#     print('error:', data)
# quote_ctx.close() # 结束后记得关闭当条连接，防止连接条数用尽


# from moomoo import *
# quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111,ai_type=1)
#
# ret, data = quote_ctx.get_capital_flow("HK.00700", period_type = PeriodType.INTRADAY)
# if ret == RET_OK:
#     print(data)
#     print(data['in_flow'][0])    # 取第一条的净流入的资金额度
#     print(data['in_flow'].values.tolist())   # 转为 list
# else:
#     print('error:', data)
# quote_ctx.close() # 结束后记得关闭当条连接，防止连接条数用尽

# from moomoo import *
# quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111,ai_type=1)
#
# ret, data = quote_ctx.get_capital_distribution("HK.00700")
# if ret == RET_OK:
#     print(data)
#     print(data['capital_in_big'][0])    # 取第一条的流入资金额度，大单
#     print(data['capital_in_big'].values.tolist())   # 转为 list
# else:
#     print('error:', data)
# quote_ctx.close() # 结束后记得关闭当条连接，防止连接条数用尽



# from moomoo import *
# quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111,ai_type=1)
#
# ret, data = quote_ctx.get_capital_flow("HK.00700", period_type = PeriodType.INTRADAY)
# if ret == RET_OK:
#     print(data)
#     print(data['in_flow'][0])    # 取第一条的净流入的资金额度
#     print(data['in_flow'].values.tolist())   # 转为 list
# else:
#     print('error:', data)
# quote_ctx.close() # 结束后记得关闭当条连接，防止连接条数用尽

from moomoo import *
quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)

ret, data = quote_ctx.get_technical_unusual("US..IXIC",time_range=7)
print("get_technical_unusual")
if ret == RET_OK:
    print(data)
else:
    print('error:', data)

ret, data = quote_ctx.get_financial_unusual("US.MU260424C442500",time_range=7)
print("get_financial_unusual")
if ret == RET_OK:
    print(data)
else:
    print('error:', data)

ret, data = quote_ctx.get_derivative_unusual("HK.00700",time_range=7)
print("get_derivative_unusual")
if ret == RET_OK:
    print(data)
else:
    print('error:', data)

quote_ctx.close() # 结束后记得关闭当条连接，防止连接条数用尽

# from moomoo import *
# pwd_unlock = '123456'
# trd_ctx = OpenSecTradeContext(filter_trdmarket=TrdMarket.HK, host='127.0.0.1', port=11111, security_firm=SecurityFirm.FUTUSECURITIES,ai_type=1)
# ret, data = trd_ctx.unlock_trade(pwd_unlock)
# if ret == RET_OK:
#     print('unlock success!')
# else:
#     print('unlock_trade failed: ', data)
# trd_ctx.close()
