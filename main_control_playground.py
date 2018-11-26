
import display_utils as du
from imutils.video import VideoStream
from imutils.video import FileVideoStream
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
import signal
from Idler import Idler
from Program_Data import Program_Data

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
def run_detector(net, frame, tracker):
    detections = net.get_detections(frame)
    indices = net.get_detection_inds(detections)
    tracking_face = False
    if len(indices) > 0:
        detected_center_raw, bounding_box = get_detection_data(indices, net, detections)

        startX, startY, endX, endY = bounding_box

        if (startX * startY) > 0:
            tracker = start_tracker(tracker, frame, startX, startY, endX, endY)
            tracking_face = True       

        if not q.full():
            q.put((detected_center_raw, 0))

        if DEBUG:
            if len(indices) > 0:
                cv2.rectangle(frame, (startX, startY), (endX, endY),
                (0, 0, 255), 2)
                cv2.imshow('main frame', frame)

    return tracking_face

#Gets center point of updated bouning box from tracker; puts this in the queue for animation

#NOTE: put() and get() from the queue has built in blocking calls; no additional locks necessary
def run_tracker(tracker, frame):
    tracked_center_raw = tracker.update_position(frame)
    tracked_center_raw = (tracked_center_raw.x, tracked_center_raw.y)
    if not q.full():
        q.put((tracked_center_raw, 1))
    if DEBUG:
        cv2.imshow('main frame', frame)

#Creates a tracker based on the bounding box returned from the detector
def start_tracker(tracker, frame, startX, startY, endX, endY):
    tracker.get_tracker().start_track(frame, 
                        dlib.rectangle( startX + 10,
                                        startY - 20,
                                        endX + 10,
                                        endY + 20))
    return tracker

#This function runs the machine vision portion of the eye. 
#params:
#   vs: Video Stream is the camera stream. Reading from the camera is I/O gating.
#   stop_event: stop event is triggered when the program either quits as expected, recieve as SIGINT (CTRL + C) signal, or
#       SIGTERM signal from the CPU. The stop event terminates the thread's execution gracefully
#This function manages both the detector (neural net) and the tracker.
def run_machine_vision(vs, stop_event):
    # load our serialized model from disk
    print("[INFO] loading model...")
    net = Deep_Detector('deploy.prototxt.txt','res10_300x300_ssd_iter_140000.caffemodel', refresh_rate = 5)

    #initialize a tracker
    print("[INFO] initializing tracker")
    tracker = Tracker(quality_threshold = 6)
    
    last_detector_update_time = time.time()
    current_time = time.time()
    tracking_face = False
    tracked_center = (0,0)
    while not stop_event.is_set():
        current_time = time.time()
        frame = vs.read()
        frame = imutils.resize(frame, width=input_video_width)

        if not tracking_face or current_time - last_detector_update_time > net.get_refresh_rate():
            last_detector_update_time = current_time
            tracking_face = run_detector(net, frame, tracker)

        if tracking_face:
            track_quality = tracker.get_track_quality(frame)
            if track_quality >= tracker.get_quality_threshold():
                run_tracker(tracker, frame)
            else:
                tracking_face = False 

        cv2.waitKey(2)


'''
####################
     ANIMATION
####################
'''

def map_center_to_corner(center_point_raw):
    #move the center of the detected face to a corresponding place in the output image
    #i.e., if the face was found in the center of the camera input image, and the camera image
    #was 480x480, then center = (240, 240), but the output image is much larger (maybe 1080x1080),
    #so the center value must be mapped to the center of the output image in order for things to look
    #correct
    center_point = (offset_x - center_point_raw[0], center_point_raw[1] + offset_y)
    #convert detected center to corner point of image in order to give point 
    return (center_point[0] - eye_width/2, center_point[1] - eye_height/2) 


def update_position(position, designation):
    if not q.empty():
        position_prev = position
        designation_prev = designation
        center_position, designation = q.get()
        position = map_center_to_corner(center_position)
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
    if dilate_sprite.dilate_req and not blinking:
        dilate_sprite.dilating = True

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

    if blinking:
        blink_sprite.group_blink.update()
        blink_sprite.group_blink.draw(out_display)
        if blink_sprite.index == 17:
            blinking = False

def check_ball_in_hole(smoothed_position):
    global ball_in_hole
    global ball_in_hole_time_start

    #initialize i = 0 and increasing = True for ball_in_hole sequence
    sequence_info = (smoothed_position, 0, True)
    if pygame.key.get_pressed()[pygame.K_h] and not ball_in_hole:
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
    if abs(position[0] - position_prev[0]) < 5 and abs(position[1] - position_prev[1]) < 5 and not ball_in_hole:
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
    smoothed_position = du.avg_center(position, smoothed_position)
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
     #initialize Queue to pass data from detector thread to main thread
    global q; q = Queue(maxsize=6)
    #Use this to toggle optional features useful for debugging. Set to False for production.
    global DEBUG; DEBUG = True
    #initialize output animation width and height
    #Match this to the chosen resolution of the screen 
    global output_width; output_width = 1920
    global output_height; output_height = 1080
    #initialize the size of the video stram coming from the camera
    global input_video_width; input_video_width = 480
    global input_video_height; input_video_height = 480
    #initialize output display of pygame
    global out_display; out_display = pygame.display.set_mode((output_width, output_height))
    #initialize default eye image and images size
    global default_eye_image; default_eye_image = pygame.image.load('prod_eye_dil/Pupil dilation 00.png').convert_alpha()
    global eye_width; eye_width = default_eye_image.get_width()
    global eye_height; eye_height = default_eye_image.get_height()
    #initialize blink and dilation sprites for use in animation;
    global blink_sprite; blink_sprite = Blink_Sprite(output_width, output_height)
    global dilate_sprite; dilate_sprite = Dilate_Sprite(eye_width, eye_height)
    #initialize offsets to be used for detected/tracked center points to image corner points
    global offset_x; offset_x = (int(output_width / 2) + int(input_video_width / 2))
    global offset_y; offset_y = (int(output_height / 2) - int(input_video_height / 2))
    #initialize blinking as global so accessory functions can monitor if the eye is blinking or not
    global blinking; blinking = False
    #initialize ball_in_hole as global so accesory functions can monitor if the ball is in the hole or not
    global ball_in_hole; ball_in_hole = False
    #initialize important points of reference
    global HOLE; HOLE = (int((output_width -  eye_width)/2),
                 int(output_height - eye_height))
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
    pygame.init()
    initialize_globals()
    #create a caption for the output display
    pygame.display.set_caption('Alien Eye')
     # initialize the video stream and allow the cammera sensor to warmup
    print("[INFO] starting video stream...")
    
    video_dims = (input_video_width, input_video_height)
    vs = VideoStream(src = 0, resolution = video_dims).start()
    #use FileVideoStream to read video from a file for testing
    #vs = FileVideoStream('no_vis_light.mp4').start()
    time.sleep(2.0)

    #Start running the detector and the tracker on seperate threads so that they won't bog down
    #the output display speed
    detector_thread = threading.Thread(target = run_machine_vision, args=(vs, stop_event))
    detector_thread.start()
    #setup signals to let the program capture user sent termiantion (SIGINT) and program sent termination (SIGTERM)
    signal.signal(signal.SIGTERM, service_shutdown)
    signal.signal(signal.SIGINT, service_shutdown)

    return detector_thread, vs

def main():
    #setup pygame, video stream, and detector thread; return detector thread and video strean so main can stop these later.
    detector_thread, vs = setup()
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
    try:
        while running:
            clock.tick(FRAMERATE)
            current_time = time.time()
            position, position_prev, designation = update_position(position, designation)
            eye_im_show = control_dilation(current_time)

            if not ball_in_hole:
                sequence_info = check_ball_in_hole(smoothed_position)
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
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    stop_event.set()
                    print("set_stop_event")

    except Service_Exit:
        stop_event.set()
    except KeyboardInterrupt:
        stop_event.set()

    finally:
        print('hit finally')
        while not q.empty():
            temp = q.get()
            q.task_done()
        q.join()
        detector_thread.join()
        vs.stop()
        pygame.quit()
        cv2.destroyAllWindows()
        print("Ended Gracefully")
        quit()
        
if __name__ == '__main__':
    main()