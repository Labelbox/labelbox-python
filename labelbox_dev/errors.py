from labelbox_dev.entity import Entity

class BaseError(Entity):
    def __init__(self, message):
        self.message = message