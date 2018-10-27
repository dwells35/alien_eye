def blink_increment(last_step, is_rising, background_height):
	if last_step < (background_height / 2) and is_rising:
		new_step = last_step + 10
	elif last_step == (background_height / 2):
		is_rising = False
		new_step = last_step - 10
	elif last_step == 0 and not is_rising:
		new_step = 0
		is_rising = False
	return (new_step, is_rising)

def blink_display(frame, new_step, background_width, background_height):
	frame[0:new_step, 0:background_width] = black[0:new_step, 0:background_width]
	frame[background_height:(background_height-1):-1, 0:background_width] = black[0:new_step, 0:background_width]
	return frame