from settings import * 
from sprites import Sprite, AnimatedSprite, Node, Icon, PathSprite
from groups import WorldSprites
from random import randint

class Overworld:
	def __init__(self, tmx_map, data, overworld_frames, switch_stage, input_controller = None):
		self.display_surface = pygame.display.get_surface()
		self.data = data 
		self.switch_stage = switch_stage
		self.input_controller = input_controller

		# groups 
		self.all_sprites = WorldSprites(data)
		self.node_sprites = pygame.sprite.Group()

		self.setup(tmx_map, overworld_frames)

		self.current_node = [node for node in self.node_sprites if node.level == self.data.current_level][0]

		self.path_frames = overworld_frames['path']
		self.create_path_sprites()

	def setup(self, tmx_map, overworld_frames):
		# tiles 
		for layer in ['main', 'top']:
			for x, y, surf in tmx_map.get_layer_by_name(layer).tiles():
				Sprite((x * TILE_SIZE,y * TILE_SIZE), surf, self.all_sprites, Z_LAYERS['bg tiles'])

		# water 
		for col in range(tmx_map.width):
			for row in range(tmx_map.height):
				AnimatedSprite((col * TILE_SIZE,row * TILE_SIZE), overworld_frames['water'], self.all_sprites, Z_LAYERS['bg'])

		# objects 
		for obj in tmx_map.get_layer_by_name('Objects'):
			if obj.name == 'palm':
				AnimatedSprite((obj.x, obj.y), overworld_frames['palms'], self.all_sprites, Z_LAYERS['main'], randint(4,6))
			else:
				layer_key = 'bg details' if obj.name == 'grass' else 'bg tiles'
				z = Z_LAYERS[layer_key]
				Sprite((obj.x, obj.y), obj.image, self.all_sprites, z)

		# paths
		self.paths = {}
		for obj in tmx_map.get_layer_by_name('Paths'):
			pos = [(int(p.x + TILE_SIZE / 2),int( p.y + TILE_SIZE / 2)) for p in obj.points]
			start = obj.properties['start'] 
			end  = obj.properties['end'] 
			self.paths[end] = {'pos': pos, 'start': start}

		# nodes & player 
		for obj in tmx_map.get_layer_by_name('Nodes'):

			# player
			if obj.name == 'Node' and obj.properties['stage'] == self.data.current_level:
				self.icon = Icon((obj.x + TILE_SIZE / 2, obj.y + TILE_SIZE / 2), self.all_sprites, overworld_frames['icon'])

			# nodes 
			if obj.name == 'Node':
				available_paths = {k:v for k,v in obj.properties.items() if k in ('left', 'right', 'up', 'down')}
				Node(
					pos = (obj.x, obj.y), 
					surf = overworld_frames['path']['node'], 
					groups = (self.all_sprites, self.node_sprites),
					level = obj.properties['stage'],
					data = self.data,
					paths = available_paths)

	def create_path_sprites(self):

		# get tiles from path 
		nodes = {node.level: vector(node.grid_pos) for node in self.node_sprites}
		path_tiles = {}

		for path_id, data in self.paths.items():
			path = data['pos']
			start_node, end_node = nodes[data['start']], nodes[path_id]
			path_tiles[path_id] = [start_node]

			for index, points in enumerate(path):
				if index < len(path) - 1:
					start, end = vector(points), vector(path[index + 1])
					path_dir = (end - start) / TILE_SIZE
					start_tile = vector(int(start[0]/ TILE_SIZE), int(start[1]/ TILE_SIZE))

					if path_dir.y:
						dir_y = 1 if path_dir.y > 0 else -1
						for y in range(dir_y, int(path_dir.y) + dir_y, dir_y):
							path_tiles[path_id].append(start_tile + vector(0,y))

					if path_dir.x:
						dir_x = 1 if path_dir.x > 0 else -1
						for x in range(dir_x, int(path_dir.x) + dir_x, dir_x):
							path_tiles[path_id].append(start_tile + vector(x,0))

			path_tiles[path_id].append(end_node)

		# create sprites 
		for key, path in path_tiles.items():
			for index, tile in enumerate(path):
				if index > 0 and index < len(path) - 1:
					prev_tile = path[index - 1] - tile
					next_tile = path[index + 1] - tile

					if prev_tile.x == next_tile.x:
						surf = self.path_frames['vertical']
					elif prev_tile.y == next_tile.y:
						surf = self.path_frames['horizontal']
					else:
						if prev_tile.x == -1 and next_tile.y == -1 or prev_tile.y == -1 and next_tile.x == -1:
							surf = self.path_frames['tl']
						elif prev_tile.x == 1 and next_tile.y == 1 or prev_tile.y == 1 and next_tile.x == 1:
							surf = self.path_frames['br']
						elif prev_tile.x == -1 and next_tile.y == 1 or prev_tile.y == 1 and next_tile.x == -1:
							surf = self.path_frames['bl']
						elif prev_tile.x == 1 and next_tile.y == -1 or prev_tile.y == -1 and next_tile.x == 1:
							surf = self.path_frames['tr']
						else:
							surf = self.path_frames['horizontal']

					PathSprite(
						pos = (tile.x * TILE_SIZE, tile.y * TILE_SIZE), 
						surf = surf, 
						groups = self.all_sprites, 
						level = key)

	def input(self):
		keys = pygame.key.get_pressed()
		gesture = self.input_controller
		if not self.current_node or self.icon.path:
			return

		requested_direction = self.requested_direction(keys, gesture)
		if requested_direction:
			move_direction = self.direction_for_request(requested_direction)
			if move_direction:
				self.move(move_direction)

		if keys[pygame.K_RETURN] or gesture and gesture.just_pressed('confirm'):
			self.data.current_level = self.current_node.level
			self.switch_stage('level')

	def requested_direction(self, keys, gesture):
		if keys[pygame.K_LEFT] or gesture and gesture.pressed('left'):
			return 'left'
		if keys[pygame.K_RIGHT] or gesture and gesture.pressed('right'):
			return 'right'
		if keys[pygame.K_UP] or gesture and gesture.pressed('up'):
			return 'up'
		if keys[pygame.K_DOWN] or gesture and gesture.pressed('down'):
			return 'down'

	def direction_for_request(self, requested_direction):
		if self.can_follow_path(requested_direction):
			return requested_direction

		current_level = self.current_node.level
		candidates = []
		for direction in self.current_node.paths:
			if not self.can_follow_path(direction):
				continue
			target_level = self.path_target_level(direction)
			if requested_direction in ('right', 'down') and target_level > current_level:
				candidates.append((target_level - current_level, direction))
			if requested_direction in ('left', 'up') and target_level < current_level:
				candidates.append((current_level - target_level, direction))

		if candidates:
			return sorted(candidates)[0][1]

	def can_follow_path(self, direction):
		return direction in self.current_node.paths and self.path_target_level(direction) <= self.data.unlocked_level

	def path_target_level(self, direction):
		path_id = str(self.current_node.paths[direction])
		digits = ''.join(char for char in path_id if char.isdigit())
		return int(digits)

	def move(self, direction):
		path_key = self.path_target_level(direction)
		path_reverse = True if self.current_node.paths[direction][-1] == 'r' else False
		path = self.paths[path_key]['pos'][:] if not path_reverse else self.paths[path_key]['pos'][::-1]
		self.icon.start_move(path)

	def get_current_node(self):
		nodes = pygame.sprite.spritecollide(self.icon, self.node_sprites, False)
		if nodes:
			self.current_node = nodes[0]

	def run(self, dt):
		self.input()
		self.get_current_node()
		self.all_sprites.update(dt)
		self.all_sprites.draw(self.icon.rect.center)
