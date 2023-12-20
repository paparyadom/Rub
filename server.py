

if __name__ == '__main__':

    try:
        host, port = sys.argv[1:]
    except:
        host, port = '', 5455
    finally:
        server = Server(host, port, proto=TCD8())
    try:
        server.run()
    except KeyboardInterrupt:
        server.stop()

