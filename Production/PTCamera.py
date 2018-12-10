from threading import Thread
import cv2
import numpy as np
import PyCapture2
import time
import yaml

class PTCamera:

	def __init__(self, resolution = (640, 480)):
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
			#	reduced by a factor of sixteen and image brightness is increased in all cases.
			#	Monochrome CCD models implement this binning mode vertically on the sensor and horizontally in the FPGA. There is
			#	an increase in image brightness and frame rate."
			#BE WARNED: Docs say to use "MODE.FC2_MODE_5", but that didn't work. Just had to guess until it did.
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
		self._camThread = Thread(target=self.update, args=())
		self._camThread.start()
		return self

	def update(self):
		# keep looping infinitely until the thread is stopped
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
		time_start = time.time()

def main():
	vs = PTCamera().start()
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