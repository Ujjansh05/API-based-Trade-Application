import inspect
from tradingapi_a.mconnect import MConnect

methods = [m[0] for m in inspect.getmembers(MConnect, predicate=inspect.isfunction)]
for m in methods:
    print(m)
