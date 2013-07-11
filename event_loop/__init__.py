######### Make a package #######

import collections
import heapq
import time


class EventLoop(object):

    def __init__(self):
        self._stop = False
        self._scheduled = []
        self._ready = collections.deque()

    def run_forever(self):
        while not self._stop:
            self._run_once()

    def time(self):
        return time.time()

    def call_soon(self, func, *args):
        self._ready.append(TimerHandle(0, func, args))

    def call_later(self, delay, func, *args):
        self.call_at(delay+self.time(), func, *args)

    def call_at(self, time, func, *args):
        heapq.heappush(self._scheduled, TimerHandle(time, func, args))

    def process_events(self, events):
        pass

    def stop(self):
        self._stop = True

    def _select(self, timeout):
        time.sleep(timeout)

    def _run_once(self, timeout=0.0001):
        if self._ready:
            timeout = 0
        elif self._scheduled:
            when = self._scheduled[0]._when
            wait = max(when-self.time(), 0)
            timeout = min(wait, timeout)

        self.process_events(self._select(timeout))

        now = self.time()
        while self._scheduled:
            handle = self._scheduled[0]
            if handle._when > now:
                break
            handle = heapq.heappop(self._scheduled)
            self._ready.append(handle)

        ntodo = len(self._ready)
        for i in range(ntodo):
            handle = self._ready.popleft()
            handle._run()


class TimerHandle:
    """ Took from toolip for heapq to work """

    def __init__(self, when, callback, args):
        assert when is not None
        self._callback = callback
        self._args = args
        self._cancelled = False

        self._when = when

    def cancel(self):
        self._cancelled = True

    def _run(self):
        try:
            self._callback(*self._args)
        except Exception:
            raise

    def __repr__(self):
        res = 'TimerHandle({}, {}, {})'.format(self._when,
                                               self._callback,
                                               self._args)
        if self._cancelled:
            res += '<cancelled>'

        return res

    def __hash__(self):
        return hash(self._when)

    def __lt__(self, other):
        return self._when < other._when

    def __le__(self, other):
        if self._when < other._when:
            return True
        return self.__eq__(other)

    def __gt__(self, other):
        return self._when > other._when

    def __ge__(self, other):
        if self._when > other._when:
            return True
        return self.__eq__(other)

    def __eq__(self, other):
        if isinstance(other, TimerHandle):
            return (self._when == other._when and
                    self._callback == other._callback and
                    self._args == other._args and
                    self._cancelled == other._cancelled)
        return NotImplemented

    def __ne__(self, other):
        equal = self.__eq__(other)
        return NotImplemented if equal is NotImplemented else not equal
