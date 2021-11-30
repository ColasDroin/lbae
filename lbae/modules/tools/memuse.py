import psutil
import os

# ? Put this in misc ?
# for dosctring: this function has been benchmarked and takes about 0.5ms to run
def logmem():
    memory = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    memory_string = "MemTotal: " + str(memory)
    return "\t" + memory_string
