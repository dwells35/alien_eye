#System
import time
import random
import multiprocessing
import signal
#3rd Party
import imutils
from imutils.video import VideoStream
from imutils.video import FileVideoStream
import cv2
import dlib
import pygame
#Local
from PTCamera import PTCamera
from Deep_Detector import Deep_Detector
from Tracker import Tracker
from Blink_Sprite import Blink_Sprite
from Dilate_Sprite import Dilate_Sprite
from Service_Exit import Service_Exit
from Idler import Idler
import display_utils as du

'''
####################
   MACHINE VISION
####################
'''

def get_detection_data(indices, net, detections):
    """
    Pick a random index from that list of indices (this way, if there are multiple people,
    the alien won't get fixated on just one person) and return that face's bounding box

    Parameters
    ----------
    indices: list of ints
    	List of integer indices corresponding to faces in the detections list that meet or exceed the confidence threshold

    net: Deep_Detector detector
    	The Deep_Detector object from which data about the detected faces is pulled

    detections: 4D array of ints
    	4D array of faces that the net identified in the image

    Returns
    -------

    bounding_box: tuple of ints
    	tuple of length 4 with corners of the bounding box of the detected face in it: (startX, startY, endX, endY)
    """

    num = random.randint(0, len(indices) - 1)
    ind_of_interest = indices[num]
    #get bounding box of detected face
    bounding_box = net.detection_box(detections, ind_of_interest)

    return bounding_box

def run_detector(net, frame, tracker, q, face_width_threshold):
    """
    Uses a nerual net to detect faces in an input image and starts a tracker if a vaild face is found

    Picks a face from a list of detected faces. If a face is found, a bounding box
    for the face is returned and the center of the box is given to the queue for
    animation. The bounding box is also used to create a new correlation tracker.
	
	If none are found, tracking_face is False, and the detector tries
    again on the next frame.

	Parameters
	----------
    net: Deep_Detector detector
    	The Deep_Detector object from which data about the detected faces is pulled

    frame: numpy ndarray
    	image from input video stream from which to find faces

    tracker: Tracker
    	A tracker object that is used to create a new correlation tracker if a valid face is found

    q: Multiprocessing Joinable Queue
        Queue that holds tracked/detected points

    face_width_threshold: int
    	Maximum width of a bounding box containing a face; used to help prevent false positives seen in previous testing

    Returns
    -------
	tracking_face: boolean
		Flag denoting that a face was found that met all necessary criteria and has been given to the Tracker to track
    """

    detections = net.get_detections(frame)
    indices = net.get_detection_inds(detections)
    tracking_face = False
    if len(indices) > 0:
        bounding_box = get_detection_data(indices, net, detections)
        #unpack bounding box into its components
        startX, startY, endX, endY = bounding_box
        detected_center_raw = (int((endX - startX) / 2) + startX, int((endY - startY) / 2) + startY)


        if (endX - startX) < face_width_threshold and not q.full():
            tracker = start_tracker(tracker, frame, startX, startY, endX, endY)
            tracking_face = True
            q.put((detected_center_raw, 0))


        if DEBUG:
            if len(indices) > 0:
                cv2.rectangle(frame, (startX, startY), (endX, endY),
                (0, 0, 255), 2)
                cv2.imshow('main frame', frame)
    elif DEBUG:
        cv2.imshow('main frame', frame)

    return tracking_face

def run_tracker(tracker, frame, q):
    """
    Get center point of updated bouning box from tracker;
    put this in the queue for animation

    Parameters
    ----------
    tracker: dlib Correlation Tracker
        Tracker object that processes the image

    frame: numpy ndarray
        most recent image from camera

    q: Multiprocessing Joinable Queue
        Queue that holds tracked/detected points

    """

    tracked_center_raw = tracker.update_position(frame)
    tracked_center_raw = (tracked_center_raw.x, tracked_center_raw.y)
    if not q.full():
        q.put((tracked_center_raw, 1))

    if DEBUG:
        cv2.imshow('main frame', frame)

def start_tracker(tracker, frame, startX, startY, endX, endY):
    """Create a tracker based on the bounding box returned from the detector"""
    tracker.get_tracker().start_track(frame, 
                        dlib.rectangle( startX,
                                        startY,
                                        endX,
                                        endY))
    return tracker

def run_machine_vision(q, sub_pipe_end, video_dims):
    """
    Manage both the detector (neural net) and the tracker in a
    seperate process than the animation.
    
    Parameters
    ----------
    q: Multiprocessing Joinable Queue
        in which points are placed from the detector/tracker

    sub_pipe_end: Pipe
        Macine vision subprocess's end of the pipe that lets the process communicate
        with the main process

    video_dims: tuple of ints 
        Dimensions of requested input video
    """

    #use imutils.FileVideoStream to read video from a file for testing
    #vs = FileVideoStream('no_vis_light.mp4').start()

    #use imutils.VideoStream to read video from a webcam for testing
    vs = VideoStream(src=0, resolution = video_dims).start()

    #Threaded application of PTGrey Camera-- Use PTCamera_Threaded
    #vs = PTCamera(resolution = video_dims).start()

    #Non-threaded application of PTGrey Camera
    #vs = PTCamera(resolution = video_dims)

    #Let the camera warm up and set configuration
    time.sleep(2)
    print("[INFO] loading model...")
    #create an insance of the detector
    net = Deep_Detector('deploy.prototxt.txt','res10_300x300_ssd_iter_140000.caffemodel', refresh_rate = 5, confidence = .4)

    #initialize a tracker
    print("[INFO] initializing tracker")
    tracker = Tracker(quality_threshold = 6)
    
    last_detector_update_time = time.time()
    current_time = time.time()
    tracking_face = False
    tracked_center = (0,0)
    running = True
    start_machine_vision_time = time.time()
    #count = 0
    #detector_count = 0

    #check to make sure that the identified face is of a reasonable size; For the PTGrey Camera, I found ~50 works well.
    #other cameras will require other thresholds
    face_width_threshold = 100
    no_frame_count = 0

    while running:
        if sub_pipe_end.poll():
            running = sub_pipe_end.recv()
        current_time = time.time()
        #Reading from the camera is I/O gating.
        frame = vs.read()
        if frame != None:
            no_frame_count = 0
            frame = imutils.resize(frame, width=input_video_width)

            if not tracking_face or current_time - last_detector_update_time > net.get_refresh_rate():
                last_detector_update_time = current_time
                tracking_face = run_detector(net, frame, tracker, q, face_width_threshold)
                #count += 1
                #detector_count += 1

            if tracking_face:
                #count += 1
                track_quality = tracker.get_track_quality(frame)
                if track_quality >= tracker.get_quality_threshold():
                    run_tracker(tracker, frame, q)
                else:
                    tracking_face = False 

            #Wait two milliseconds before looping again. OpenCV will freeze if this number
            #is too low or the waitKey call is omitted. If waitKey is called with no params,
            #the program will wait indefinitely for the user to hit a key before it
            #runs another loop; nice for debugging. 
            cv2.waitKey(2)

        else:
            no_frame_count += 1
            if no_frame_count == 50:
                print('Received too many null frames; exiting machine_vision_subprocess')
                break
        
    end_machine_vision_time = time.time()
    #fps = count / (end_machine_vision_time - start_machine_vision_time)
    #print('Machine Vision fps: ' + str(fps))
    vs.stop()
    cv2.destroyAllWindows()
    #print('Detector Count: ' + str(detector_count))


'''
####################
     ANIMATION
####################
'''

def control_ouput_region(position):
    """
    Map corner point of eye image output to a visible region of the display
    if the output exceeds the display bounds

    Parameters
    ----------
    position: tuple of ints
        Position of the eye after it has been mapped to the corner of
        the eye output image.

    Returns
    -------
    position: tuple of ints
    	Updated position if the input position is found to be "out of bounds";
    	otherwise simply returns input position
    """

    x = position[0]
    y = position[1]

    if x < 0:
        position = (0, position[1])
    elif x > (output_width - eye_width):
        position = (output_width - eye_width, position[1])

    if y < 0:
        position = (position[0], 0)
    elif y > (output_height - eye_height):
        position = (position[0], output_height - eye_height)

    return position

def scale_point_to_display(center_point_raw, flip_horizontal = False):
    """
    Scales the input center point to a corresponding point on the output image.

    Not quite a one-to-one mapping since this function also takes into account a restricted bounding box that is
    a function of the camera's field of view (FOV). This makes sure that the eye actually looks at a person.

    Parameters
    ----------
    center_point_raw: tuple of ints
        Center point of face given from tracker or detector; therefore, this center point corresponds to
        a pixel on the input video image (frame)

    flip_horizontal: boolean, default = False
        This flag tells this function whether or not the center point needs to be mirrored along the vertical axis
        to correctly look at someone.
        NOTE: this flag is optional since the camera has this capability built in, but webcams often do not. It was easier
        to make it programmatically changeable here, though one could do this from the PT Grey camera configuration if performance
        gains were needed

    Returns
    -------
    (output_x, output_y): tuple of ints
        This tuple represents the coordinate of the face in the output image that corresponds to the
        location of the face in the input image (but sllightly different because of scaling from camera FOV)
    """
    x = center_point_raw[0]
    y = center_point_raw[1]

    if flip_horizontal:
        x = input_video_width - x
    norm_x = ((x / input_video_width) / eye_view_adjustment_factor) 
    norm_y = ((y / input_video_height) / eye_view_adjustment_factor)
    output_x = (norm_x * output_width) + (output_width / 2) - (output_width / (2 * eye_view_adjustment_factor))
    output_y = (norm_y * output_height) + (output_height / 2) - (output_height / (2 * eye_view_adjustment_factor))
    return (output_x, output_y)

def map_center_to_corner(scaled_point):
    """
    Convert scaled center (center point on output image) to corner point of image in order for the
    image to be drawn correctly centered

    Parameters
    ----------
    scaled_point: tuple of ints
    	Center point of the eye with repect to the output image

    Returns
    -------
	corner_point: tuple of ints
		Center point mapped to the corner of the eye image
    """

    corner_point = (scaled_point[0] - eye_width/2, scaled_point[1] - eye_height/2)
    return  corner_point


def update_position(position, data_origin, q):
    """
    Update position of the eye based on tracker/detector data (gotten from queue)

    Parameters
    ----------
    postition: tuple of ints
        Position of the last point the eye was drawn

    data_origin: int
        Either a one or a zero; this lets this function know if the point was put there by the detector
        or the tracker. This is used to control dilation behavior when a new face is found.

    q: Multiprocessing Joinable Queue
        Points are placed from the detector/tracker

    Returns
    -------
    position: tuple of ints
        New position of eye as given from tracker/detector

    position_prev: tuple of ints
        Previous position of the eye; used for checking if the eye is idle

    data_origin: int
        Either a one or a zero; this lets this function know if the point was put there by the detector
        or the tracker. This is used to control dilation behavior when a new face is found.
    """
    if not q.empty():
        position_prev = position
        data_origin_prev = data_origin
        center_position, data_origin = q.get()
        scaled_point = scale_point_to_display(center_position, flip_horizontal = True)
        position = map_center_to_corner(scaled_point)
        position = control_ouput_region(position)
        #Send a blink request if a face is detected outside of a 5x5 bounding box
        #where the tracked center was
        if data_origin - data_origin_prev == -1 \
        and not dilate_sprite.dilate_req \
        and abs(position[0] - position_prev[0]) > 5 \
        and abs(position[1] - position_prev[1]) > 5:
             dilate_sprite.dilate_req = True

        q.task_done()
    else:
        position_prev = position


    return position, position_prev, data_origin

def control_dilation(current_time):
    """
    Control when dilation occurs: looks for a dilation request to be set (dilate_req)

    Parameters
    ----------
    current_time: double
        Time since the epoch; used to get current time of the main animation loop

    Returns
    -------
    eye_im_show: pygame Image
        The eye image that will be displayed
    """
    
    if dilate_sprite.dilate_req and not dilate_sprite.dilating:
        dilate_sprite.dilating = True
        dilate_sprite.dilate_clock = current_time - 1

    if dilate_sprite.dilating: 
        eye_im_show = dilate_sprite.dilate(current_time)
        
    else:
        eye_im_show = default_eye_image

    return eye_im_show

def control_blinking(current_time):
    """
    Control blinking frequency: blinking is pseudo random; one blink happens between between every
        3.0 and 6.0 seconds

    Parameters
    ----------
    current_time: double
        Time since the epoch; used to get current time of the main animation loop
    """

    global blinking
    global ball_in_hole

    if not blinking \
    and not ball_in_hole \
    and current_time - blink_sprite.last_blink_time > blink_sprite.rand_blink_time:
        blink_sprite.rand_blink_time = random.uniform(3.0, 6.0)
        blinking = True
        blink_sprite.last_blink_time = current_time
        blink_sprite.blink_clock = current_time - 1

    if blinking:
        if current_time - blink_sprite.blink_clock > blink_sprite.blink_refresh_time:
            blink_sprite.blink_clock = current_time
            blink_sprite.group_blink.update()
        blink_sprite.group_blink.draw(out_display)
        if blink_sprite.index == blink_sprite.MAX_INDEX:
            blinking = False

def check_ball_in_hole(events):
    """
    Check to see if the program has received a simulated 'h' key denoting that the ball has been
        putted into the hole


    Parameters
    ----------
    events: pygame Event queue
        Queue of all game events that have happened since the last time the queue was emptied

    Returns
    -------
    ball_in_hole_init: boolean
        Flag that tells sequence_info to initialize; acts as a one-shot. Makes sure that sequence
        info is only initialized when another keystroke is detected.
    """
    global ball_in_hole_time_start
    ball_in_hole_init = False

    #This will cause the ball_in_hole event to fire when the 'h' key is pressed on the keyboard
    for event in events:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_h:
            ball_in_hole_time_start = time.time()
            dilate_sprite.dilate_req = True
            ball_in_hole_init = True

    return ball_in_hole_init

def pulse_schlera(current_time, sequencer_info):
    """
    Control behavior when ball is hit into hole

    This will cause the eye to look down at the hole and make the schlera pulse red (or any other color desired)

    Parameters
    ----------
    current_time: double
        Time since the epoch; used to get current time of the main animation loop

    sequencer_info: tuple -> (i: int, increasing: boolean)
        Used to control the pulsing schera. Increasing denotes if i (the color index) is increasing
        or decreasing.

    Returns
    -------
    sequencer_info: tuple -> (i: int, increasing: boolean)
        Used to control the pulsing schera. Increasing denotes if i (the color index) is increasing
        or decreasing.
    """
    global ball_in_hole
    i, increasing = sequencer_info

    #Make the color of the schlera pulse red; change pulse speed by changing how quickly i is incremented
    if increasing and i <= SCHLERA_RED_MAX:
        i += 2
        out_display.fill((i, 0, 0))
        if i == SCHLERA_RED_MAX:
            increasing = False
    else:
        i -= 2
        out_display.fill((i, 0, 0))
        if i == 0:
            increasing = True

    #Control how long the eye looks down at the hole; Make sure also to stop looking down when i has returned to 0
    if current_time - ball_in_hole_time_start > 4.5 and i == 0:
        ball_in_hole = False

    return (i, increasing)

def check_idle(position, position_prev, current_time):
    """
    Check to see if the coordinate received from the machine vision pipeline is within a 1x1 bounding box of the previous coordinate
    
    Parameters
    ----------
    position: tuple of ints
        Current position of the eye

    position_prev: tuple of ints
        Previous position of the eye

    current_time: double
        Time since the epoch; used to get current time of the main animation loop
    """
    if abs(position[0] - position_prev[0]) < 1 and abs(position[1] - position_prev[1]) < 1 and not ball_in_hole:
        idle_time = current_time - idler.get_idle_watch_start()
        if idle_time > idler.get_idle_time_trigger() and not idler.is_running_idle():
            idler.begin_idle()
            
    else:
        idler.set_idle_watch_start(current_time)
        idler.set_running_idle(False)

def handle_idle(current_time, smoothed_position, eye_im_show):
    """
    Run an idle behavior if the eye has been determined to be idle

    Parameters
    ----------
    current_time: double
        Time since the epoch; used to get current time of the main animation loop
    
    smoothed_position: tuple of ints
        Position of the eye after it has been passed through the alpha smoothing algorithm

    eye_im_show: pygame image
        The current image of the eye

    Returns
    -------
    smoothed_position: tuple of ints
        Updated position of the eye after it has been passed through the alpha smoothing algorithm; in this
        case, after the idle behavior has altered the position of the eye
    """
    smoothed_position = idler.run_idle(current_time, smoothed_position)
    out_display.fill((0,0,0))
    out_display.blit(eye_im_show, smoothed_position)
    return smoothed_position

def run_main_animation(position, smoothed_position, eye_im_show):
    """
    Handles default animation of the eye; i.e. normal tracking behavior animation

    Parameters
    ----------
    position: tuple of ints
        Current position of the eye (to be drawn at)

    smoothed position: tuple of ints
        Position of eye after being passed through alpha smoothing algorithm. In this case, this is the
        last position at which the eye was actually drawn

    eye_im_show: pygame image
        Current image of the eye (this changes with dilation)

    Returns
    -------
    smoothed_position: tuple of ints
        Position of eye after being passed through alpha smoothing algorithm. In this case, this is the
        NEW last position at which the eye was actually drawn

    """
    smoothed_position = du.smooth_position(position, smoothed_position, 1/10)
    out_display.fill((0,0,0))
    out_display.blit(eye_im_show, smoothed_position)
    return smoothed_position

'''
####################
     SETUP/RUN
####################
'''

def service_shutdown(signum, frame):
    """
    Custom exception caught from signals to terminate processes cleanly
    """
    raise Service_Exit

def initialize_globals():
    """
    Initialize all global variables
    """

    #Use this to toggle optional features useful for debugging. Set to False for production.
    global DEBUG; DEBUG = True
    #set factor to make eye look at a person. This factor helps map a coordinate to an artificial bounding box
    #in which the eye can move so that its range of motion will align with the camera's field of view
    camera_horiz_angle_of_view = 90
    global eye_view_adjustment_factor; eye_view_adjustment_factor = 360 / camera_horiz_angle_of_view
    #initialize output animation width and height
    #Get an object containing information about the detected output screen
    screen_info = pygame.display.Info()
    #Match this to the chosen resolution of the screen; Also, ensure that the aspect ratio matche with this value
    print('detected screen size: %sx%s' % (str(screen_info.current_w), str(screen_info.current_h)))
    #set global ouput width and height to detected screen resolution 
    global output_width; output_width = screen_info.current_w
    global output_height; output_height = screen_info.current_h
    #initialize the size of the video stram coming from the camera; Make sure the chosen aspect ratio works with this value
    global input_video_width; input_video_width = 640
    global input_video_height; input_video_height = 480
    #initialize output display of pygame
    #pygame.NOFRAME parameter gets rid of title bar
    global out_display; out_display = pygame.display.set_mode((output_width, output_height), pygame.NOFRAME)
    #initialize eye image and size
    global eye_width; eye_width = 350
    global eye_height; eye_height = 350
    #initialize blink and dilation sprites for use in animation;
    global blink_sprite; blink_sprite = Blink_Sprite(output_width, output_height)
    global dilate_sprite; dilate_sprite = Dilate_Sprite(eye_width, eye_height)
    #initialize default eye image
    global default_eye_image; default_eye_image = dilate_sprite.images[0] 
    #initialize offsets to be used for detected/tracked center points to image corner points
    global offset_x; offset_x = (int(output_width / 2) + int(input_video_width / 2))
    global offset_y; offset_y = (int(output_height / 2) - int(input_video_height / 2))
    #initialize blinking as global so accessory functions can monitor if the eye is blinking or not
    global blinking; blinking = False
    #initialize ball_in_hole as global so accesory functions can monitor if the ball is in the hole or not
    global ball_in_hole; ball_in_hole = False
    #initialize important points of reference
    global HOLE; HOLE = (int((output_width -  eye_width)/2),
                 int(.75 * (output_height - eye_height)))
    global CENTER; CENTER = (int((output_width -  eye_width)/2),
                 int((output_height - eye_height)/2))
    #set desired framerate
    global FRAMERATE; FRAMERATE = 40
    #initialize time delta to control how often the animation updates
    global DELTA_T; DELTA_T = (1/FRAMERATE)
    #initialize an idler to handle when the program is at idle
    global idler; idler = Idler(CENTER, (output_width, output_height), (eye_width, eye_height))
    #initialize maximum schelra RED color when the ball is hit into the hole
    global SCHLERA_RED_MAX; SCHLERA_RED_MAX = 50
    global ball_in_hole_time_start

def setup():
    """
    Initialize Processes, PyGame, and communication channels

    Returns
    -------
    (machine_vision_subprocess, q, main_pipe_end): tuple
        This tuple is given to the main loop so that these structures can be properlly terminated
    """

    #initialize PyGame for output animation
    pygame.display.init()
    initialize_globals()
    #create a caption for the output display
    pygame.display.set_caption('Alien Eye')
    #initialize the video stream and allow the cammera sensor to warmup
    print("[INFO] starting video stream...")
    #Only allow pygame events of type KEYDOWN and type QUIT into the pygame event queue. This prevents the event queue 
    #from ever getting bloated. This queue is automatically setup by pygame but must be manually emptied
    #with get() or poll().
    pygame.event.set_allowed([pygame.KEYDOWN, pygame.QUIT])
    
    video_dims = (input_video_width, input_video_height)

    #initialize Pipe to pass signal data (process termination data) from animation process
    #to machine vision process; duplex is False, so information can only flow one way
    sub_pipe_end, main_pipe_end = multiprocessing.Pipe(duplex = False)
    #initialize Queue to pass face location data from machine vision process to animation process
    q = multiprocessing.JoinableQueue(maxsize=4)
    #Run machine vision in a seperate process to keep it from bogging down animation
    machine_vision_subprocess = multiprocessing.Process(target = run_machine_vision, args=(q, sub_pipe_end, video_dims))
    machine_vision_subprocess.start()
    #setup signals to let the program capture user sent termiantion (SIGINT) and program sent termination (SIGTERM)
    signal.signal(signal.SIGTERM, service_shutdown)
    signal.signal(signal.SIGINT, service_shutdown)

    return machine_vision_subprocess, q, main_pipe_end

def main():
    #setup pygame, video stream, and detector thread; return detector thread and video strean so main can stop these later.
    machine_vision_subprocess, q, main_pipe_end = setup()
    #initialize previous time to use for checking when to run the animation loop
    previous_time = 0
    #initialize data_origin for center point given to queue
    #'0' designates that the detector put the value in the queue
    #'1' designates that the tracker put the value into the queue
    #This is used for "rising edge detection" to flag when the detector has run
    #and lets the animation loop control when the eye will dilate when it detects a new person
    data_origin = 0
    #initialize all possible starting locations for the eye as CENTER
    smoothed_position = CENTER
    position = CENTER
    position_prev = CENTER
    #Setup condition for continuous while loop
    running = True
    #Initialize clock to control refresh rate of PyGame
    clock = pygame.time.Clock()
    #fps counter initialize
    #count = 0

    #This is to appease Python because of how ball_in_hole is referenced later in this loop.
    #It needs to understance ball_in_hole should always be global
    global ball_in_hole

    try:
        #profiling_watch_end = time.time()
        start_fps_timer = time.time()
        
        #MAIN LOOP
        while running:
            clock.tick(FRAMERATE)
            current_time = time.time()

            ######################
            #GAME EVENT GATHERING#
            ######################
            #event is a queue run by pygame that handles all input. When "get" is called,
            #it will return all the messages that have accumulated in the queue. It will also clear
            #the queue.
            events = pygame.event.get()

            #####################
            #EYE POSITION UPDATE#
            #####################
            position, position_prev, data_origin = update_position(position, data_origin, q)

            ##########
            #DILATION#
            ##########
            eye_im_show = control_dilation(current_time)

            ##############
            #BALL IN HOLE#
            ##############
            ball_in_hole_init = check_ball_in_hole(events)
            #Only run this initialization statement if a ball is putted in AND the eye is currently not looking
            #down at the hole. This lets multiple people to hit their ball in, and it will not interupt the
            #eye's "looking at the hole" animation, but it will extend the time it looks down
            #(by resetting ball_in_hole_time_start)
            if ball_in_hole_init and not ball_in_hole:
                #initialize i = 0 and increasing = True for ball_in_hole sequence
                sequence_info = (0, True)
                ball_in_hole = True

            if ball_in_hole:
                sequence_info = pulse_schlera(current_time, sequence_info)
                #Update the position of the eye to be the HOLE constant
                smoothed_position = du.smooth_position(HOLE, smoothed_position, 1/4)
                #draw the eye on the display
                out_display.blit(eye_im_show, smoothed_position)

            ##############################
            #MAIN ANIMATION (EYE DRAWING)#
            ##############################
            if not ball_in_hole and not idler.is_running_idle():
                smoothed_position = run_main_animation(position, smoothed_position, eye_im_show)
            #handle idle behavior
            check_idle(position, position_prev, current_time)
            if idler.is_running_idle():
                smoothed_position = handle_idle(current_time, smoothed_position, eye_im_show)

            ##########
            #BLINKING#
            ##########
            #Blinking must be done after eye drawing for the layers to look correct
            control_blinking(current_time)

            #######################
            #UPDATE OUPTUT DISPLAY#
            #######################
            pygame.display.update()
            #check to see if game has been exited (by hitting the red "X" on the display or hitting the "ESC" key)
            #Since the event queue is cleared on every loop by the "check_ball_in_hole" command, one
            #may need to spam the ESCAPE key to get this to fire since the event must be triggered between that fucntion
            #and this one
            for event in events:
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                    main_pipe_end.send(False)
                    print("ending Subprocess")

            '''
            if profiling_watch_end - start_fps_timer > 30:
                running = False
                print("edning Subprocess")
            
            profiling_watch_end = time.time()
            '''
            #count += 1
    except Service_Exit:
        print('Service_Exit')
        main_pipe_end.send(False)
    except KeyboardInterrupt:
        print('KeyboardInterrupt')
        main_pipe_end.send(False)

    finally:
        end_fps_timer = time.time()
        #fps = count / (end_fps_timer - start_fps_timer)
        #print("animation FPS: " + str(fps))
        print('hit finally')
        #empty the queue
        while not q.empty():
            temp = q.get()
            q.task_done()
        q.join()
        machine_vision_subprocess.join()
        pygame.quit()
        print("Ended Gracefully")
        print('Subprocess is still live: ' + str(machine_vision_subprocess.is_alive()))
        quit()

#Run the whole thing
if __name__ == '__main__':
    main()
