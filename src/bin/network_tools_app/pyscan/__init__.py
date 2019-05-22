import socket
import sys
import threading, Queue

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

def port_scan(host, start, stop, thread_count=DEFAULT_THREAD_LIMIT, callback=None):
    to_scan = Queue.Queue()
    scanned = Queue.Queue()

    scanners = [Scanner(to_scan, scanned) for i in range(thread_count)]
    for scanner in scanners:
        scanner.start()

    host_ports = [(host, port) for port in xrange(start, stop + 1)]
    for host_port in host_ports:
        to_scan.put(host_port)

    results = {}
    for host, port in host_ports:
        while (host, port) not in results:
            nhost, nport, nstatus = scanned.get()
            results[(nhost, nport)] = nstatus
        status = results[(host, port)]

        # Run the callback if one is present
        if callback:
            callback(host, port, status)

        if status != CLOSED_STATUS:
            print '%s:%d %s' % (host, port, status)

    return results

