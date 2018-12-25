from threading import Thread
import cv2
import numpy as np
import PyCapture2
import time
import yaml

class PTCamera:
    """
    This class creates an object used to control a GigE PT Grey Camera with the PyCapture2 API

    Attributes
    ----------
    c: PyCapture2 GigECamera
        PTGrey GigE Camera used for image capture

    _frame_req: boolean
        Flag indicating wheter or not another frame is being requested from the camera

    _frame: numpy ndarray
        PyCapture2 Image captured from the camera converted to a numpy array

    Methods
    -------
    initialize_camera_settings(resolution)
        Sets up camera with desired settings; settings read in from a yaml configuration file

    update()
        Gets the newest frame from the camera

    read()
        Returns the newest frame from the camera as a numpy array

    stop()
        De-initializes the camera correctly
    """

    def __init__(self, resolution = (320, 240)):
        """
        Create a new instance of a PTCamera which uses PyCapture2's GigECamera API

        Parameters
        ----------
        resolution: tuple of ints; default: (320, 240)
            Resolution of desired input video stream; default is 320x240 which will make sure the camera
            initialization will not error out regardless of the capture mode selected.
        """

        #self._update_count = 0
        # Ensure sufficient cameras are found
        bus = PyCapture2.BusManager()
        num_cams = bus.getNumOfCameras()
        print('Number of cameras detected: ', num_cams)
        if not num_cams:
            print('Insufficient number of cameras. Exiting...')
            exit()
            
        # Select camera on 0th index
        self.c = PyCapture2.GigECamera()
        uid = bus.getCameraFromIndex(0)
        self.c.connect(uid)
        self.initialize_camera_settings(resolution)
        
        
        print('Starting image capture...')
        self.c.startCapture()
        self._frame_req = True

    def initialize_camera_settings(self, resolution):
        try:
            self.c.setGigEImageSettings(offsetX = 0, offsetY = 0, width = resolution[0], \
                                        height = resolution[1], pixel_format = PyCapture2.PIXEL_FORMAT.MONO8)
            #From Documentation:
            #  "Mode 5 is 4x4 binning. Implementation and impact on frame rate varies between models. Effective resolution is
            #   reduced by a factor of sixteen and image brightness is increased in all cases.
            #   Monochrome CCD models implement this binning mode vertically on the sensor and horizontally in the FPGA. There is
            #   an increase in image brightness and frame rate."
            #BE WARNED: Docs say to use "MODE.FC2_MODE_5", but that didn't work. Just had to guess until it did.
            #NOTE: May need to use Mode 1 if better resolution required
            self.c.setGigEImagingMode(PyCapture2.MODE.MODE_1)
            max_packet_size = self.c.discoverGigEPacketSize()
            self.c.setGigEProperty(propType = PyCapture2.GIGE_PROPERTY_TYPE.GIGE_PACKET_SIZE, value = max_packet_size)

            with open('camera_config.yml', 'r') as f:
                settings = yaml.load(f)

            for p in settings:
                #print(settings[p])
                self.c.setProperty(type = eval(settings[p]['type']), present = settings[p]['present'], \
                                    absControl = settings[p]['absControl'], onePush = eval(settings[p]['onePush']), \
                                    onOff = eval(settings[p]['onOff']), autoManualMode = eval(settings[p]['autoManualMode']), \
                                    ValueA = eval(settings[p]['ValueA']), ValueB = eval(settings[p]['ValueB']), \
                                    absValue = eval(settings[p]['absValue']))


        except PyCapture2.Fc2error as fc2Err:
            print('Error setting up camera : ', fc2Err)
            print("Make sure you aren't trying to set a setting that is impossible \n \
                    e.g. any resolution above 640x480 for MODE_1")
            self.c.disconnect()
            quit()

    def update(self):
        """
        Get newest frame from the camera and convert it to a numpy ndarray
        """
        
        try:
            image = self.c.retrieveBuffer()
            new_image = image.convert(PyCapture2.PIXEL_FORMAT.BGR)
            image_data = new_image.getData()
            self._frame = image_data.reshape((new_image.getRows(), new_image.getCols(), 3))
            #increment frame captured counter for fps calculation
            #self._update_count += 1
        except PyCapture2.Fc2error as fc2Err:
                print('Error retrieving buffer : %s' % fc2Err)

    def read(self):
        """
        Get an image from the camera and return it

        Returns
        -------
        self._frame: numpy ndarray
            Most recent image taken from the camera
        """

        #if self._update_count == 0:
        #   self._start_capture_time = time.time()
        self.update()
        return self._frame

    def stop(self):
        """
        Stops camera capturing; disconnects the camera
        """

        #self._end_capture_time = time.time()
        #fps = self._update_count / (self._end_capture_time - self._start_capture_time)
        #print('Camera capture fps: ' + str(fps))
        self.c.stopCapture()
        self.c.disconnect()
        print("Camera acquisition stopped")
