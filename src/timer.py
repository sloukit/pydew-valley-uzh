import pygame
# from settings import *

class Timer:
	def __init__(self, duration, repeat = False, autostart = False, func = None):
		'''
		Initializes the Timer.

		:param duration: Duration for the timer in milliseconds
		:param repeat: If True, the timer will restart automatically aafter deactivation.
		:param autostart: If True, the timer will start immediately upon creation.
		:param func: A function to be called when the timer expires.
		'''
		self.duration = duration
		self.start_time = 0
		self.active = False
		self.repeat = repeat
		self.func = func
		
		if autostart:
			self.activate()

	def __bool__(self):
		return self.active

	def activate(self):
		'''Activates the timer'''
		self.active = True
		self.start_time = pygame.time.get_ticks()

	def deactivate(self):
		'''Deactivates the timer and reactivates it if repeat is True'''
		self.active = False
		self.start_time = 0
		if self.repeat:
			self.activate()

	def update(self):
		'''Updates the timer status. Should be called regularly to check timer status'''
		if self.active:
			if pygame.time.get_ticks() - self.start_time >= self.duration:
				if self.func and self.start_time != 0: self.func()
				self.deactivate()