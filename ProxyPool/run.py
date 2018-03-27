from ProxyPool.proxyPool.api import app
from ProxyPool.proxyPool.schedule import Schedule

def main():

    s = Schedule()
    s.run()
    app.run()




if __name__ == '__main__':
    main()