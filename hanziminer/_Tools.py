# -*- encoding:utf8 -*-

import os
import psutil
import sys

class Tools:
    # Frome here : https://github.com/lovit/soynlp/tree/master/soynlp/utils
    @staticmethod
    def get_available_memory():
        """It returns remained memory as percentage"""

        mem = psutil.virtual_memory()
        return 100 * mem.available / (mem.total)

    def get_process_memory():
        """It returns the memory usage of current process"""

        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 ** 3)

    def progress_symbol():
        return ['\\', '|', '/', '―']

    # Print iterations progress
    def print_progress(iteration, total, prefix='Progress', suffix='Complete', decimals=1, bar_length=100):
        """
        Call in a loop to create terminal progress bar
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            bar_length  - Optional  : character length of bar (Int)
        """
        str_format = "{0:." + str(decimals) + "f}"
        percents = str_format.format(100 * (iteration / float(total)))
        filled_length = int(round(bar_length * iteration / float(total)))
        bar = '█' * filled_length + '-' * (bar_length - filled_length)

        sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),

        if iteration == total:
            sys.stdout.write('\n')
        sys.stdout.flush()
        # ref : https://gist.github.com/aubricus/f91fb55dc6ba5557fbab06119420dd6a
