import pygame
import random
import time

class Blink_Sprite(pygame.sprite.Sprite):
    """
    This class creates an object used to control dilation behavior for the eye

    Extends pygame Sprite class

    Attributes
    ----------
    images: list
        list used to contain all images for the sprite

    index: int
        Curent index of the image list from which the calling function will
        retrieve an image

    MAX_INDEX: int
        Maximum index of the image list. Used to control how many times the update method
        is called

    image: pygame image
        Image selected out of the images list by index

    rect: pygame rectagle
        rectangular bounding box to contain the image

    last_blink_time: float
        Time in seconds since last blink (time since the epoch; must compare with current_time
        for a time delta: e.g. delta_t = current_time - last_blink_time)

    rand_blink_time: float
        Time in seconds between a lower and upper bound, randomly selected. Used to trigger
        next blink (gives blinking a more realistic feel)

    group_blink: pygame Sprite Group
        group set up to hold blinking information

    blink_clock: float
        Timer used to reference when updating the blinking animation

    BLINK_FRAMERATE: int
        Desired framerate of dilation in frames per second (fps)

    blink_refresh_time: float
        Timer used to control how frequently the animation updates;
        derived from BLINK_FRAMERATE

    Methods
    -------
    update()
        Increments the index used to grab images from the images list
    """
    def __init__(self, output_width, output_height):
        """
        Create a new blinking sprite to be used for blink animation

        Parameters
        ----------
        output_width: int
            Width of the output display

        output_height: int
            Height of the output display
        """
        super(Blink_Sprite, self).__init__()
        self.images = []
        for i in range(1, 10, 1):
            self.images.append(pygame.image.load('blink_images/Nictitating membrane update2 0%s.png' % str(i)).convert_alpha())
        for i in range(9,0,-1):
            self.images.append(pygame.image.load('blink_images/Nictitating membrane update2 0%s.png' % str(i)).convert_alpha())
        for i in range(len(self.images)):
            self.images[i] = pygame.transform.scale(self.images[i], (output_width, output_height))

        self.index = 0
        self.MAX_INDEX = len(self.images) - 1
        self.image = self.images[self.index]
        self.rect = pygame.Rect(0,0,output_width, output_height)
        self.last_blink_time = 0.0
        self.rand_blink_time = random.uniform(3, 6)
        self.group_blink = pygame.sprite.Group(self)
        self.blink_clock = time.time()
        self.BLINK_FRAMERATE = 50
        self.blink_refresh_time = (1 / self.BLINK_FRAMERATE)

    def update(self):
        """Increment the index of the image list"""
        self.index += 1
        if self.index >= len(self.images):
            self.index = 0
        self.image = self.images[self.index]