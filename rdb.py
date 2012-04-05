import errno
import socket
import sys

from pdb import Pdb

RDB_HOST = "127.0.0.1"
RDB_PORT = 6910

class Rdb(Pdb):
    me = "Remote Debugger"
    _prev_outs = None
    _sock = None

    def __init__(self, host=RDB_HOST, port=RDB_PORT,
            port_search_limit=100, port_skew=+0):
        self.active = True
        try:
            from multiprocessing import current_process
            _, port_skew = current_process().name.split('-')
        except (ImportError, ValueError):
            pass
        port_skew = int(port_skew)

        self._prev_handles = sys.stdin, sys.stdout
        this_port = None
        for i in xrange(port_search_limit):
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            this_port = port + port_skew + i
            try:
                self._sock.bind((host, this_port))
            except socket.error, exc:
                if exc.errno in [errno.EADDRINUSE, errno.EINVAL]:
                    continue
                raise
            else:
                break
        else:
            raise Exception(
                "%s: Could not find available port. Please set using "
                "environment variable RDB_PORT" % (self.me, ))

        self._sock.listen(1)
        me = "%s:%s" % (self.me, this_port)
        context = self.context = {"me": me, "host": host, "port": this_port}
        print("%(me)s: Please telnet %(host)s %(port)s."
              "  Type `exit` in session to continue." % context)
        print("%(me)s: Waiting for client..." % context)

        self._client, address = self._sock.accept()
        context["remote_addr"] = ":".join(map(str, address))
        print("%(me)s: In session with %(remote_addr)s" % context)
        self._handle = sys.stdin = sys.stdout = self._client.makefile("rw")
        Pdb.__init__(self, completekey="tab", stdin=self._handle,
            stdout=self._handle)

    def _close_session(self):
        self.stdin, self.stdout = sys.stdin, sys.stdout = self._prev_handles
        self._handle.close()
        self._client.close()
        self._sock.close()
        self.active = False
        print("Session %(remote_addr)s ended." % self.context)

    def do_continue(self, arg):
        self._close_session()
        self.set_continue()
        return 1
    do_c = do_cont = do_continue

    def do_quit(self, arg):
        self._close_session()
        self.set_quit()
        return 1
    do_q = do_exit = do_quit

    def post_mortem(self, frame):
        self.reset()
        self.interaction(None, frame)

    def set_quit(self):
        # this raises a BdbQuit exception that we are unable to catch.
        sys.settrace(None)
