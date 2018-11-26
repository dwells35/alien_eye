import cv2
import numpy as np

class Deep_Detector:
    """This class sets up a detector based on a convolutional nerual network in the OpenCV DNN module"""

    def __init__(self, prototxt, caffe_model, confidence = .5, refresh_rate = 1, glance_style = 'smooth'):
        """Creates a new detector with options to adjusts the confidence of a detected face, refresh rate of the detector (in seconds), and glance style (smooth or jerky)"""
        self._caffe_model = caffe_model
        self._prototxt = prototxt
        self._confidence = confidence
        self._refresh_rate = refresh_rate
        self._glance_style = glance_style
        self._net = cv2.dnn.readNetFromCaffe(self._prototxt, self._caffe_model)

    def get_refresh_rate(self):
        """Return the refresh rate in milliseconds for the detector"""
        return self._refresh_rate

    def get_glance_style(self):
        """Return the glance style as a string for the detector"""
        return self._glance_style

    def get_confidence(self):
        """Return the confidence threshold for the detector to classify a face"""
        return self._confidence

    def get_detections(self, frame):
        """Return a list of integers that represent indeces in an array of detections"""

        # grab the frame dimensions and convert it to a blob
        (h, w) = frame.shape[:2]
        self._h, self._w = (h, w)
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0,
            (300, 300), (104.0, 177.0, 123.0))
    
        # pass the blob through the network and obtain the detections and
        # predictions
        self._net.setInput(blob)
        detections = self._net.forward()
        return detections

    def get_detection_inds(self, detections):
        #initialize index list
        inds = []

        # loop over the detections
        for i in range(0, detections.shape[2]):
            # extract the confidence (i.e., probability) associated with the
            # prediction
            confidence = detections[0, 0, i, 2]

            # filter out weak detections by ensuring the `confidence` is
            # greater than the minimum confidence
            if confidence >= self._confidence:
                inds.append(i)
        return inds

    def detection_box(self, detections, ind):
        # compute the (x, y)-coordinates of the bounding box for the
        # object
        box = detections[0, 0, ind, 3:7] * np.array([self._w, self._h, self._w, self._h])
        return box.astype("int")
