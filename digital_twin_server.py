# Python 3 server example
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os

hostName = "localhost"
serverPort = 2233


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(
            bytes(
                "<html><head><title>Simple Server</title></head><body>This is the Digital Twin server</body></html>",
                "utf-8",
            )
        )

    def do_POST(self):
        self.data_string = self.rfile.read(int(self.headers["Content-Length"]))
        # print data_string on file named data_string_out.txt
        with open("data_string_out.txt", "w") as f:
            f.write(self.data_string.decode("utf-8"))
        self.send_response(200)
        self.end_headers()
        data = json.loads(self.data_string)
        if not "kind" in data.keys():
            return
        kind = data["kind"]
        if kind == "source_code":
            do_source_code(data["code"])
        elif kind == "traffic_data":
            do_traffic_data(data["traffic"], data["serial_number"])
        print("data: ",data)

def do_source_code(code):
    # actions to perform when source code is sent
    # save code on file named code.py
    with open("network.py", "w") as f:
        f.write(code)
    # execute code.py through a syscall
    os.system("python3 network.py")

def do_traffic_data(traffic_data,serial_number):
    # actions to perform when traffic data is sent
    # save data on file named [serial_number].txt inside the traffic folder
    with open(f"traffic_2/{serial_number}.txt", "w") as f:
        f.write(traffic_data)

if __name__ == "__main__":
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
