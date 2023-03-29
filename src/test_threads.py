# import thread
from threading import Thread
import time


class StopCondition():
	def __init__(self):
		self.is_stopped = False

sc = StopCondition()

# stop_condition = False

def print_time(thread_name, delay, stop_condition):
	count = 0
	start = time.time()
	while count < 5 and not stop_condition.is_stopped:
		time.sleep(delay)
		if count > 2:
			stop_condition.is_stopped = True
		count += 1
		print(f"{thread_name} - {round(time.time()-start, 2)}")

# thread.start_new_thread(print_time, ("t1", 0.5))
# thread.start_new_thread(print_time, ("t1", 2))

thread_1 = Thread(target=print_time, args=("t1", 0.01, sc))
thread_2 = Thread(target=print_time, args=("t2", 3, sc))

thread_1.start()
thread_2.start()

thread_1.join()
thread_2.join()