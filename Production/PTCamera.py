from threading import Thread
import cv2
import numpy as np
import PyCapture2
from ServiceExit import ServiceExit

class PTCamera:

	def __init__(self):
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
		set_camera_propterties(c)
		self.c.setGigEImageSettings(offsetX = 0, offsetY = 0, width = 640, height = 480, pixel_format = PyCapture2.PIXEL_FORMAT.MONO8)
		
		
		print('Starting image capture...')
		self.c.startCapture()
		


	def set_camera_properties(c):
		'''
		type (int)
		present (bool)
		absControl (bool)
		onePush (bool)
		onOff (bool)
		autoManualMode (bool)
		valueA (int)
		valueB (int)
		absValue (float)
		Note that type MUST be specified if this method of calling is used.
		Information about these properties can be found in the Property documentation.
		Ex. camera.setProperty(type = PyCapture2.PROPERTY_TYPE.ZOOM, absValue = 2.0) Sets
		zoom to 2.

		CHANGEABLE PARAMETERS:
		Brightness
		Exposure Time (Shutter Speed)
		Gain
		Auto Exposure
		Sharpness
		Gamma
		'''
		#set brightness
		



	def start(self):
		self._camThread = Thread(target=self.update, args=())
		self._camThread.start()
		return self

	def update(self):
		# keep looping infinitely until the thread is stopped
		while True:
			# if the thread indicator variable is set, stop the thread
			if self.stopped:
				return

			# otherwise, read the next frame from the stream
			try:
				image = self.c.retrieveBuffer()
				new_image = image.convert(PyCapture2.PIXEL_FORMAT.BGR)
				image_data = new_image.getData()
				self._frame = image_data.reshape((new_image.getRows(), new_image.getCols(), 3))
			except PyCapture2.Fc2error as fc2Err:
		    		print('Error retrieving buffer : %s' % fc2Err)
		    		continue
	'''
	def convertToCVmat(self, pImage):

		convertedImage = pImage.Convert(PySpin.PixelFormat_BGR8, PySpin.NEAREST_NEIGHBOR);

		XPadding = convertedImage.GetXPadding()
		YPadding = convertedImage.GetYPadding();
		rowsize = convertedImage.GetWidth();
		colsize = convertedImage.GetHeight();
		print("XPadding: " + str(XPadding))
		print("YPadding: " + str(YPadding))
		print("rowsize: " + str(rowsize))
		print("colsize: " + str(colsize))

		#image data contains padding. When allocating Mat container size, you need to account for the X,Y image data padding. 
		#row_bytes = float(len(pImage.GetData()))/float(pImage.GetHeight())
		cvimg = np.array(convertedImage.GetData()).reshape(colsize + YPadding, rowsize + XPadding, 3)
		cv2.imshow('Image',cvimg)
		return cvimg
	'''
	def read(self):
		# return the frame most recently read
		return self._frame

	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True
		self.c.stopCapture()
		self.c.disconnect()
		print("Camera acquisition stopped")