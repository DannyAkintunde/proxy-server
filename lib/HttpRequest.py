class HTTPRequest:
    def __init__(self, raw_request):
        self.raw_request = raw_request
        self.method = None
        self.path = None
        self.http_version = None
        self.headers = {}
        self.body = ''
        
        # Parse the raw request on initialization
        self.parse_request()

    def parse_request(self):
        """Parse the raw HTTP request into components."""
        lines = self.raw_request.split('\r\n')
        
        # Parse the request line
        request_line = lines[0]
        self.method, self.path, self.http_version = request_line.split(" ")

        # Parse headers
        for line in lines[1:]:
            if line == '':  # End of headers
                break
            key, value = line.split(': ', 1)
            self.headers[key] = value

        # The body is everything after the headers
        if len(lines) > len(self.headers) + 2:
            self.body = '\r\n'.join(lines[len(self.headers) + 2:])

    def set_header(self, key, value):
        """Set a header value."""
        self.headers[key] = value

    def delete_header(self, key):
        """Delete a header if it exists."""
        if key in self.headers:
            del self.headers[key]

    def get_header(self, key, defualt=None):
        """Get a header value."""
        return self.headers.get(key, defualt)

    def to_raw_request(self):
        """Convert the object back to a raw HTTP request string."""
        request_line = f"{self.method} {self.path} {self.http_version}\r\n"
        headers = ''.join(f"{key}: {value}\r\n" for key, value in self.headers.items())
        return f"{request_line}{headers}\r\n{self.body}"

