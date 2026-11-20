class InputError(ValueError):
    def __init__(self, code, status=422):
        super().__init__(code)
        self.code = code
        self.status = status
