import pygame
import random
import time

class Dilate_Sprite(pygame.sprite.Sprite):
    """
    This class creates an object used to control dilation behavior for the eye

    Extends pygame Sprite class

    Attributes
    ----------
    images: list
        list used to contain all images for the sprite

    MAX_DILATION_FRAME: int
        Constant used to set upper bound on how many dilation images are used for
        the dilation behavior. This number can range from 1 to 13

    index: int
        Curent index of the image list from which the calling function will
        retrieve an image

    image: pygame image
        Image selected out of the images list by index

    rect: pygame rectagle
        rectangular bounding box to contain the image

    dilate_req: boolean
        Flag indicating whether or not main control is requesting dilation to occur

    DILATE_TIME_OPEN: float
        Time the pupil remains in a "dilated open" state (aka, time the pupil is big)

    open_start_time: float
        Time since the eye has been in a fully dilated state

    dilate_open: boolean
        Flag indicating whether or not the eye is fully dilated

    dilating: boolean
        Flag indicating if the eye is currently in the process of dilation
        (either opening or closing)

    group_dilate: pygame Sprite Group
        group set up to hold dilation information

    dilate_clock: float
        Timer used to reference when updating the dilation animation

    DILATE_FRAMERATE: int
        Desired framerate of dilation in frames per second (fps)

    dilate_refresh_time: float
        Timer used to control how frequently the animation updates;
        derived from DILATE_FRAMERATE

    Methods
    -------
    dilate(current_time)
        Controls all dilation logic

    update()
        Increments the index used to grab images from the images list
    """

    def __init__(self, eye_width, eye_height):
        """
        Creates a new dilation sprite to be used for dilation animation

        Parameters
        ----------
        eye_width: tuple of ints
            width of the eye image requested as output

        eye_height: tuple of ints
            height of the eye image requested as output
        """
        super(Dilate_Sprite, self).__init__()
        self.images = []
        self.MAX_DILATION_FRAME = 7
        for i in range(0, self.MAX_DILATION_FRAME + 1):
            self.images.append(pygame.image.load('eye_dilation_images/Pupil dilation 0%s.png' % str(i)).convert_alpha())
        for i in range(self.MAX_DILATION_FRAME, -1, -1):
            self.images.append(pygame.image.load('eye_dilation_images/Pupil dilation 0%s.png' % str(i)).convert_alpha())
        for i in range(len(self.images)):
            self.images[i] = pygame.transform.scale(self.images[i], (eye_width, eye_height))
        self.index = 0
        self.image = self.images[self.index]
        self.rect = pygame.Rect(0, 0, eye_width, eye_height)
        self.dilate_req = False
        self.DILATE_TIME_OPEN = 1.0
        self.open_start_time = 0.0
        self.dilate_open = False
        self.dilating = False
        self.group_dilate = pygame.sprite.Group(self)
        self.dilate_clock = time.time()
        self.DILATE_FRAMERATE = 30
        self.dilate_refresh_time = (1 / self.DILATE_FRAMERATE)

    def dilate(self, current_time):
        """
        Control dilation behavior

        Parameters
        ----------
        current_time: float
            Time since the epoch; used to get current time of the main animation loop
        """
        if current_time - self.dilate_clock > self.dilate_refresh_time:
            self.dilate_clock = current_time
            if self.index <= len(self.images)/2:
                self.group_dilate.update()
                eye_im_show = self.images[self.index]
            elif self.index > len(self.images)/2 and not self.dilate_open:
                self.dilate_open = True
                self.open_start_time = time.time()
                eye_im_show = self.images[self.index]
            elif self.dilate_open and current_time - self.open_start_time > self.DILATE_TIME_OPEN:
                self.group_dilate.update()
                eye_im_show = self.images[self.index]
                if self.index == 0:
                    self.dilate_open = False
                    self.dilate_req = False
                    self.dilating = False
            else:
                eye_im_show = self.images[self.index]
        else:
            eye_im_show = self.images[self.index]

        return eye_im_show

    def update(self):
        """Increment the index of the image list"""
        self.index += 1
        if self.index >= len(self.images):
            self.index = 0
        self.image = self.images[self.index]
