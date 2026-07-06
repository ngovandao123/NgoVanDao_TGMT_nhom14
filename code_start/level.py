from settings import *
from sprites import Sprite, MovingSprite, AnimatedSprite, Spike, Item, ParticleEffectSprite
from player import Player
from groups import AllSprites
from enemies import Tooth, Shell, Pearl

from random import uniform

LEVEL_OBJECTIVES = {
	0: {'kills': 0, 'coins': 5, 'label': 'Lay chia khoa so 1 tren con tau'},
	1: {'kills': 2, 'coins': 8, 'label': 'Lay chia khoa so 2 o ben ca'},
	2: {'kills': 1, 'coins': 10, 'label': 'Lay chia khoa so 3 trong hang da'},
	3: {'kills': 2, 'coins': 8, 'label': 'Lay chia khoa so 4 o rung may'},
	4: {'kills': 2, 'coins': 10, 'label': 'Lay chia khoa so 5 trong thap den'},
	5: {'kills': 2, 'coins': 10, 'label': 'Lay chia khoa so 6 de mo ruong'}
}

TOTAL_KEYS = len(LEVEL_OBJECTIVES)

EASY_REMOVE_OBJECTS = {
	1: {
		'Objects': {65, 98, 99, 100, 101, 104, 105, 106, 107, 108, 135, 136, 137, 138, 139, 141, 142, 143, 144, 145, 147, 154, 173, 174},
		'Moving Objects': {68, 219},
		'Enemies': {157, 159, 161, 162, 164, 165}
	},
	2: {
		'Objects': {89, 90, 134, 135, 140, 142, 143, 178, 179, 189, 191, 192},
		'Moving Objects': {81, 133},
		'Enemies': set()
	},
	3: {
		'Objects': {71},
		'Moving Objects': {68},
		'Enemies': set()
	},
	4: {
		'Objects': {91, 134, 135, 140, 142, 178, 179, 189, 191, 192},
		'Moving Objects': {133, 137, 234},
		'Enemies': {225, 227, 228}
	},
	5: {
		'Objects': {71},
		'Moving Objects': {68},
		'Enemies': set()
	}
}

class Level:
	def __init__(self, tmx_map, level_frames, audio_files, data, switch_stage, input_controller = None):
		self.display_surface = pygame.display.get_surface()
		self.data = data
		self.switch_stage = switch_stage
		self.input_controller = input_controller

		# level data 
		self.level_width = tmx_map.width * TILE_SIZE
		self.level_bottom = tmx_map.height * TILE_SIZE
		tmx_level_properties = tmx_map.get_layer_by_name('Data')[0].properties
		self.level_unlock = tmx_level_properties['level_unlock']
		if tmx_level_properties['bg']:
			bg_tile = level_frames['bg_tiles'][tmx_level_properties['bg']]
		else:
			bg_tile = None

		# groups 
		self.all_sprites = AllSprites(
			width = tmx_map.width, 
			height = tmx_map.height,
			bg_tile = bg_tile, 
			top_limit = tmx_level_properties['top_limit'], 
			clouds = {'large': level_frames['cloud_large'], 'small': level_frames['cloud_small']},
			horizon_line = tmx_level_properties['horizon_line'])
		self.collision_sprites = pygame.sprite.Group()
		self.semi_collision_sprites = pygame.sprite.Group()
		self.damage_sprites = pygame.sprite.Group()
		self.tooth_sprites = pygame.sprite.Group()
		self.shell_sprites = pygame.sprite.Group()
		self.pearl_sprites = pygame.sprite.Group()
		self.item_sprites = pygame.sprite.Group()

		self.setup(tmx_map, level_frames, audio_files)
		self.setup_objectives()

		# frames 
		self.pearl_surf = level_frames['pearl']
		self.particle_frames = level_frames['particle']

		# audio
		self.coin_sound = audio_files['coin']
		self.coin_sound.set_volume(0.4)
		self.damage_sound = audio_files['damage']
		self.damage_sound.set_volume(0.5)
		self.pearl_sound = audio_files['pearl']
		self.objective_font = pygame.font.Font(None, 28)
		self.objective_notice_until = 0

	def should_skip_object(self, layer_name, obj):
		level_rules = EASY_REMOVE_OBJECTS.get(self.data.current_level, {})
		try:
			object_id = int(getattr(obj, 'id', -1))
		except (TypeError, ValueError):
			return False
		return object_id in level_rules.get(layer_name, set())

	def setup_objectives(self):
		objective = LEVEL_OBJECTIVES.get(self.data.current_level, {'kills': 0, 'coins': 0, 'label': 'Hoan thanh man'})
		total_enemies = len(self.tooth_sprites) + len(self.shell_sprites)
		self.objective_label = objective['label']
		self.required_kills = min(objective['kills'], total_enemies)
		self.required_coins = objective['coins']
		self.enemies_defeated = 0
		self.coins_collected = 0
		self.key_collected = self.data.has_key(self.data.current_level)

	def objectives_complete(self):
		return self.key_collected and self.enemies_defeated >= self.required_kills and self.coins_collected >= self.required_coins

	def setup(self, tmx_map, level_frames, audio_files):
		# tiles 
		for layer in ['BG', 'Terrain', 'FG', 'Platforms']:
			for x, y, surf in tmx_map.get_layer_by_name(layer).tiles():
				groups = [self.all_sprites]
				if layer == 'Terrain': groups.append(self.collision_sprites)
				if layer == 'Platforms': groups.append(self.semi_collision_sprites)
				match layer:
					case 'BG': z = Z_LAYERS['bg tiles']
					case 'FG': z = Z_LAYERS['bg tiles']
					case _: z = Z_LAYERS['main']

				Sprite((x * TILE_SIZE,y * TILE_SIZE), surf, groups, z)

		# bg details
		for obj in tmx_map.get_layer_by_name('BG details'):
			if obj.name == 'static':
				Sprite((obj.x, obj.y), obj.image, self.all_sprites, z = Z_LAYERS['bg tiles'])
			else:
				AnimatedSprite((obj.x, obj.y), level_frames[obj.name], self.all_sprites, Z_LAYERS['bg tiles'])
				if obj.name == 'candle':
					AnimatedSprite((obj.x, obj.y) + vector(-20,-20), level_frames['candle_light'], self.all_sprites, Z_LAYERS['bg tiles'])
		
		# objects 
		for obj in tmx_map.get_layer_by_name('Objects'):
			if self.should_skip_object('Objects', obj):
				continue
			if obj.name == 'player':
				self.player = Player(
					pos = (obj.x, obj.y), 
					groups = self.all_sprites, 
					collision_sprites = self.collision_sprites, 
					semi_collision_sprites = self.semi_collision_sprites,
					frames = level_frames['player'], 
					data = self.data, 
					attack_sound = audio_files['attack'],
					jump_sound = audio_files['jump'],
					input_controller = self.input_controller)
			else:
				if obj.name in ('barrel', 'crate'):
					Sprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites))
				else:
					# frames 
					frames = level_frames[obj.name] if not 'palm' in obj.name else level_frames['palms'][obj.name]
					if obj.name == 'floor_spike' and obj.properties['inverted']:
						frames = [pygame.transform.flip(frame, False, True) for frame in frames]

					# groups 
					groups = [self.all_sprites]
					if obj.name in('palm_small', 'palm_large'): groups.append(self.semi_collision_sprites)
					if obj.name in ('saw', 'floor_spike'): groups.append(self.damage_sprites)

					# z index
					z = Z_LAYERS['main'] if not 'bg' in obj.name else Z_LAYERS['bg details']

					# animation speed
					animation_speed = ANIMATION_SPEED if not 'palm' in obj.name else ANIMATION_SPEED + uniform(-1,1)
					AnimatedSprite((obj.x, obj.y), frames, groups, z, animation_speed)
			if obj.name == 'flag':
				self.level_finish_rect = pygame.Rect((obj.x, obj.y), (obj.width, obj.height))

		# moving objects 
		for obj in tmx_map.get_layer_by_name('Moving Objects'):
			if self.should_skip_object('Moving Objects', obj):
				continue
			if obj.name == 'spike':
				Spike(
					pos = (obj.x + obj.width / 2, obj.y + obj.height / 2),
					surf = level_frames['spike'],
					radius = obj.properties['radius'],
					speed = obj.properties['speed'],
					start_angle = obj.properties['start_angle'],
					end_angle = obj.properties['end_angle'],
					groups = (self.all_sprites, self.damage_sprites))
				for radius in range(0, obj.properties['radius'], 20):
					Spike(
						pos = (obj.x + obj.width / 2, obj.y + obj.height / 2),
						surf = level_frames['spike_chain'],
						radius = radius,
						speed = obj.properties['speed'],
						start_angle = obj.properties['start_angle'],
						end_angle = obj.properties['end_angle'],
						groups = self.all_sprites,
						z = Z_LAYERS['bg details'])

			else:
				frames = level_frames[obj.name]
				groups = (self.all_sprites, self.semi_collision_sprites) if obj.properties['platform'] else (self.all_sprites, self.damage_sprites)
				if obj.width > obj.height: # horizontal
					move_dir = 'x'
					start_pos = (obj.x, obj.y + obj.height / 2)
					end_pos = (obj.x + obj.width,obj.y + obj.height / 2)
				else: # vertical 
					move_dir = 'y'
					start_pos = (obj.x + obj.width / 2, obj.y)
					end_pos = (obj.x + obj.width / 2,obj.y + obj.height)
				speed = obj.properties['speed']
				MovingSprite(frames, groups, start_pos, end_pos, move_dir, speed, obj.properties['flip'])

				if obj.name == 'saw':
					if move_dir == 'x':
						y = start_pos[1] - level_frames['saw_chain'].get_height() / 2
						left, right = int(start_pos[0]), int(end_pos[0])
						for x in range(left, right, 20):
							Sprite((x,y), level_frames['saw_chain'], self.all_sprites, Z_LAYERS['bg details'])
					else:
						x = start_pos[0] - level_frames['saw_chain'].get_width() / 2
						top, bottom = int(start_pos[1]), int(end_pos[1])
						for y in range(top, bottom, 20):
							Sprite((x,y), level_frames['saw_chain'], self.all_sprites, Z_LAYERS['bg details'])

		# enemies 
		for obj in tmx_map.get_layer_by_name('Enemies'):
			if self.should_skip_object('Enemies', obj):
				continue
			if obj.name == 'tooth':
				Tooth((obj.x, obj.y), level_frames['tooth'], (self.all_sprites, self.damage_sprites, self.tooth_sprites), self.collision_sprites)
			if obj.name == 'shell':
				Shell(
					pos = (obj.x, obj.y), 
					frames = level_frames['shell'], 
					groups = (self.all_sprites, self.collision_sprites, self.shell_sprites), 
					reverse = obj.properties['reverse'], 
					player = self.player, 
					create_pearl = self.create_pearl)

		# items 
		for obj in tmx_map.get_layer_by_name('Items'):
			Item(obj.name, (obj.x + TILE_SIZE / 2, obj.y + TILE_SIZE / 2), level_frames['items'][obj.name], (self.all_sprites, self.item_sprites), self.data)

		# water 
		for obj in tmx_map.get_layer_by_name('Water'):
			rows = int(obj.height / TILE_SIZE) 
			cols = int(obj.width / TILE_SIZE) 
			for row in range(rows):
				for col in range(cols):
					x = obj.x + col * TILE_SIZE
					y = obj.y + row * TILE_SIZE
					if row == 0:
						AnimatedSprite((x,y), level_frames['water_top'], self.all_sprites, Z_LAYERS['water'])
					else:
						Sprite((x,y), level_frames['water_body'], self.all_sprites, Z_LAYERS['water'])

	def create_pearl(self, pos, direction):
		Pearl(pos, (self.all_sprites, self.damage_sprites, self.pearl_sprites), self.pearl_surf, direction, 150)
		self.pearl_sound.play()

	def pearl_collision(self):
		for sprite in self.collision_sprites:
			sprite = pygame.sprite.spritecollide(sprite, self.pearl_sprites, True)
			if sprite:
				ParticleEffectSprite((sprite[0].rect.center), self.particle_frames, self.all_sprites)

	def hit_collision(self):
		for sprite in self.damage_sprites:
			if sprite.rect.colliderect(self.player.hitbox_rect):
				self.player.get_damage()
				self.damage_sound.play()
				if hasattr(sprite, 'pearl'):
					sprite.kill()
					ParticleEffectSprite((sprite.rect.center), self.particle_frames, self.all_sprites)

	def item_collision(self):
		if self.item_sprites:
			item_sprites = pygame.sprite.spritecollide(self.player, self.item_sprites, True)
			if item_sprites:
				for item_sprite in item_sprites:
					if item_sprite.item_type == 'diamond':
						self.key_collected = True
					self.coins_collected += self.item_coin_value(item_sprite.item_type)
					item_sprite.activate()
					ParticleEffectSprite((item_sprite.rect.center), self.particle_frames, self.all_sprites)
				self.coin_sound.play()

	def item_coin_value(self, item_type):
		values = {
			'silver': 1,
			'gold': 5,
			'diamond': 20,
			'skull': 50,
			'potion': 0
		}
		return values.get(item_type, 0)

	def attack_collision(self):
		if not self.player.attacking:
			return

		attack_rect = self.player_attack_rect()
		for target in self.tooth_sprites.sprites() + self.shell_sprites.sprites():
			if target.rect.colliderect(attack_rect):
				ParticleEffectSprite(target.rect.center, self.particle_frames, self.all_sprites)
				target.kill()
				self.enemies_defeated += 1

		for pearl in self.pearl_sprites:
			if pearl.rect.colliderect(attack_rect):
				pearl.reverse()

	def player_attack_rect(self):
		width, height = 96, 70
		top = self.player.hitbox_rect.centery - height / 2
		if self.player.facing_right:
			left = self.player.hitbox_rect.right - 8
		else:
			left = self.player.hitbox_rect.left - width + 8
		return pygame.Rect(left, top, width, height)

	def check_constraint(self):
		# left right
		if self.player.hitbox_rect.left <= 0:
			self.player.hitbox_rect.left = 0
		if self.player.hitbox_rect.right >= self.level_width:
			self.player.hitbox_rect.right = self.level_width

		# bottom border 
		if self.player.hitbox_rect.bottom > self.level_bottom:
			self.switch_stage('overworld', -1)

		# success 
		if self.player.hitbox_rect.colliderect(self.level_finish_rect):
			if self.objectives_complete():
				self.data.collect_key(self.data.current_level)
				self.switch_stage('overworld', self.level_unlock)
			else:
				self.objective_notice_until = pygame.time.get_ticks() + 1600

	def draw_objectives(self):
		key_status = 'DA NHAT' if self.key_collected else 'CHUA'
		lines = [
			f'NV: {self.objective_label}',
			f'Chia khoa: {key_status}   Tong: {len(self.data.keys_collected)}/{TOTAL_KEYS}',
			f'Quai: {self.enemies_defeated}/{self.required_kills}   Xu: {self.coins_collected}/{self.required_coins}'
		]
		if self.objectives_complete():
			lines.append('Da xong nhiem vu - toi la co!')
		elif pygame.time.get_ticks() < self.objective_notice_until:
			lines.append('Can chia khoa, xu va quai truoc khi cham co!')

		for index, line in enumerate(lines):
			text_surf = self.objective_font.render(line, True, '#f5f1de')
			text_rect = text_surf.get_rect(topleft = (16, 72 + index * 24))
			bg_rect = text_rect.inflate(12, 6)
			pygame.draw.rect(self.display_surface, '#111018', bg_rect)
			self.display_surface.blit(text_surf, text_rect)

	def run(self, dt):
		self.display_surface.fill('black')
		
		self.all_sprites.update(dt)
		self.pearl_collision()
		self.attack_collision()
		self.hit_collision()
		self.item_collision()
		self.check_constraint()
		
		self.all_sprites.draw(self.player.hitbox_rect.center, dt)
		self.draw_objectives()
