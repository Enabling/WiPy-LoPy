import usocket
import ujson
import gc

try:
    import ussl
    SUPPORT_SSL = True
except ImportError:
    ussl = None
    SUPPORT_SSL = False

SUPPORT_TIMEOUT = hasattr(usocket.socket, 'settimeout')
CONTENT_TYPE_JSON = 'application/json'
CONTENT_TYPE_BINARY = 'application/binary'

gc.enable()


class Response(object):
    def __init__(self, status_code, status_msg, raw, contLen):
        self.status_code = status_code
        self.status_msg = status_msg.decode('utf-8').strip('\r\n')
        self.raw = raw
        self._content = False
        self._contLen = contLen
        self.encoding = 'utf-8'

    @property
    def content(self):
        if self._content is False and self._contLen != 0:
            if self._contLen > 0:
                self._content = self.raw.recv(self._contLen)
#            self.raw.close()
#            self.raw = None
            else: #chunked  : chucnksize - chunk (and repeat)
                self._content = bytearray()
                #print("Getting the chunks ..")
                keepReading = True
                while(keepReading):
                    #print("fetching chunksize")
                    line = self.raw.readline()
                    #print(line)
                    chunkSize = int(line.decode('utf-8'), 16)
                    #print("Receiving chunk of size = ", chunkSize)
                    self._content.extend(self.raw.recv(chunkSize))
                    #print("consuming trailing newline chars")
                    line = self.raw.readline()
                    #print(line)
                    keepReading = chunkSize > 0
            
#        else:
#            print("NO DATA ??!!")
 
 
        return self._content

    @property
    def text(self):
        self.content
        content = self._content

        return str(content, self.encoding) if content else ''

    def close(self):
        if self.raw is not None:
            self._content = None
            self.raw.close()
            self.raw = None
            gc.collect()
 

    def json(self):
        if self.text:
            return ujson.loads(self.text)
        else:
            return {}

    def raise_for_status(self):
        if 400 <= self.status_code < 500:
            raise OSError('Client error: %s %s' % (self.status_code, self.status_msg ))
        if 500 <= self.status_code < 600:
            raise OSError('Server error: %s %s' % (self.status_code, self.status_msg ))

    def getStatus(self):
        return (self.status_code, self.status_msg)
        
# Adapted from upip
def request(method, url, json=None, textMsg=None, binary=None, timeout=None, headers=None,  contentType='application/text',  debug = False):
    if debug: print(method, url)
    urlparts = url.split('/', 3)
    proto = urlparts[0]
    host = urlparts[2]
    urlpath = '' if len(urlparts) < 4 else urlparts[3]

    if proto == 'http:':
        port = 80
    elif proto == 'https:':
        port = 443
    else:
        raise OSError('Unsupported protocol: %s' % proto[:-1])

    if ':' in host:
        host, port = host.split(':')
        port = int(port)

    if json is not None:
        content = ujson.dumps(json)
        content_type = CONTENT_TYPE_JSON
    elif textMsg is not None:
        content = textMsg
        content_type = contentType
    elif binary is not None:
        content = binary
        content_type = CONTENT_TYPE_BINARY
    else:
        content = None


    ai = usocket.getaddrinfo(host, port)
    addr = ai[0][4]
    
    
    #sock = connect(proto, addr, timeout)
    

    try:
        sock = connect(proto, addr, timeout)
    except OSError as oerr:
        print ("OSError : %s" % oerr)
        raise oerr
#        try:
#            sock = connect(proto, addr, timeout)
#        except OSError as oerr:
#            print (oerr)
#            raise oerr
#    
    
    
    # DUMP TO CONSOLE DEBUG
    http_verb = '%s /%s HTTP/1.1'  % (method, urlpath)
    http_content_type = '' if content is None else 'Content-Type: %s' % content_type
    http_host = 'Host: %s' % (host)
    http_headers = ''
    if headers is not None:
        http_headers = ''.join(': '.join(_) for _ in headers.items())

    http_content_length = 'Content-Length: %s' % (len(content) if not content is None else 0)

    if content is None:
        sending = '{0}\r\n{1}\r\n{2}\r\n\r\n'.format(http_verb, http_host,  http_headers)
    else:
        sending = '{0}\r\n{1}\r\n{2}\r\n{3}\r\n{4}\r\n\r\n'.format(http_verb, http_content_type, http_host, http_content_length, http_headers)

        
    if debug: 
        print(sending)
        if not content is None:
            print(content)
    
    

    # START SENDING
    sock.send(sending)
    if not content is None:
        sock.send(content)

    
    l = sock.readline()
    if debug: print (l)
    protover, status, msg = l.split(None, 2)

    # Skip headers
    l = sock.readline()
    if debug: print (l)
    contentlength = 0
    while l != b'\r\n':
        l = sock.readline()
        if debug: print (l)
        if l.startswith(b'Content-Length:'):
            dummy, contentlength = l.split(None, 1)
            if debug: print("Body size = " ,  int(contentlength))
        if l.startswith(b'Transfer-Encoding: chunked'):
            if contentlength == 0:
                contentlength = -1
                if debug: print("CHUNKED DATA !!")


    return Response(int(status), msg, sock, int( contentlength))

def connect(protocol, address,  timeout):

    if protocol == 'https:':
        sock = usocket.socket(usocket.AF_INET,  usocket.SOCK_STREAM, usocket.IPPROTO_SEC)
    else:
        sock = usocket.socket()

    if timeout is not None:
        assert SUPPORT_TIMEOUT, 'Socket does not support timeout'
        sock.settimeout(timeout)

    if protocol == 'https:':
        assert SUPPORT_SSL, 'HTTPS not supported: could not find ussl'
#        sock = ussl.wrap_socket(sock, ssl_version=ussl.PROTOCOL_TLSv1)
        sock = ussl.wrap_socket(sock)
        
    sock.connect(address)
    
    return sock

def get(url, **kwargs):
    return request('GET', url, **kwargs)

def post(url, **kwargs):
    return request('POST', url, **kwargs)

def put(url, **kwargs):
    return request('PUT', url, **kwargs)
