import os 
from .HttpRequest import HTTPRequest

BASE_DIR = "web"
ALLOWED_HOSTS = [".bot-hosting.net", "127.0.0.1"]

def send_404_response(client_socket):
    body = '<h1>File not found</h1>'
    response = 'HTTP/1.1 404 Not Found\r\n'
    response += 'Content-Type: text/html\r\n'
    response += f'Content-Length: {len(body)}\r\n'
    response += '\r\n'  # End of headers
    response += body  # Body content (HTML)

    # Send the response to the client
    client_socket.sendall(response.encode('utf-8'))

def send_500_response(client_socket, e=None):
    body = '<h1>500 Internal Server Error</h1><p>Something went wrong on the server.</p>'
    if e:
      body += '<p>Error: {}</p>'.format(repr(e))
    response = 'HTTP/1.1 500 Internal Server Error\r\n'
    response += 'Content-Type: text/html\r\n'
    response += f'Content-Length: {len(body)}\r\n'
    response += '\r\n'  # End of headers
    response += body  # Body content (HTML)

    # Send the response to the client
    client_socket.sendall(response.encode('utf-8'))

def send_200_html_response(client_socket, content):
    # Build HTTP response
    response = 'HTTP/1.1 200 OK\r\n'
    response += 'Content-Type: text/html\r\n'
    response += 'Content-Length: {}\r\n'.format(len(content))
    response += '\r\n'  # Separate headers from content
    response += content
    
    # send response
    client_socket.sendall(response.encode('utf-8'))

def serve_html_file(client_socket, html_file):
  try:
    if not os.path.exists(html_file):
      send_404_response(client_socket)
      return
    
    with open(html_file, 'r') as page:
      content = page.read()
      send_200_html_response(client_socket, content)
    
  except Exception as e:
    send_500_response(client_socket, e)

def http_server(request, client_socket, logger) -> bool:
  request = request.decode('utf-8')
  request_obj = HTTPRequest(request)
  
  host = request_obj.get_header("Host", defualt=[])
  is_allowed = False
  
  for a_host in ALLOWED_HOSTS:
    if a_host in host: is_allowed = True
  
  if request_obj.method and request_obj.path.startswith('/') and is_allowed:
    if request_obj.path == '/':
      request_obj.path = 'index.html'
    path = os.path.join(BASE_DIR, request_obj.path.lstrip('/'))
    logger.info('GET {}'.format(request_obj.path))
    serve_html_file(client_socket, path)
    return True
  else:
    return False