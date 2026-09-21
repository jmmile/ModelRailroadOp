"""Desktop-owned companion lifetime; never stop a separately launched server."""

import logging
import secrets
import socket
import threading

from PySide6.QtCore import QObject, Signal, QTimer


class CompanionController(QObject):
    changed = Signal()

    def __init__(self, parent=None, port=8675):
        super().__init__(parent)
        self.port = port
        self.status = "Stopped"
        self.code = ""
        self.addresses = ""
        self.server = None
        self.thread = None
        self.error = ""
        self.timer = QTimer(self)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.poll)

    @property
    def busy(self):
        return self.thread is not None and self.thread.is_alive()

    def start(self):
        if self.busy:
            return
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Windows otherwise permits multiple listeners to share a port.
            if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            listener.bind(("0.0.0.0", self.port))
            listener.listen(128)
            self.port = listener.getsockname()[1]
        except OSError:
            listener.close()
            self.status = "Unavailable — port in use or blocked. If Companion is already open, use its console or close it and retry."
            self.code = ""
            self.changed.emit()
            return
        self.status = "Starting…"
        self.error = ""
        self.code = ""
        self.server = None
        self.thread = threading.Thread(target=self._serve, args=(listener,), daemon=True)
        self.thread.start()
        self.timer.start()
        self.changed.emit()

    def _serve(self, listener):
        try:
            import uvicorn
            from modelrailroadops.web import server as web

            web.PAIRING_CODE = f"{secrets.randbelow(1_000_000):06d}"
            web.AUTH_TOKEN = secrets.token_urlsafe(32)
            self.code = web.PAIRING_CODE
            try:
                addresses = sorted({item[4][0] for item in socket.getaddrinfo(
                    socket.gethostname(), None, socket.AF_INET
                ) if not item[4][0].startswith("127.")})
            except OSError:
                addresses = []
            self.addresses = " | ".join(f"http://{ip}:{self.port}" for ip in addresses)
            self.server = uvicorn.Server(uvicorn.Config(
                web.app, host="0.0.0.0", port=self.port, loop="asyncio",
                http="h11", ws="none", log_config=None, access_log=False,
                timeout_graceful_shutdown=5,
            ))
            self.server.run(sockets=[listener])
        except BaseException as exc:
            logging.exception("Companion server failed")
            self.error = str(exc) or type(exc).__name__
        finally:
            listener.close()

    def stop(self):
        if self.busy:
            self.status = "Stopping…"
            if self.server is not None:
                self.server.should_exit = True
            self.changed.emit()

    def poll(self):
        if self.status == "Stopping…" and self.server is not None:
            self.server.should_exit = True
        if not self.busy:
            self.timer.stop()
            self.status = f"Failed: {self.error}" if self.error else "Stopped"
            self.code = ""
        elif self.server is not None and self.server.started and self.status != "Stopping…":
            self.status = "Running"
        self.changed.emit()
