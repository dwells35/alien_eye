import dlib
import cv2
class Tracker:
    """Uses dlib's correlation tracker and provides methods to track a given image"""

    def __init__(self, quality_threshold = 5):
        """Create a tracker that uses dlib's correlation tracker"""
        self._tracker = dlib.correlation_tracker()
        self._quality_threshold = quality_threshold
    def get_tracker(self):
        """Returns the correlation tracker"""
        return self._tracker

    def get_quality_threshold(self):
        """Return the quality threshold for the tracker"""
        return self._quality_threshold

    def get_track_quality(self, frame):
        """Return the quality of the track as a value from 0 to 9"""
        return self._tracker.update(frame)

    def update_position(self, frame):
        """Return the center of the tracked region containing a face"""
        tracked_position = self._tracker.get_position()

        #print('position: ' + str(tracked_position))
        t_x = int(tracked_position.left())
        t_y = int(tracked_position.top())
        t_w = int(tracked_position.width())
        t_h = int(tracked_position.height())

        cv2.rectangle(frame, (t_x, t_y), (t_x + t_w, t_y + t_h),
                           (255, 0, 0), 2)

        center = tracked_position.center()
        return center

