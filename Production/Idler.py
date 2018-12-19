import time
import random
import display_utils as du

class Idler():
    """
    This class creates an object that controls idle behavior for the eye

    Attributes
    ----------
    _CENTER: tuple of ints
        Center of the output display

    _idle: boolean
        Flag that denotes if the eye is idle or not

    _idle_list: list of strings
        List containing string names of idle behaviors

    _idle_func: str
        String chosen out of _idle_list for which idle behavior to perform

    _idle_watch_start: float
        Time since the eye has been idling

    _IDLE_TIME_TRIGGER: float
        Time eye must be idle before idle behavior will begin

    _idle_position: tuple of ints
        Position of eye during idle

    _OUPUT_WIDTH: int
        Width of the output display for the idle class to use

    _OUPUT_HEIGHT: int
        Height of the output display for the idle class to use

    _EYE_WIDTH: int
        Width of the eye for the idle class to use

    _EYE_HEIGHT: int
        Height of the eye for the idle class to use

    _IDLE_RUN_TIME: float
        How long to run any of the idle behaviors

    _prev_idle_time: float
        Timer used internally to the Idle class to control the sequence of idle behaviors



    Methods
    -------
    is_running_idle()
        Returns a boolean as to whether or not the eye is running an idle behavior

    set_running_idle(idle)
        Used to set the self._idle parameter to True (is running idle behavior)
        or False (is not idling)

    get_idle_watch_start()
        Returns the time since the eye has been in an idle state

    set_idle_watch_start(current_time)
        Sets the self._idle_watch_start parameter to the current time
        (thus resetting the timer)

    get_idle_time_trigger()
        Returns the number of seconds the eye must be idle before starting an
        idle behavior

    begin_idle()
        initializes values for idling and picks an idle behavior to perform from the
        list of possible behaviors

    run_idle()
        run the selected idle behavior
    """

    def __init__(self, center, output_dims, eye_dims):
        """
        Creates a new Idler object to control idle behavior for the eye

        Parameters
        ----------
        center: tuple of ints
            Center of the output image

        output_dims: tuple of ints
            Resolution of output display

        eye_dims: tuple of ints
            Resolution of the eye image
        """

        self._CENTER = center
        self._idle = False
        self._idle_list = ['roll_idle', 'random_idle']
        self._idle_func = self._idle_list[0]
        self._idle_watch_start = time.time()
        #set time that idle condition must stay true to
        #trigger an idle behavior
        self._IDLE_TIME_TRIGGER = 7.0
        self._idle_position = self._CENTER
        #blink idle will work if the Idle class can request a blink
        #from the BlinkSprite class from main_control.
        #self._blink_count = 0
        self._OUTPUT_WIDTH, self._OUTPUT_HEIGHT = output_dims
        self._EYE_WIDTH, self._EYE_HEIGHT = eye_dims
        self._IDLE_RUN_TIME = 5.0
        self._prev_idle_time = 0.0

    def is_running_idle(self):
        return self._idle

    def set_running_idle(self, idle):
        self._idle = idle

    def get_idle_watch_start(self):
        return self._idle_watch_start

    def set_idle_watch_start(self, current_time):
        self._idle_watch_start = current_time

    def get_idle_time_trigger(self):
        return self._IDLE_TIME_TRIGGER

    def begin_idle(self):
        """Initializes all necessary information to run an idle behavior"""
        self._idle = True
        self._idle_watch_start = time.time()

        which_idle = random.randint(0, len(self._idle_list) - 1)
        self._prev_idle_time = self._idle_watch_start
        self._idle_func = self._idle_list[which_idle]
        self._idle_position = self._CENTER

    def run_idle(self, current_time, smoothed_position):
        """
        Run idle behavior selected in 'begin_idle()'

        Parameters
        ----------
        current_time: float
            The current time in seconds since the epoch; used to mark current time in animation

        smoothed_position: tuple of ints
            The current position of the eye after its raw position is passed through the
            smoothing filter
        """

        if current_time - self._idle_watch_start > self._IDLE_RUN_TIME:
            self._idle = False
            self._idle_watch_start = current_time
            return smoothed_position

        elif self._idle_func == 'random_idle':
            if current_time - self._prev_idle_time > .75:
                #Use of decimal multiplier on next two lines restricts the effective
                #bounding box in which the eye may look during random idle
                random_x = random.randint(int(.25 * self._OUTPUT_WIDTH), int(.75 * (self._OUTPUT_WIDTH - self._EYE_WIDTH)))
                random_y = random.randint(int(.25 * self._OUTPUT_HEIGHT), int(.75 * (self._OUTPUT_HEIGHT - self._EYE_HEIGHT)))
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