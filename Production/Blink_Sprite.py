import pygame
import random
import time

class Blink_Sprite(pygame.sprite.Sprite):
    def __init__(self, output_width, output_height):
        super(Blink_Sprite, self).__init__()
        self.images = []
        for i in range(1, 10, 1):
            self.images.append(pygame.image.load('blink_ims_2/Nictitating membrane update2 0%s.png' % str(i)).convert_alpha())
        for i in range(9,0,-1):
            self.images.append(pygame.image.load('blink_ims_2/Nictitating membrane update2 0%s.png' % str(i)).convert_alpha())
        for i in range(len(self.images)):
            self.images[i] = pygame.transform.scale(self.images[i], (output_width, output_height))

        self.index = 0
        self.image = self.images[self.index]
        self.rect = pygame.Rect(0,0,output_width, output_height)
        self.last_blink_time = 0
        self.rand_blink_time = random.uniform(3, 6)
        self.group_blink = pygame.sprite.Group(self)
        self.blink_clock = time.time()
        self.BLINK_FRAMERATE = 50
        self.blink_refresh_time = (1 / self.BLINK_FRAMERATE)

    def update(self):
        self.index += 1
        if self.index >= len(self.images):
            self.index = 0
        self.image = self.images[self.index]

    def blink(self, group, out_display):
        group.update()
        group.draw(out_display)
        if self.index == 12:
            blinking = False
        return blinking