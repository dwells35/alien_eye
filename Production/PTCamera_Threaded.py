from threading import Thread
import cv2
import numpy as np
import PyCapture2
import time
import yaml

class PTCamera:
    """
    This class uses a threaded implementation of a GigE PT Grey Camera with the PyCapture2 API

    Attributes
    ----------
    stopped: boolean
        Flag indication whether or not the camera has been requested to stop image capture;
        used to terminate the camera thread

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

    start()
        Starts the camera thread

    update()
        Gets the newest frame from the camera continuously in a seperate thread from main thread

    read()
        Returns the newest frame from the camera as a numpy array

    stop()
        Stops camera thread; de-initializes the camera correctly
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

        self.stopped = False

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

    def start(self):
        """
        Start the camera thread via update function

        Returns
        -------
        self: PTCamera
            Returns self so it can be called in the same line as the constructor.
            EX.
                camera = PTCamera().start()
                
            This will both create the camera object and start the thread that
            will update the camera stream
        """

        self._camThread = Thread(target=self.update, args=())
        self._camThread.start()
        return self

    def update(self):
        """
        Get newest frame from the camera and convert it to a numpy ndarray

        Keep looping indefinitely until the thread is stopped
        """

        start_capture_time = time.time()
        count = 0
        while True:
            #.017 was determined emperically to nearly match machine vision and camera refresh rates
            time.sleep(.02)
            # if the thread indicator variable is set, stop the thread
            if self.stopped:
                print('Camera update stopped')
                break
        # otherwise, read the next frame from the stream
            try:
                image = self.c.retrieveBuffer()
                new_image = image.convert(PyCapture2.PIXEL_FORMAT.BGR)
                image_data = new_image.getData()
                self._frame = image_data.reshape((new_image.getRows(), new_image.getCols(), 3))
                #increment frame captured counter for fps calculation
                count += 1
            except PyCapture2.Fc2error as fc2Err:
                    print('Error retrieving buffer : %s' % fc2Err)
                    continue

        end_capture_time = time.time()
        fps = count / (end_capture_time - start_capture_time)
        print('Camera capture fps: ' + str(fps))

    def read(self):
        """
        Get an image from the camera and return it

        Returns
        -------
        self._frame: numpy ndarray
            Most recent image taken from the camera
        """
        return self._frame

    def stop(self):
        """
        Terminates camera update thread; disconnects the camera
        """

        # indicates that the thread should be stopped
        self.stopped = True
        self._camThread.join()
        self.c.stopCapture()
        self.c.disconnect()
        print("Camera acquisition stopped")
        time_start = time.time()


#Run PTCamera as main in order to test camera. This means running PTCamera directly
#from the command line; else, main will not run
#usage (Linux): 
#user@mycomputer: ~/[your path here]$ python3 PTCamera.py
def main():
    #Make sure to change resolution to appropriate values depending on which
    #camera mode is being used. An IIDC error will occur if a higher resolution is attempted to be set
    #than what is allowable for that mode
    vs = PTCamera(resolution = (640, 480)).start()
    running = True
    time_start = time.time()
    print('ran main')
    time.sleep(2)

    while running:
        current_time = time.time()
        frame = vs.read()
        time.sleep(.02)
        cv2.imshow('', frame)
        if current_time - time_start > 10:
            running = False
            vs.stop()
        cv2.waitKey(1)

if __name__ == '__main__':
    main()