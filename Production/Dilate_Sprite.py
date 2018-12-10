import pygame
import random
import time

class Dilate_Sprite(pygame.sprite.Sprite):
    def __init__(self, eye_width, eye_height):
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
        self.dilate_time_open = 1
        self.open_start_time = 0
        self.dilate_open = False
        self.dilating = False
        self.group_dilate = pygame.sprite.Group(self)
        self.dilate_clock = time.time()
        self.DILATE_FRAMERATE = 30
        self.dilate_refresh_time = (1 / self.DILATE_FRAMERATE)

    def dilate(self, current_time):
        if current_time - self.dilate_clock > self.dilate_refresh_time:
            self.dilate_clock = current_time
            if self.index <= len(self.images)/2:
                self.group_dilate.update()
                eye_im_show = self.images[self.index]
            elif self.index > len(self.images)/2 and not self.dilate_open:
                self.dilate_open = True
                self.open_start_time = time.time()
                eye_im_show = self.images[self.index]
            elif self.dilate_open and current_time - self.open_start_time > self.dilate_time_open:
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
        self.index += 1
        if self.index >= len(self.images):
            self.index = 0
        self.image = self.images[self.index]
