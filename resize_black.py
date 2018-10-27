import cv2

black = cv2.imread('black.jpg')
black = cv2.resize(black, (1800, 1080))
cv2.imwrite('black.jpg', black)