#### -*- coding:utf-8 -*- #######

from tulip import get_event_loop, tasks, futures
import functools
from event_loop import EventLoop


def in_loop_call(loop):
    print("IN LOOP")
    def print_msg(msg):
        return lambda msg=msg: print(msg)
    loop.call_soon(print_msg('SOON 1'))
    loop.call_later(0.6, print_msg('LATER 0.6.1'))
    loop.call_later(0.6, print_msg('LATER 0.6.2'))
    loop.call_later(0.6, print_msg('LATER 0.6.3'))
    loop.call_soon(print_msg('SOON 2'))
    loop.call_later(0, print_msg('LATER 0'))
    loop.call_soon(print_msg('SOON 3'))
    time = loop.time()
    loop.call_at(time+0.6, print_msg('AT +0.6 1'))
    loop.call_at(time+0.6, print_msg('AT +0.6 2'))
    loop.call_at(time+0.6, print_msg('AT +0.6 3'))

    # Теперь посмотрим на вложеные вызовы
    def reinclude(n, func):
        if n > 0:
            func(n)
            loop.call_soon(functools.partial(reinclude, n-1, func))
    loop.call_soon(lambda: reinclude(10, lambda n: print('SOON 4.{}'.format(n))))

    loop.call_soon(print_msg('SOON 5'))

    loop.call_later(0.9, lambda: loop.stop())


def main(loop):
    loop.call_soon(in_loop_call, loop)
    loop.run_forever()

if __name__ == "__main__":
    main(get_event_loop())
    print("-"*20)
    main(EventLoop())
