class Data:
	def __init__(self, ui):
		self.ui = ui
		self._coins = 0
		self._health = 5
		self.ui.create_hearts(self._health)

		self.unlocked_level = 0
		self.current_level = 0
		self.keys_collected = set()

	def collect_key(self, level):
		self.keys_collected.add(level)

	def has_key(self, level):
		return level in self.keys_collected

	@property
	def coins(self):
		return self._coins

	@coins.setter
	def coins(self, value):
		self._coins = value
		if self.coins >= 100:
			self.coins -= 100
			self.health += 1
		self.ui.show_coins(self.coins)

	@property
	def health(self):
		return self._health

	@health.setter
	def health(self, value):
		self._health = value
		self.ui.create_hearts(value)
