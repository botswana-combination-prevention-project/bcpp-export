class Lis(object):
    user = 'erikvw'
    password = 'jsw99Wid'
    host = 'mssql.bhp.org.bw'
    port = '1433'
    name = 'bhplab'


class Edc(object):
    """
    requires an ssh tunnel to edc.bhp.org.bw, for example:
        ssh -f django@edc.bhp.org.bw -L5001:localhost:3306 -N

        mysql -u root -p -h 127.0.0.1 -P 5001
    """
    user = 'root'
    password = 'cc3721b'
    host = '127.0.0.1'
    port = '5001'
    name = 'bhp066_master'
