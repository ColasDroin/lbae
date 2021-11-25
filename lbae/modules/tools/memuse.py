# Inspired from https://stackoverflow.com/questions/10848342/use-python-logging-for-memory-usage-statistics

import logging
import psutil
import os


def logmem():
    memory = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    memory_string = "MemTotal: " + str(memory)
    return "\t" + memory_string
