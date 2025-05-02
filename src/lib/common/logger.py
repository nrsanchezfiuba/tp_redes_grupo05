class Logger:
    def __init__(
        self, verbose: bool = False, quiet: bool = False, log_file: str = ""
    ) -> None:
        self.log_file = log_file
        self.verbose = verbose
        self.quiet = quiet

    def info(self, message: str) -> None:
        msg = f"[INFO] {message}"
        if self.log_file:
            self._log_to_file(msg)
        else:
            self._log_to_console(msg)

    def debug(self, message: str) -> None:
        if not self.verbose:
            return
        msg = f"[DEBUG] {message}"
        if self.log_file:
            self._log_to_file(msg)
        else:
            self._log_to_console(msg)

    def warning(self, message: str) -> None:
        if not self.verbose:
            return
        msg = f"[WARNING] {message}"
        if self.log_file:
            self._log_to_file(msg)
        else:
            self._log_to_console(msg)

    def error(self, message: str) -> None:
        msg = f"[ERROR] {message}"
        if self.log_file:
            self._log_to_file(msg)
        else:
            self._log_to_console(msg)

    def _log_to_console(self, message: str) -> None:
        if self.quiet:
            return
        print(message)

    def _log_to_file(self, message: str) -> None:
        if self.quiet:
            return
        with open(self.log_file, "a") as f:
            f.write(message + "\n")
