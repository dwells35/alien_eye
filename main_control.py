
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


def display(frame, position_list, center, lrbt, im_dims):
    """Dispay the eye image"""
    left, right, bottom, top = lrbt
    position_list = du.add_center_point(position_list, center)
    avgCenter = du.avg_center(position_list)
    aLeft, aRight, aBottom, aTop = du.get_roi(avgCenter[0] - im_dims[0], avgCenter[0] + im_dims[0], avgCenter[1] - im_dims[1], avgCenter[1] + im_dims[1], eye_image, background_image)

    background_image[bottom:top, left:right] = black_cover
    background_image[aBottom:aTop, aLeft:aRight] = eye_image
    cv2.imshow('Face_Tracking_Output', background_image)

    left = aLeft
    right = aRight
    bottom = aBottom
    top = aTop

    return left, right, bottom, top

#Use this to toggle optional features useful for debugging. Set to False for production.
DEBUG = True

# load our serialized model from disk
print("[INFO] loading model...")
net = Deep_detector('deploy.prototxt.txt','res10_300x300_ssd_iter_140000.caffemodel', refresh_rate = 100)

#initialize a tracker
print("[INFO] initializing tracker")
tracker = Tracker(quality_threshold = 6)

#initialize trackingFace as False because no face is being tracked yet.
#Count is number of frames (cumulative) that the camera has read in.
trackingFace = False
count = 0

# initialize the video stream and allow the cammera sensor to warmup
print("[INFO] starting video stream...")
input_video_width = 480
input_video_height = 480
vs = VideoStream(src=0, resolution=(input_video_width,input_video_height)).start()
#vs = FileVideoStream('no_vis_light.mp4').start()
time.sleep(2.0)

eye_image = cv2.imread('cartoon_eye_squashed.png')
background_image = cv2.imread('cream_background.png')
black_cover = cv2.imread('small_cream.png')

#initializes the size boundaries of the output images; this can be changed by changing the video size and/or changing what integer
#is in the dividend
left = 0
right = eye_image.shape[1]
bottom = 0
top = eye_image.shape[0]
lrbt = (left, right, bottom, top)

offset_y = (int(background_image.shape[0] / 2) - int(input_video_height / 2))
offset_x = (int(background_image.shape[1] / 2) + int(input_video_height / 2))

im_dims = (int(eye_image.shape[1] / 2), int(eye_image.shape[0] / 2))


#initializes a list of however many point you want to use for the moving average that smooths the video output
num_avg_points = 6
position_list = [(0, 0)] * num_avg_points

#initializes "tracked_center_raw" so that comparison on line 104 doesn't error out on first scan
tracked_center_raw = dlib.point(0,0)

#begin detecting/tracking
while True:
 
    # get next frame; increment frame counter by 1
    frame = vs.read()
    frame = imutils.resize(frame, width=input_video_width)
    count = count + 1

    if not trackingFace or count > net.get_refresh_rate():
        count = 0
        if DEBUG:
            print('detector ran')
        #get detected faces from the input frame
        detections = net.get_detections(frame)

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
            '''
            if abs(detected_center_raw[0] - tracked_center_raw.x) < 20 and abs(detected_center_raw[1] - tracked_center_raw.y) < 20:
                if len(indeces) > 1:
                    num = (num + 1) % len(indeces)
                    ind_of_interest = indeces[num]
                    (startX, startY, endX, endY) = net.detection_box(detections, ind_of_interest)
                    detected_center_raw = (int((endX - startX) / 2) + startX, int((endY - startY) / 2) + startY)
            '''
            #move the center of the detected face to a corresponding place in the output image
            #i.e., if the face was found in the center of the camera input image, and the camera image
            #was 480x480, then center = (240, 240), but the output image is much larger (maybe 1080x1080),
            #so the center value must be mapped to the center of the output image in order for things to look
            #correct
            detected_center = (offset_x - detected_center_raw[0], detected_center_raw[1] + offset_y)

            #display the image to the console
            left, right, bottom, top = display(frame, position_list, detected_center, lrbt, im_dims)
            lrbt = (left, right, bottom, top)

            if (startX * startY) > 0:
                tracker.get_tracker().start_track(frame, 
                                    dlib.rectangle( startX + 10,
                                                    startY - 20,
                                                    endX + 10,
                                                    endY + 20))
                trackingFace = True

        if DEBUG:
            if len(indeces) > 0:
                cv2.rectangle(frame, (startX, startY), (endX, endY),
                (0, 0, 255), 2)
                cv2.rectangle(frame, (detected_center[0] - 5, detected_center[1] - 5), (detected_center[0] + 5, detected_center[1] + 5), (0,255,0), 2)
            cv2.imshow('main frame', frame)

    if trackingFace:
        track_quality = tracker.get_track_quality(frame)
        if track_quality >= tracker.get_quality_threshold():
            count = count + 1
            tracked_center_raw = tracker.update_position(frame)
            tracked_center = (offset_x - tracked_center_raw.x, tracked_center_raw.y + offset_y)
            left, right, bottom, top = display(frame, position_list, tracked_center, lrbt, im_dims)
            lrbt = (left, right, bottom, top)
        else:
            trackingFace = False
        if DEBUG:
            cv2.imshow('main frame', frame)

    cv2.waitKey(2)

    if 0xFF == ord('q'):
        break

vs.stop()
cv2.destroyAllWindows()




