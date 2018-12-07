import time
import random
import display_utils as du

class Idler():

    def __init__(self, center, output_dims, eye_dims):
        self._CENTER = center
        self._idle = False
        self._idle_count = 1
        self._idle_list = ['roll_idle', 'random_idle']
        self._idle_func = self._idle_list[0]
        self._idle_watch_start = time.time()
        #set time that idle condition must stay true to
        #trigger an idle behavior
        self._IDLE_TIME_TRIGGER = 7
        self._idle_position = self._CENTER
        self._blink_count = 0
        self._OUTPUT_WIDTH, self._OUTPUT_HEIGHT = output_dims
        self._EYE_WIDTH, self._EYE_HEIGHT = eye_dims
        self._IDLE_RUN_TIME = 5
        self._prev_idle_time = 0

    def is_idle(self):
        return self._idle

    def set_idle(self, idle):
        self._idle = idle

    def get_idle_count(self):
        return self._idle_count

    def get_idle_watch_start(self):
        return self._idle_watch_start

    def set_idle_watch_start(self, current_time):
        self._idle_watch_start = current_time

    def get_idle_time_trigger(self):
        return self._IDLE_TIME_TRIGGER

    def begin_idle(self):
        self._idle = True
        self._idle_watch_start = time.time()

        which_idle = random.randint(0, len(self._idle_list) - 1)
        self._prev_idle_time = self._idle_watch_start
        self._idle_func = self._idle_list[which_idle]
        self._idle_position = self._CENTER

    def run_idle(self, current_time, smoothed_position):
        if current_time - self._idle_watch_start > self._IDLE_RUN_TIME:
            self._idle = False
            self._idle_watch_start = current_time
            return smoothed_position

        elif self._idle_func == 'random_idle':
            if current_time - self._prev_idle_time > .75:
                random_x = random.randint(0, self._OUTPUT_WIDTH - self._EYE_WIDTH)
                random_y = random.randint(0, self._OUTPUT_HEIGHT - self._EYE_HEIGHT)
                self._prev_idle_time = time.time()
                self._idle_position = (random_x, random_y)
            smoothed_position = du.avg_center(self._idle_position, smoothed_position, 1/2)
            return smoothed_position


        elif self._idle_func == 'roll_idle':
            smoothed_position = du.avg_center(self._idle_position, smoothed_position)
            dt = current_time - self._prev_idle_time

            if smoothed_position[0] >= self._OUTPUT_WIDTH or (dt < 1.3 and dt > 1):
                smoothed_position = du.avg_center((0 - self._EYE_WIDTH, self._OUTPUT_HEIGHT/2 - self._EYE_HEIGHT/2), (0 - self._EYE_WIDTH, self._OUTPUT_HEIGHT/2 - self._EYE_HEIGHT/2))
                return smoothed_position
                
            elif smoothed_position[0] > 0 - self._EYE_WIDTH and smoothed_position[0] < 0:
                smoothed_position = du.avg_center(self._CENTER, smoothed_position, 1/16)
                return smoothed_position
                
            elif dt > .5 and smoothed_position[0] <= self._OUTPUT_WIDTH + self._EYE_WIDTH*2 and smoothed_position[0] >= self._CENTER[0] - 10 and dt < 1.25:
                smoothed_position = du.avg_center((self._OUTPUT_WIDTH + self._EYE_WIDTH*2, self._OUTPUT_HEIGHT/2 - self._EYE_HEIGHT/2), smoothed_position, 1/16)
                return smoothed_position
                
            else:
                smoothed_position = du.avg_center(self._CENTER, smoothed_position, 1/16)
                return smoothed_position
        '''
        elif self._idle_func == 'blink_idle':
            smoothed_position = du.avg_center(self._CENTER, smoothed_position, 1/16)
            if not blinking and self._blink_count == 0:
                blinking = True
                max_blink_count = random.randint(0, 1)
                start_blink_idle = time.time()
                self._blink_count += 1
            elif not blinking and blink_count <= max_blink_count:
                blinking = True
                self._blink_count += 1
            elif not blinking and current_time - start_blink_idle > 3:
                self._blink_count = 0

            return smoothed_position
        '''