from check_home_flow import CheckHomeFlowThread
from check_stock import CheckStockThread

if __name__ == '__main__':
    check_stock_thread = CheckStockThread('config.ini')

    check_home_flow_thread = CheckHomeFlowThread('config.ini')

    check_stock_thread.start()
    check_home_flow_thread.start()
