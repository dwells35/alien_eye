import cv2
import numpy as np

class Deep_Detector:
    """
    This class sets up a detector based on a convolutional nerual network in the OpenCV DNN module

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
        """
        Creates a new detector with options to adjusts the confidence of a detected face
        and refresh rate of the detector (in seconds)

        Attributes
        ----------
        _prototxt : .txt file
            deploys the model

        _caffe_model : .caffemodel file
            points to the image database for the network

        _confidence : float, default = .5
            minimum confidence threshold required for the model to classify
            a detected face as a "face".
            
        _refresh_rate : float, default = 1
            frequency (in seconds) of the detector running (assuming tracker is running in the interem)
        """

        self._caffe_model = caffe_model
        self._prototxt = prototxt
        self._confidence = confidence
        self._refresh_rate = refresh_rate
        self._net = cv2.dnn.readNetFromCaffe(self._prototxt, self._caffe_model)


    def get_detections(self, frame):
        """
        Return a 4D array of detections

        Attributes
        ----------
        frame: numpy ndarray
            frame retrieved from camera as a numpy array

        Notes
        -----
        How to read the detections array:
        # = no idea what this detection index corresponds to
            (have to read model source code for this info)

            Detections array format:
            [#, #, i, k]

            i: index of detected face; each 'i' is a face
            k: can range from 1-7
                1: object classification as a string (not used in this application)
                2: confidence
                3-7: bounding box coordinates
        """

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
        """
        Return a list of indices corresponding to faces in the detections array
        that meet or exceed the instance confidence threshold

        Attributes
        ----------
        detections: numpy ndarray
            4D array of detected faces
        """

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
        """Return a bounding box for the detected face"""

        # compute the (x, y)-coordinates of the bounding box for the
        # object
        box = detections[0, 0, ind, 3:7] * np.array([self._w, self._h, self._w, self._h])
        return box.astype("int")
