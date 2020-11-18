class ActionError(Exception):
    """Base class for action exceptions."""
    def __init__(self, message):
        self.message = message

class Action:
    "Base class for specific actions."
    def __init__(self, config):
        pass

    def execute(self):
        pass