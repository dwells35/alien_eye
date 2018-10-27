import cv2
import numpy as np
import sys
class Cv_image_wrapper:
    """This class is used to read in and change images for use with the displayed output from OpenCV"""
    
    def __init__(self, file_path):
        """Use provided image path to create an OpenCV image"""
        self._file_path = file_path
        image = cv2.imread(self._file_path)
        self._width, self._height = image.shape[:2]
        if image.all() == None:
            sys.exit("File at path: %s \ncould not be opened." % _file_path)

    def get_height(self):
        """Return the height of the image"""
        return self._height

    def get_width(self):
        """Return the width of the image"""
        return self._width

    def get_image_path(self):
        """Return the image path of the image"""
        return self._file_path

