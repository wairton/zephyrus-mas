class Objectives:
    def __init__(self, data):
        self._data = data

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __getitem__(self, key):
        return self._data[key]

    def __str__(self):
        return str(self._data)

    def __repr__(self):
        return repr(self._data)

    def copy(self):
        return Objectives(self._data.copy())


class LazyObjectives:
    def __init__(self, _id, request_callback, notifier_callback, data=None):
        self._data = data
        self.id = _id
        self.request_callback = request_callback
        self.notifier_callback = notifier_callback

    @property
    def data(self):
        return self._data or self.get_data()

    def get_data(self, block=True):
        if self._data is None:
            maybe_data = self.request_callback(self.id)
            if maybe_data is None and block:
                data = self.wait_for_completion()
            else:
                data = maybe_data
            self._data = data
        return self._data

    def wait_for_completion(self):
        # TODO: oh boy, the exchange between get_data and wait_for_completion is somewhat confusing...
        event = self.notifier_callback(self.id)
        if not event.is_set():
            event.wait()
        return self.get_data(block=False)

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, key):
        return self.data[key]

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return repr(self.data)

    def copy(self):
        return LazyObjectives(self.id, self.request_callback, self.notifier_callback, self._data)
