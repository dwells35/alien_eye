import cv2
import numpy as np

class Deep_Detector:
    """This class sets up a detector based on a convolutional nerual network in the OpenCV DNN module
    
    Attribues
    ---------
    _prototxt : .txt file
        deploys the model
    _caffe_model : .caffemodel file
        points to the image database for the network
    _confidence : float, default = .5
        minimum confidence threshold required for the model to classify
        a detected face as a "face".
    _refresh_rate : float, default = 1
        frequency (in seconds) of the detector running (assuming tracker is running in the interem)

    Methods
    --------
    get_detections(frame)
        Returns an array of all detected faces in an inpute image (frame)

    get_detection_inds(detections)
        Returns a list of indices of the detected faces array for detections that
        meet or exceed the confidence threshold

    detection_box(detections, ind)
        Returns a bounding box of the detection chosen by indexing the detection array with the "ind"
        parameter

    """

    def __init__(self, prototxt, caffe_model, confidence = .5, refresh_rate = 1):
        """Creates a new detector with options to adjusts the confidence of a detected face, refresh rate of the detector (in seconds), and glance style (smooth or jerky)"""
        self._caffe_model = caffe_model
        self._prototxt = prototxt
        self._confidence = confidence
        self._refresh_rate = refresh_rate
        self._net = cv2.dnn.readNetFromCaffe(self._prototxt, self._caffe_model)

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
