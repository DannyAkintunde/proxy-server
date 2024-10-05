import logging
import threading
import ssl
import socket
import ua_generator
from ua_generator.options import Options
from lib.HttpRequest import HTTPRequest


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

port = 8080
host = '0.0.0.0'

#UAmanager = UserAgentManager()

def generate_ua():
  device = ('desktop', 'mobile')
  platform = ('windows', 'macos', 'ios', 'linux', 'android')
  browser = ('chrome', 'edge', 'firefox', 'safari')
  options = Options(weighted_versions=True)
  ua = ua_generator.generate(platform=platform, browser=browser, device=device, options=options)
  ua.headers.accept_ch('Sec-CH-UA-Platform-Version, Sec-CH-UA-Full-Version-List')
  return ua
# Create the server socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen(10)
logging.info(f"Proxy server listening at {host}:{port}")

def clean_request_headers(request):
    # Parsing the request
    parsed_request = HTTPRequest(request.decode('utf-8'))
    
    # Accessing request data
    headers = parsed_request.headers
    # Remove sensitive headers
    headers.pop("X-Forwarded-For", None)
    headers.pop("Referer", None)
    #headers.pop("Origin", None)
    headers.pop("Cookie", None)
    headers.pop("Accept-Language", None)
    headers.pop("DNT", None)
    headers.pop("Cache-Control", None)
    
    ua_headers = generate_ua().headers.get()
    ua_headers["User-Agent"] = ua_headers["user-agent"]
    del ua_headers["user-agent"]
    headers = headers | ua_headers
    
    parsed_request.headers = headers
    
    # Convert back to raw HTTP request format
    modified_request = parsed_request.to_raw_request()
    
    logging.debug(modified_request)
    
    return modified_request.encode('utf-8')


def extract_host_and_port_from_request(request):
    if not request.startswith(b'CONNECT'):
        host_start_string = request.find(b'Host: ') + len(b'Host: ')
        host_end_string = request.find(b'\r\n', host_start_string)
        host_string = request[host_start_string:host_end_string].decode('utf-8').strip()
    else:
        host_start_string = request.find(b'CONNECT ') + len(b'CONNECT ')
        host_end_string = request.find(b' HTTP/', host_start_string)
        host_string = request[host_start_string:host_end_string].decode('utf-8').strip()
    http_version_start = request.find(b'HTTP/') + len(b'HTTP/')
    http_version_end = request.find(b'\r\n', http_version_start)
    http_version = request[http_version_start:http_version_end].decode('utf-8')
    logging.info(host_string, http_version)
    webserver_pos = host_string.find('/')
    if webserver_pos == -1:
        webserver_pos = len(host_string)
    
    port_pos = host_string.find(':')
    if port_pos == -1 or webserver_pos < port_pos:
        port = 80
        host = host_string[:webserver_pos]
    else:
        port = int(host_string[(port_pos + 1):webserver_pos])
        host = host_string[:port_pos]

    return host, port, http_version

def handle_client_request(client_socket):
    logging.info("Received request\n---")
    request = b''

    # Read the request from the client
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
            request += data
            if b'\r\n\r\n' in request:  # Basic end of headers check
                break
        except Exception as e:
            logging.error(f"Error receiving data: {e}")
            break

    if not request:
        client_socket.close()
        return
    logging.info(request)

    # Check if the request is a CONNECT method
    if request.startswith(b'CONNECT'):
      try:
          host, port, version = extract_host_and_port_from_request(request)
          logging.info(f"Establishing tunnel to {host}:{port}")
  
          # Send response indicating the connection has been established
          res = f"HTTP/{version} 200 Connection established\r\nProxy-Connection: keep-alive\r\n\r\n"
          client_socket.send(res.encode('utf-8'))
          
          # Create a socket to connect to the destination server
          destination_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          destination_socket.connect((host, port))
  
          # Create SSL context for the client-side (proxy to server)
          client_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)  # Use modern TLS version
          client_context.check_hostname = True  # Enable hostname check for the server
          client_context.verify_mode = ssl.CERT_REQUIRED  # Verify the server certificate
          client_context.load_default_certs()  # Load system default CA certificates
  
          # Set the SSL ciphers to ensure compatibility
          client_context.set_ciphers('ECDHE+AESGCM:!ECDSA')  # Modern ciphers only
          ssl_socket = client_context.wrap_socket(destination_socket, server_hostname=host)
          ssl_socket.do_handshake()

          # Create a separate SSL context for the server-side (proxy to client)
          server_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)  # Server side
          server_context.check_hostname = False  # No hostname check for clients
          server_context.verify_mode = ssl.CERT_NONE  # No client certificate validation
          # Load a valid certificate and private key (you may need to generate these)
          server_context.load_cert_chain(certfile='certificate.pem', keyfile='private_key.pem')

          # Set modern cipher suites
          server_context.set_ciphers('ECDHE+AESGCM:!ECDSA')  # Use strong ciphers

          # Wrap the client socket with the server-side SSL context
          client_ssl_socket = server_context.wrap_socket(client_socket, server_side=True)

          ssl_socket.do_handshake()
          client_request = b''
          while True:
              logging.info("fetching client data")
              # Receive data from client
              client_data = client_ssl_socket.recv(4096)
              if not client_data:
                break
              client_request += client_data
              if b'\r\n\r\n' in client_request:  # Basic end of headers check
                  break
              
          logging.debug("client request: ", clean_request_headers(client_request).decode('utf-8'))
  
          # Relay data between client and destination
          ssl_socket.send(clean_request_headers(client_request))
          while True:
              # Receive response from the destination
              server_data = ssl_socket.recv(4096)
              #print(server_data)
              if not server_data:
                  break
              
              client_ssl_socket.send(server_data)
  
      except Exception as e:
          logging.error(f"Error establishing connection to {host}:{port} - {e}")
          
      finally:
          try:
              ssl_socket.close()
          except:
              pass
          try:
              client_ssl_socket.close()
          except:
              pass


    else:
        # Handle regular HTTP requests
        host, port, version = extract_host_and_port_from_request(request)
        try:
            destination_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            destination_socket.connect((host, port))
            destination_socket.sendall(clean_request_headers(request))

            while True:
                data = destination_socket.recv(4096)
                if not data:
                    break
                client_socket.sendall(data)

        except Exception as e:
            logging.error(f"Error connecting to {host}:{port} - {e}")

        finally:
            destination_socket.close()
            client_socket.close()

# Accept incoming requests
def main():
    while True:
      client_socket, addr = server.accept()
      logging.info(f"Accepted request from {addr[0]}:{addr[1]}")
      client_handler = threading.Thread(target=handle_client_request, args=(client_socket,))
      client_handler.start()

if __name__ == '__main__':
  main()
