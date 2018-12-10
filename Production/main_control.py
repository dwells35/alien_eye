
import display_utils as du
from imutils.video import VideoStream
from imutils.video import FileVideoStream
from PTCamera import PTCamera
from Deep_Detector import Deep_Detector
from Tracker import Tracker
from Blink_Sprite import Blink_Sprite
from Dilate_Sprite import Dilate_Sprite
from Service_Exit import Service_Exit
import time
import random
import imutils
import cv2
import dlib
import pygame
from queue import Queue
import threading
import multiprocessing
import signal
from Idler import Idler
import sys


'''
####################
   MACHINE VISION
####################
'''

def get_detection_data(indices, net, detections):
    #pick a random index from that list of indices (this way, if there are multiple people,
    #the alien won't get fixated on just one person)
    num = random.randint(0, len(indices) - 1)
    ind_of_interest = indices[num]
    #get bounding box of detected face
    bounding_box = net.detection_box(detections, ind_of_interest)
    #unpack bounding box into its components
    startX, startY, endX, endY = bounding_box
    detected_center_raw = (int((endX - startX) / 2) + startX, int((endY - startY) / 2) + startY)

    return detected_center_raw, bounding_box

#Picks a face from a list of detected faces. If a face is found, a bounding box
#for the face is returned and the center of the box is given to the queue for animation
#If none are found, tracking_face is False, and the detector tries again on the next frame.

#NOTE: put() and get() from the queue has built in blocking calls; no additional locks necessary
def run_detector(net, frame, tracker, q):
    detections = net.get_detections(frame)
    indices = net.get_detection_inds(detections)
    tracking_face = False
    if len(indices) > 0:
        detected_center_raw, bounding_box = get_detection_data(indices, net, detections)

        startX, startY, endX, endY = bounding_box

        if (endX - startX) < 45 and not q.full():
            tracker = start_tracker(tracker, frame, startX, startY, endX, endY)
            tracking_face = True
            q.put((detected_center_raw, 0))

        if DEBUG:
            if len(indices) > 0:
                cv2.rectangle(frame, (startX, startY), (endX, endY),
                (0, 0, 255), 2)
                cv2.imshow('main frame', frame)
    else:
        cv2.imshow('main frame', frame)

    return tracking_face

#Gets center point of updated bouning box from tracker; puts this in the queue for animation

#NOTE: put() and get() from the queue has built in blocking calls; no additional locks necessary
def run_tracker(tracker, frame, q):
    tracked_center_raw = tracker.update_position(frame)
    tracked_center_raw = (tracked_center_raw.x, tracked_center_raw.y)
    if not q.full():
        q.put((tracked_center_raw, 1))
    if DEBUG:
        cv2.imshow('main frame', frame)

#Creates a tracker based on the bounding box returned from the detector
def start_tracker(tracker, frame, startX, startY, endX, endY):
    tracker.get_tracker().start_track(frame, 
                        dlib.rectangle( startX,
                                        startY,
                                        endX,
                                        endY))
    return tracker

#This function runs the machine vision portion of the eye. 
#params:
#   vs: Video Stream is the camera stream. Reading from the camera is I/O gating.
#   stop_event: stop event is triggered when the program either quits as expected, recieve as SIGINT (CTRL + C) signal, or
#       SIGTERM signal from the CPU. The stop event terminates the thread's execution gracefully
#This function manages both the detector (neural net) and the tracker.
def run_machine_vision(q, sub_pipe_end, video_dims):
    #Threaded application -- Use PTCamera_Threaded module
    #vs = PTCamera(resolution = video_dims).start()
    #Non-threaded application
    vs = PTCamera(resolution = video_dims)
    time.sleep(2)
    print("[INFO] loading model...")
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
    count = 0
    detector_count = 0
    while running:
        if sub_pipe_end.poll():
            running = sub_pipe_end.recv()
        current_time = time.time()
        frame = vs.read()
        frame = imutils.resize(frame, width=input_video_width)

        if not tracking_face or current_time - last_detector_update_time > net.get_refresh_rate():
            last_detector_update_time = current_time
            tracking_face = run_detector(net, frame, tracker, q)
            count += 1
            detector_count += 1

        if tracking_face:
            count += 1
            track_quality = tracker.get_track_quality(frame)
            if track_quality >= tracker.get_quality_threshold():
                run_tracker(tracker, frame, q)
            else:
                tracking_face = False 

        cv2.waitKey(2)
        

    end_machine_vision_time = time.time()
    fps = count / (end_machine_vision_time - start_machine_vision_time)
    print('Machine Vision fps: ' + str(fps))
    vs.stop()
    cv2.destroyAllWindows()
    print('Detector Count: ' + str(detector_count))


'''
####################
     ANIMATION
####################
'''
def scale_point_to_display(center_point_raw, flip_horizontal = False):
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
    #move the center of the detected face to a corresponding place in the output image
    #i.e., if the face was found in the center of the camera input image, and the camera image
    #was 480x480, then center = (240, 240), but the output image is much larger (maybe 1080x1080),
    #so the center value must be mapped to the center of the output image in order for things to look
    #correct
    #center_point = (offset_x - center_point_raw[0], center_point_raw[1] + offset_y)
    #convert detected center to corner point of image in order to give point 
    return (scaled_point[0] - eye_width/2, scaled_point[1] - eye_height/2) 


def update_position(position, designation, q):
    if not q.empty():
        position_prev = position
        designation_prev = designation
        center_position, designation = q.get()
        scaled_point = scale_point_to_display(center_position, flip_horizontal = True)
        position = map_center_to_corner(scaled_point)
        if designation - designation_prev == -1 \
        and not dilate_sprite.dilate_req \
        and abs(position[0] - position_prev[0]) > 5 \
        and abs(position[1] - position_prev[1]) > 5:
             dilate_sprite.dilate_req = True

        q.task_done()
    else:
        position_prev = position


    return position, position_prev, designation

def control_dilation(current_time):
    #control the dilation frequency
    if dilate_sprite.dilate_req and not blinking and not dilate_sprite.dilating:
        dilate_sprite.dilating = True
        dilate_sprite.dilate_clock = current_time - 1

    if dilate_sprite.dilating: 
        eye_im_show = dilate_sprite.dilate(current_time)
        
    else:
        eye_im_show = default_eye_image

    return eye_im_show

def control_blinking(current_time):
    #control blinking frequency
    global blinking
    global ball_in_hole

    if not blinking \
    and not ball_in_hole \
    and not dilate_sprite.dilate_req \
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
        if blink_sprite.index == 17:
            blinking = False

def check_ball_in_hole(smoothed_position, events):
    global ball_in_hole
    global ball_in_hole_time_start

    #initialize i = 0 and increasing = True for ball_in_hole sequence
    sequence_info = (smoothed_position, 0, True)
    #event is a queue run by pygame that handles all input. When "get" is called,
    #it will return all the messages that have accumulated in the queue. Here, we
    #iterate over each message to see if it's what we want.
    #This will cause the ball_in_hole event to fire when the 'h' key is pressed on the keyboard
    for event in events:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_h and not ball_in_hole:
            ball_in_hole_time_start = time.time()
            ball_in_hole = True
            dilate_sprite.dilate_req = True

    return sequence_info

def handle_ball_in_hole(current_time, sequencer_info, eye_im_show):
    global ball_in_hole
    #Control behavior when ball is hit into hole
    smoothed_position, i, increasing = sequencer_info

    smoothed_position = du.avg_center(HOLE, smoothed_position, 1/4)
    
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

    out_display.blit(eye_im_show, smoothed_position)
    if current_time - ball_in_hole_time_start > 4:
        ball_in_hole = False

    return (smoothed_position, i, increasing)

def check_idle(position, position_prev, current_time):
    #check to see if the coordinate received from the machine vision pipeline is within a 3x3 bounding box of the previous coordinate
    if abs(position[0] - position_prev[0]) < 1 and abs(position[1] - position_prev[1]) < 1 and not ball_in_hole:
        idle_time = current_time - idler.get_idle_watch_start()
        if idle_time > idler.get_idle_time_trigger() and not idler.is_idle():
            idler.begin_idle()
            
    else:
        idler.set_idle_watch_start(current_time)
        idler.set_idle(False)

def handle_idle(current_time, smoothed_position, eye_im_show):
    smoothed_position = idler.run_idle(current_time, smoothed_position)
    out_display.fill((0,0,0))
    out_display.blit(eye_im_show, smoothed_position)
    return smoothed_position

def run_main_animation(position, smoothed_position, eye_im_show):
    smoothed_position = du.avg_center(position, smoothed_position, 1/10)
    out_display.fill((0,0,0))
    out_display.blit(eye_im_show, smoothed_position)
    return smoothed_position

'''
####################
     SETUP/RUN
####################
'''

def service_shutdown(signum, frame):
    raise Service_Exit

def initialize_globals():
     
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
    global FRAMERATE; FRAMERATE = 30
    #initialize time delta to control how often the animation updates
    global DELTA_T; DELTA_T = (1/FRAMERATE)
    #initialize an idler to handle when the program is at idle
    global idler; idler = Idler(CENTER, (output_width, output_height), (eye_width, eye_height))
    #initialize maximum schelra RED color when the ball is hit into the hole
    global SCHLERA_RED_MAX; SCHLERA_RED_MAX = 50
    #Setting up a stop event in order to make sure the threads finish gracefully when the program is stopped
    global stop_event; stop_event = threading.Event()
    global ball_in_hole_time_start

def setup():
     #initialize PyGame for output animation
    pygame.display.init()
    initialize_globals()
    #create a caption for the output display
    pygame.display.set_caption('Alien Eye')
     # initialize the video stream and allow the cammera sensor to warmup
    print("[INFO] starting video stream...")
    #Only allow pygame events of type KEYDOWN and type QUIT into the pygame event queue. This prevents it 
    #from ever getting bloated. This queue is automatically setup by pygame but must be manually emptied
    #with get() or poll(). See "check_ball_in_hole()" for information on pygame.event.get()
    pygame.event.set_allowed([pygame.KEYDOWN, pygame.QUIT])
    
    video_dims = (input_video_width, input_video_height)
    
    #use FileVideoStream to read video from a file for testing
    #vs = FileVideoStream('no_vis_light.mp4').start()
    #initialize Queue to pass data from detector thread to main thread
    sub_pipe_end, main_pipe_end = multiprocessing.Pipe(duplex = False)
    q = multiprocessing.JoinableQueue(maxsize=6)
    #Start running the detector and the tracker on seperate threads so that they won't bog down
    #the output display speed
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
    #initialize designation for center point given to queue
    #'0' designates that the detector put the value in the queue
    #'1' designates that the tracker put the value into the queue
    #This is used for "rising edge detection" to flag when the detector has run
    #and lets the animation loop control when the eye will dilate when it detects a new person
    designation = 0
    #initialize all possible starting locations for the eye as CENTER
    smoothed_position = CENTER
    position = CENTER
    position_prev = CENTER
    #Setup condition for continuous while loop
    running = True
    #Initialize clock to control refresh rate of PyGame
    clock = pygame.time.Clock()
    #fps counter initialize
    count = 0
    try:
        profiling_watch_end = time.time()
        start_fps_timer = time.time()
        while running:
            clock.tick(FRAMERATE)
            current_time = time.time()
            #get all events for this loop; clears the queue
            events = pygame.event.get()
            position, position_prev, designation = update_position(position, designation, q)
            eye_im_show = control_dilation(current_time)

            if not ball_in_hole:
                sequence_info = check_ball_in_hole(smoothed_position, events)
            if ball_in_hole:
                sequence_info = handle_ball_in_hole(current_time, sequence_info, eye_im_show)
                smoothed_position = sequence_info[0]
            #handle main animation
            if not ball_in_hole and not idler.is_idle():
                smoothed_position = run_main_animation(position, smoothed_position, eye_im_show)
            #handle idle behavior
            check_idle(position, position_prev, current_time)
            if idler.is_idle():
                smoothed_position = handle_idle(current_time, smoothed_position, eye_im_show)

            control_blinking(current_time)
            #update output display
            pygame.display.update()
            #check to see if game has been exited (by hitting the red "X" on the display)
            #Since the event queue is cleared on every loop by the "check_ball_in_hole" command, one
            #may need to spam the ESCAPE key to get this to fire since the event must be triggered between that fucntion
            #and this one
            for event in events:
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                    stop_event.set()
                    main_pipe_end.send(False)
                    print("set_stop_event")

            '''
            if profiling_watch_end - start_fps_timer > 30:
                running = False
                stop_event.set()
                print("set_stop_event")
            '''
            profiling_watch_end = time.time()
            count += 1
    except Service_Exit:
        stop_event.set()
        main_pipe_end.send(False)
    except KeyboardInterrupt:
        stop_event.set()
        main_pipe_end.send(False)

    finally:
        end_fps_timer = time.time()
        fps = count / (end_fps_timer - start_fps_timer)
        print("animation FPS: " + str(fps))
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
        
if __name__ == '__main__':
    main()