import os
import sys
import random
import traceback
import time

class Pool:
    """
    A Pool class that uses processes.  It does not rely on pickling
    the function, so it can be used on instance methods.  The
    disadvantage is that the return value can only be an integer from
    0 to 255.
    """

    def __init__(self, n):
        self.max_procs = n
        self.num_running = 0
        self.procs = {}
        self.stop_on_fail = False
    
    def launch(self, func, arg, index=True):
        pid = os.fork()
        if pid == 0:
            rv = func(arg)
            if isinstance(rv, int):
                rv %= 256
            else:
                rv = 0
            os._exit(rv)
        else:
            self.procs[pid] = index
            self.num_running += 1

    def wait(self):
        pid, status = os.wait()
        status /= 256
        index = self.procs[pid]
        del(self.procs[pid])
        self.num_running -= 1
        if isinstance(index, int):
            self.statuses[index] = status
        if self.stop_on_fail and status != 0:
            raise Exception("proc %s exit code %s" % 
                            (index, status))
        return index, status

    def init_statuses(self, n):
        self.statuses = [None] * n

    def wait_all(self):
        while self.num_running > 0:
            yield self.wait()

    def run(self, func, args, stop_on_fail=False):
        self.init_statuses(len(args))
        self.stop_on_fail = stop_on_fail
        for index, arg in enumerate(args):
            while self.num_running >= self.max_procs:
                self.wait()
            self.launch(func, arg, index=index)
        for dummy in self.wait_all():
            pass
        return self.statuses


class PoolWrapper:
    """
    A wrapper to Pool, which uses the filesystem to gather back 
    stdout and exception information as well as the return statuses.

    Passes a collated set of outputs to the logger, and if any of the 
    processes raises an exception then raises a exception with the 
    collated exception messages.
    """
    
    def __init__(self, nprocs, filename_stem = None, log_func = None):
        self.nprocs = nprocs
        self.pool = Pool(nprocs)
        if filename_stem == None:
            filename_stem = "/tmp/proc_output.%s.%s" % (
                os.getpid(), random.randint(0, 100000))
        self.filename_stem = filename_stem
        if log_func == None:
            log_func = self._default_logger
        self.log_func = log_func
        
    def _default_logger(self, msg):
        print msg

    def _output_file(self, index):
        return "%s.out_%d" % (self.filename_stem, index)

    def _exception_file(self, index):
        return "%s.exc_%d" % (self.filename_stem, index)

    def _remove(self, fn):
        if os.path.exists(fn):
            os.remove(fn)

    def _subproc_runner(self, func, args_with_index):
        index, args = args_with_index
        out_file = self._output_file(index)
        exc_file = self._exception_file(index)
        fd_out = os.open(out_file, os.O_WRONLY | os.O_CREAT)
        os.dup2(fd_out, 1)
        os.dup2(fd_out, 2)
        self._remove(exc_file)
        self._timestamp("Start time")
        try:            
            rv = func(args)
        except:     
            exc_type, exc_val, tb = sys.exc_info()
            rv = 255
            fh_exc = open(exc_file, "w")
            for line in [ str(exc_val) + "\n" ] + traceback.format_tb(tb):
                fh_exc.write(line)
            fh_exc.close()
        self._timestamp("Finish time")
        print "Return status %s" % rv            
        sys.stdout.flush()
        os.close(fd_out)
        return rv

    def _timestamp(self, label):
        print label, " ", time.asctime()

    def _collect_outputs(self, n):
        return self._collect_all_file_contents(n, self._output_file)

    def _collect_exceptions(self, n):
        return self._collect_all_file_contents(n, self._exception_file)

    def _collect_all_file_contents(self, n, func):
        return [self._collect_file_contents(i, func) for i in range(n)]
        
    def _collect_file_contents(self, i, func):
        fname = func(i)
        if not os.path.exists(fname):
            return None
        f = open(fname)
        answer = f.read()
        f.close()
        os.remove(fname)
        return answer

    def run(self, func, args, raise_exception=True):
        num = len(args)
        rvs = self.pool.run(lambda arg: self._subproc_runner(func, arg),
                            list(enumerate(args)))
        outputs = self._collect_outputs(num)
        for i, output in enumerate(outputs):
            self.log_func("Output from process %s:" % i)
            for line in output.split("\n"):
                self.log_func("    %s" % line)

        all_exc_msgs = ""
        num_exc = 0
        for i, exc_msg in enumerate(self._collect_exceptions(num)):
            if exc_msg:
                num_exc += 1
                all_exc_msgs += "    Exception from process %s:\n" % i
                for line in exc_msg.split("\n"):
                    all_exc_msgs += "       %s\n" % line
        
        if raise_exception and all_exc_msgs:
            summary = "%s out of %s processes raised an exception:" % (
                num_exc, num)
            raise Exception(summary + "\n\n" + all_exc_msgs)

        return rvs, all_exc_msgs


if __name__ == '__main__':

    import time
    import logging
   
    class Foo:

        def __init__(self, x):
            self.x = x

        def mult(self, y):
            # a sleep to prove that 
            # it didn't run sequentially
            time.sleep(1)
            print "Hello it is %s" % y
            if y in (40, 56):
                raise Exception("we don't like %s" % y)
            return self.x * y

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    p = PoolWrapper(25, log_func = logging.info)
    f = Foo(2)
    print p.run(f.mult, range(20, 70))
