import display_utils as du
from imutils.video import VideoStream
from imutils.video import FileVideoStream
from Deep_detector import Deep_detector
from Tracker import Tracker
import time
import random
import imutils
import cv2
import dlib
import pygame
from queue import Queue
import threading
import signal

class BlinkSprite(pygame.sprite.Sprite):
    def __init__(self):
        super(BlinkSprite, self).__init__()
        self.images = []
        for i in range(0, 11, 3):
            self.images.append(pygame.image.load('blink_ims/rect%s.png' % str(i + 1)))
        for i in range(10,0,-3):
            self.images.append(pygame.image.load('blink_ims/rect%s.png' % str(i + 1)))
        self.index = 0
        self.image = self.images[self.index]
        self.rect = pygame.Rect(0,0,1920,1080)

    def update(self):
        self.index += 1
        if self.index >= len(self.images):
            self.index = 0
        self.image = self.images[self.index]

    def blink(group, out_display, self):
        group.update()
        group.draw(out_display)
        if self.index == 12:
            blinking = False
        return blinking

class DilateClose(pygame.sprite.Sprite):
    def __init__(self):
        super(DilateClose, self).__init__()
        self.images = []
        for i in range(0, 7):
            self.images.append(pygame.image.load('eye_dilation/eye_dil%s.png' % str(i + 1)))
        self.index = 0
        self.image = self.images[self.index]
        self.rect = pygame.Rect(0, 0, 480, 480)

    def update(self):
        self.index += 1
        if self.index >= len(self.images):
            self.index = 0
        self.image = self.images[self.index]

class DilateOpen(pygame.sprite.Sprite):
    def __init__(self):
        super(DilateOpen, self).__init__()
        self.images = []
        for i in range(7, 0, -1):
            self.images.append(pygame.image.load('eye_dilation/eye_dil%s.png' % str(i)))
        self.index = 0
        self.image = self.images[self.index]
        self.rect = pygame.Rect(0, 0, 480, 480)

    def update(self):
        self.index += 1
        if self.index >= len(self.images):
            self.index = 0
        self.image = self.images[self.index]



class ServiceExit(Exception):
    """
    Custom exception which is used to trigger the clean exit
    of all running threads and the main program.
    """
    pass

def service_shutdown(signum, frame):
    raise ServiceExit


def display(eye_im, corner, position_list, out_display, group, blink_sprite, blinking):
    position_list = du.add_center_point(position_list, corner)
    avg_corner = du.avg_center(position_list)
    out_display.fill((255, 255, 255))
    out_display.blit(eye_im, avg_corner)
    if blinking:
        blinking = blink_sprite.blink(group, out_display)
    
    return blinking


def run_detector(vs, q, eye_image, video_dims, DEBUG, stop_event):
    # load our serialized model from disk
    print("[INFO] loading model...")
    net = Deep_detector('deploy.prototxt.txt','res10_300x300_ssd_iter_140000.caffemodel', refresh_rate = 2000)

    #initialize a tracker
    print("[INFO] initializing tracker")
    tracker = Tracker(quality_threshold = 6)

    
    display_width = 1920
    display_height = 1080
    input_video_width, input_video_height = video_dims
    
    offset_x = (int(display_width / 2) + int(input_video_width / 2))
    offset_y = (int(display_height / 2) - int(input_video_height / 2))
   
    count = 0
    trackingFace = False
    while not stop_event.is_set():
        # get next increment frame counter by 1
        frame = vs.read()
        frame = imutils.resize(frame, width=input_video_width)


        if not trackingFace or count > net.get_refresh_rate():
            #get detected faces from the input frame
            detections = net.get_detections(frame)
            count = 0

            if DEBUG:
                print('detector ran')


            #get indeces of the detections array that correspond to detections that have a probability greater
            #than the detector's confidence threshold of actually being a face
            indeces = net.get_detection_inds(detections)

            if len(indeces) > 0:

                #pick a random index from that list of indeces (this way, if there are multiple people,
                #the alien won't get fixated on just one person)
                num = random.randint(0, len(indeces) - 1)
                ind_of_interest = indeces[num]

                #use detections array and our random index (random face) to get the center of the found face in the input video
                (startX, startY, endX, endY) = net.detection_box(detections, ind_of_interest)
                detected_center_raw = (int((endX - startX) / 2) + startX, int((endY - startY) / 2) + startY)
                
                #move the center of the detected face to a corresponding place in the output image
                #i.e., if the face was found in the center of the camera input image, and the camera image
                #was 480x480, then center = (240, 240), but the output image is much larger (maybe 1080x1080),
                #so the center value must be mapped to the center of the output image in order for things to look
                #correct
                detected_center = (offset_x - detected_center_raw[0], detected_center_raw[1] + offset_y)
                im_out_corner = (detected_center[0] - eye_image.get_width()/2, detected_center[1] - eye_image.get_height()/2)
                if not q.full():
                    q.put(im_out_corner)

                if DEBUG:
                    if len(indeces) > 0:
                        cv2.rectangle(frame, (startX, startY), (endX, endY),
                        (0, 0, 255), 2)
                        cv2.rectangle(frame, (detected_center[0] - 5, detected_center[1] - 5), (detected_center[0] + 5, detected_center[1] + 5), (0,255,0), 2)
                        cv2.imshow('main frame', frame)
                
                if (startX * startY) > 0:
                    tracker.get_tracker().start_track(frame, 
                                        dlib.rectangle( startX + 10,
                                                        startY - 20,
                                                        endX + 10,
                                                        endY + 20))
                    trackingFace = True

        if trackingFace:

            track_quality = tracker.get_track_quality(frame)
            if track_quality >= tracker.get_quality_threshold():
                count = count + 1
                tracked_center_raw = tracker.update_position(frame)
                tracked_center = (offset_x - tracked_center_raw.x, tracked_center_raw.y + offset_y)
                im_out_corner = (tracked_center[0] - eye_image.get_width()/2, tracked_center[1] - eye_image.get_height()/2)
                if not q.full():
                    q.put(im_out_corner)
            else:
                trackingFace = False 
            
            if DEBUG:
                cv2.imshow('main frame', frame)

        cv2.waitKey(2)






def main():
    q = Queue(maxsize=6)
    pygame.init()

    #Use this to toggle optional features useful for debugging. Set to False for production.
    DEBUG = True

    output_width = 1920
    output_height = 1080

    out_display = pygame.display.set_mode((output_width, output_height))
    pygame.display.set_caption('Alien Eye')

    #eye_image = cv2.imread('cartoon_eye_squashed.png')
    eye_image = pygame.image.load('cartoon_eye_squashed.png')
    eye_image_dil = pygame.image.load('eye_dilation/eye_dil7.png')
    #background_im = cv2.imread('cream_background.png')
    #cover_im = cv2.imread('small_cream.png')

    #Setting up a stop event in order to make sure the threads finish gracefully when the program is stopped
    stop_event = threading.Event()

    # initialize the video stream and allow the cammera sensor to warmup
    print("[INFO] starting video stream...")
    input_video_width = 480
    input_video_height = 480
    video_dims = (input_video_width, input_video_height)
    vs = VideoStream(src=0, resolution=(input_video_width,input_video_height)).start()
    #vs = FileVideoStream('no_vis_light.mp4').start()
    time.sleep(2.0)

    #Start running the detector and the tracker on seperate threads so that they won't bog down
    #the output display speed
    detector_thread = threading.Thread(target = run_detector, args=(vs, q, eye_image, video_dims, DEBUG, stop_event))
    detector_thread.start()

    #initializes a list of however many point you want to use for the moving average that smooths the video output
    num_avg_points = 6
    position_list = [(0, 0)] * num_avg_points

    #initializes "tracked_center_raw" so that comparison on line 104 doesn't error out on first scan
    tracked_center_raw = dlib.point(0,0)

    corner_point = (0,0)
    trackingFace = False

    running = True

    signal.signal(signal.SIGTERM, service_shutdown)
    signal.signal(signal.SIGINT, service_shutdown)
    frame_count = 0
    clock = pygame.time.Clock()

    blink_sprite = BlinkSprite()
    dilate_close = DilateClose()
    dilate_open = DilateOpen()

    group_close = pygame.sprite.Group(dilate_close)
    group_open = pygame.sprite.Group(dilate_open)
    group = pygame.sprite.Group(blink_sprite)
    blinking = False
    dilating_close = False
    dilating_open = False
    small_pupil = False
    ball_in_hole = False

    try:
        start = time.time()
        dil_start = time.time()
        while running:
            clock.tick(90)
            frame_count = frame_count + 1
            if not q.empty():
                corner_point = q.get()
                #print(corner_point)
                q.task_done()

            #blinking = display(eye_image, corner_point, position_list, out_display, group, blink_sprite, blinking)
            if (time.time() - dil_start > random.randint(3, 7) or dilating_close) and not small_pupil:
                dilating_close = True
                group_close.update()
                if dilate_close.index > 0:
                    eye_im_show = dilate_close.images[dilate_close.index]
                else:
                    eye_im_show = dilate_close.images[6]
                    dilating_close = False
                    small_pupil = True
                    print("closed")
                    dil_start = time.time()

            elif (time.time() - dil_start > random.randint(3, 7) or dilating_open) and small_pupil:
                dilating_open = True
                group_close.update()
                if dilate_open.index > 0:
                    eye_im_show = dilate_open.images[dilate_open.index]
                else:
                    eye_im_show = dilate_open.images[6]
                    print("opened")
                    dilating_open = False
                    small_pupil = False
                    dil_start = time.time()

            elif not dilating_close and not small_pupil:
                print('open eye')
                eye_im_show = eye_image

            elif small_pupil:
                eye_im_show = dilate_close.images[6]
                print('close eye')

            else:
                eye_im_show = eye_image
                print('default')



            if frame_count > random.randint(90, 1000):
                blinking = True
                frame_count = 0
            if not ball_in_hole:
                position_list = du.add_center_point(position_list, corner_point)
                avg_corner = du.avg_center(position_list)
                out_display.fill((255, 255, 255))
                out_display.blit(eye_im_show, avg_corner)

            if ball_in_hole:
                position_list = du.add_center_point(position_list, (int(output_width/2) - int(eye_image.get_width()/2), output_height - eye_image.get_height()))
                avg_corner = du.avg_center(position_list)
                out_display.fill((255, 255, 255))
                out_display.blit(eye_im_show, avg_corner)
                if time.time() - look_time_start > 4:
                    ball_in_hole = False


            if blinking:
                group.update()
                group.draw(out_display)
                if blink_sprite.index == 7:
                    blinking = False

            pygame.display.update()

            if pygame.key.get_pressed()[pygame.K_h]:
                look_time_start = time.time()
                ball_in_hole = True
            

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    end = time.time()
                    total_time = (end - start)
                    fps = frame_count/total_time
                    print("total time: " + str(total_time))
                    print("fps: " + str(fps))
                    stop_event.set()
                    print("set_stop_event")


    except ServiceExit:
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