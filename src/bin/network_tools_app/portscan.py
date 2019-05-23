import socket
import sys
import threading, Queue
from collections import OrderedDict
import parseintset

DEFAULT_THREAD_LIMIT = 100
CLOSED_STATUS = 'closed'
OPEN_STATUS = 'open'

class Scanner(threading.Thread):
    def __init__(self, input_queue, output_queue):
        threading.Thread.__init__(self)
        self.setDaemon(1)

        # These are the scan queues
        self.input_queue = input_queue
        self.output_queue = output_queue

    def run(self):
        # This loop will exit when the input_queue generates an exception because all of the threads are complete
        while 1:
            host, port = self.input_queue.get()

            # Make the socket for performing the scan
            sock_instance = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            try:
                # Connect to the host via TCP
                sock_instance.connect((host, port))
            except socket.error:
                # Note that it is in the closed state
                self.output_queue.put((host, port, CLOSED_STATUS))
            else:
                # Note that it is in the open state
                self.output_queue.put((host, port, OPEN_STATUS))
                sock_instance.close()

def port_scan(host, ports, thread_count=DEFAULT_THREAD_LIMIT, callback=None):
    # Parse the ports if necessary
    if isinstance(ports, (str, unicode)):
        parsed_ports = parseintset.parseIntSet(ports)
    else:
        parsed_ports = ports

    # Setup the queues
    to_scan = Queue.Queue()
    scanned = Queue.Queue()

    # Prepare the scanners
    scanners = [Scanner(to_scan, scanned) for i in range(thread_count)]
    for scanner in scanners:
        scanner.start()

    # Create the list of host ports to scan
    host_ports = [(host, port) for port in parsed_ports]
    for host_port in host_ports:
        to_scan.put(host_port)

    # This will store the list of successfully executed host/port combiations
    results = {}

    # This will contain the resulting data
    data = []

    for host, port in host_ports:
        while (host, port) not in results:
            # Get the queued thread: this will block if necessary
            scanned_host, scanned_port, scan_status = scanned.get()

            # Log that that we performed the scan
            results[(scanned_host, scanned_port)] = scan_status

            # Append the data
            data.append(OrderedDict({
                'dest' : scanned_host,
                'port' : 'TCP\\' + str(scanned_port),
                'status': scan_status
            }))

        # Run the callback if one is present
        if callback is not None:
            callback(scanned_host, scanned_port, scan_status)

    return data

