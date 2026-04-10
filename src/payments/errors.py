class IdempotencyConflict(Exception):
    code = "idempotency_conflict"

    def __init__(self, key: str):
        self.key = key
        self.message = "Idempotency-Key '%s' already used with different parameters" % key
        super().__init__(self.message)
