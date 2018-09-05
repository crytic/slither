
class ChildEvent(object):
    def __init__(self):
        super(ChildEvent, self).__init__()
        self._event = None

    def set_event(self, event):
        self._event = event

    @property
    def event(self):
        return self._event
