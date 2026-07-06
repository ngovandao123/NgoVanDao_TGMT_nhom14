from settings import * 
from level import Level
from pytmx.util_pygame import load_pygame
from support import * 
from data import Data
from debug import debug
from ui import UI
from overworld import Overworld
from gesture_controller import GestureController

INTRO_DURATION = 16000
QUIT_HOLD_DURATION = 900

INTRO_PANELS = (
	(0, 4000, 'BIEN CA STARLIGHT', 'Ngay xua, ngon hai dang giu yen binh cho ca vung bien.'),
	(4000, 8000, 'RUONG KHO BAU BI KHOA', 'Mot dem, sau chia khoa pha le bi danh cap va giau tren cac hon dao.'),
	(8000, 12000, 'HANH TRINH SAU CHIA KHOA', 'Moi man giu mot chia khoa dan toi ruong vang cuoi ban do.'),
	(12000, INTRO_DURATION, 'THUYEN TRUONG NHO', 'Ban len duong, gom du chia khoa va mo lai kho bau Starlight.')
)

STORY_CHAPTERS = (
	{
		'title': 'CHUONG 1 - CON TAU MAC CAN',
		'lines': (
			'Ban tim thay con thuyen dau tien tren dong nuoc day banh rang.',
			'Chia khoa pha le dau tien nam giua dong tien vang tren mui thuyen.',
			'Hay lay no roi cham co de mo loi den dao tiep theo.'
		)
	},
	{
		'title': 'CHUONG 2 - BEN CA BO HOANG',
		'lines': (
			'Ngu dan bien mat, chi con nhung dong tien vang bi bo lai.',
			'Mau chia khoa thu hai phat sang sau nhung buc tuong muc nat.',
			'Ha it nhat mot ke canh gac va lay chia khoa truoc khi roi ben.'
		)
	},
	{
		'title': 'CHUONG 3 - DAO DA XANH',
		'lines': (
			'Ban do chi den mot hang da phat sang mau xanh la.',
			'Chia khoa thu ba nam sau nhung bac da cao va cac bay sat.',
			'Thu thap du xu, lay chia khoa roi tim loi ra khoi hang.'
		)
	},
	{
		'title': 'CHUONG 4 - RUNG MAY',
		'lines': (
			'Nhung cay cau treo dua ban len cao, gan hon voi mat bao.',
			'Quai vat canh rung giu chia khoa thu tu cua con duong cu.',
			'Di theo cac buc thang may va dung de mat dau vet tren cao.'
		)
	},
	{
		'title': 'CHUONG 5 - THAP DEN HONG',
		'lines': (
			'Hai dang Starlight da tat, chi con anh sang hong chay lap loe.',
			'May moc va gai sat bao ve chia khoa thu nam tren dinh thap.',
			'Lay chia khoa nay de danh dau loi vao dao kho bau.'
		)
	},
	{
		'title': 'CHUONG CUOI - LA CO VANG',
		'lines': (
			'Ruong kho bau nam o hon dao cuoi cung, nhung no can du sau chia khoa.',
			'Lay chia khoa cuoi, vuot qua ke canh gac va cham co de mo ruong.',
			'Khi ruong mo ra, bien Starlight se tu do.'
		)
	}
)

class Game:
	def __init__(self):
		pygame.init()
		self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
		pygame.display.set_caption('Super Pirate World')
		self.clock = pygame.time.Clock()
		self.gesture_controller = GestureController()
		self.import_assets()

		self.tmx_maps = {
			0: load_pygame(project_path('data', 'levels', '0.tmx')),
			1: load_pygame(project_path('data', 'levels', '1.tmx')),
			2: load_pygame(project_path('data', 'levels', '2.tmx')),
			3: load_pygame(project_path('data', 'levels', '3.tmx')),
			4: load_pygame(project_path('data', 'levels', '4.tmx')),
			5: load_pygame(project_path('data', 'levels', '6.tmx')),
			}
		self.max_level = max(self.tmx_maps)
		self.tmx_overworld = load_pygame(project_path('data', 'overworld', 'overworld.tmx'))
		self.game_over = False
		self.menu_mode = None
		self.menu_title = ''
		self.game_over_options = ()
		self.game_over_index = 0
		self.app_state = 'intro'
		self.intro_start_time = pygame.time.get_ticks()
		self.quit_hold_start = None
		self.story_level = 0
		self.current_stage = None
		self.ui = None
		self.data = None
		self.bg_music.play(-1)

	def start_new_game(self):
		self.ui = UI(self.font, self.ui_frames)
		self.data = Data(self.ui)
		self.current_stage = Overworld(self.tmx_overworld, self.data, self.overworld_frames, self.switch_stage, self.gesture_controller)
		self.app_state = 'game'
		self.game_over = False
		self.menu_mode = None
		self.game_over_index = 0

	def switch_stage(self, target, unlock = 0):
		if target == 'level':
			self.open_story(self.data.current_level)
			
		else: # overworld 
			if unlock > 0:
				if self.data.current_level >= self.max_level:
					if len(self.data.keys_collected) >= self.max_level + 1:
						self.open_menu('victory')
					else:
						self.current_stage = Overworld(self.tmx_overworld, self.data, self.overworld_frames, self.switch_stage, self.gesture_controller)
					return
				next_level = min(self.data.current_level + 1, self.max_level)
				self.data.unlocked_level = max(self.data.unlocked_level, next_level)
			else:
				self.data.health -= 1
				if self.data.health <= 0:
					self.open_menu('death')
					return
			self.current_stage = Overworld(self.tmx_overworld, self.data, self.overworld_frames, self.switch_stage, self.gesture_controller)

	def open_story(self, level):
		self.story_level = level
		self.app_state = 'story'

	def start_story_level(self):
		self.current_stage = Level(self.tmx_maps[self.story_level], self.level_frames, self.audio_files, self.data, self.switch_stage, self.gesture_controller)
		self.app_state = 'game'

	def import_assets(self):
		self.level_frames = {
			'flag': import_folder('..', 'graphics', 'level', 'flag'),
			'saw': import_folder('..', 'graphics', 'enemies', 'saw', 'animation'),
			'floor_spike': import_folder('..', 'graphics','enemies', 'floor_spikes'),
			'palms': import_sub_folders('..', 'graphics', 'level', 'palms'),
			'candle': import_folder('..', 'graphics','level', 'candle'),
			'window': import_folder('..', 'graphics','level', 'window'),
			'big_chain': import_folder('..', 'graphics','level', 'big_chains'),
			'small_chain': import_folder('..', 'graphics','level', 'small_chains'),
			'candle_light': import_folder('..', 'graphics','level', 'candle light'),
			'player': import_sub_folders('..', 'graphics','player'),
			'saw': import_folder('..', 'graphics', 'enemies', 'saw', 'animation'),
			'saw_chain': import_image('..',  'graphics', 'enemies', 'saw', 'saw_chain'),
			'helicopter': import_folder('..', 'graphics', 'level', 'helicopter'),
			'boat': import_folder('..',  'graphics', 'objects', 'boat'),
			'spike': import_image('..',  'graphics', 'enemies', 'spike_ball', 'Spiked Ball'),
			'spike_chain': import_image('..',  'graphics', 'enemies', 'spike_ball', 'spiked_chain'),
			'tooth': import_folder('..', 'graphics','enemies', 'tooth', 'run'),
			'shell': import_sub_folders('..', 'graphics','enemies', 'shell'),
			'pearl': import_image('..',  'graphics', 'enemies', 'bullets', 'pearl'),
			'items': import_sub_folders('..', 'graphics', 'items'),
			'particle': import_folder('..', 'graphics', 'effects', 'particle'),
			'water_top': import_folder('..', 'graphics', 'level', 'water', 'top'),
			'water_body': import_image('..', 'graphics', 'level', 'water', 'body'),
			'bg_tiles': import_folder_dict('..', 'graphics', 'level', 'bg', 'tiles'),
			'cloud_small': import_folder('..', 'graphics','level', 'clouds', 'small'),
			'cloud_large': import_image('..', 'graphics','level', 'clouds', 'large_cloud'),
		}
		self.font = pygame.font.Font(project_path('graphics', 'ui', 'runescape_uf.ttf'), 40)
		self.menu_title_font = pygame.font.Font(project_path('graphics', 'ui', 'runescape_uf.ttf'), 72)
		self.story_title_font = pygame.font.Font(project_path('graphics', 'ui', 'runescape_uf.ttf'), 52)
		self.menu_font = pygame.font.Font(project_path('graphics', 'ui', 'runescape_uf.ttf'), 34)
		self.preview_font = pygame.font.Font(None, 24)
		self.ui_frames = {
			'heart': import_folder('..', 'graphics', 'ui', 'heart'), 
			'coin':import_image('..', 'graphics', 'ui', 'coin')
		}
		self.overworld_frames = {
			'palms': import_folder('..', 'graphics', 'overworld', 'palm'),
			'water': import_folder('..', 'graphics', 'overworld', 'water'),
			'path': import_folder_dict('..', 'graphics', 'overworld', 'path'),
			'icon': import_sub_folders('..', 'graphics', 'overworld', 'icon'),
		}

		self.audio_files = {
			'coin': pygame.mixer.Sound(project_path('audio', 'coin.wav')),
			'attack': pygame.mixer.Sound(project_path('audio', 'attack.wav')),
			'jump': pygame.mixer.Sound(project_path('audio', 'jump.wav')), 
			'damage': pygame.mixer.Sound(project_path('audio', 'damage.wav')),
			'pearl': pygame.mixer.Sound(project_path('audio', 'pearl.wav')),
		}
		self.bg_music = pygame.mixer.Sound(project_path('audio', 'starlight_city.mp3'))
		self.bg_music.set_volume(0.5)

	def check_game_over(self):
		if self.data.health <= 0:
			self.open_menu('death')

	def open_menu(self, mode):
		self.game_over = True
		self.menu_mode = mode
		self.game_over_index = 0
		if mode == 'victory':
			self.menu_title = 'RUONG KHO BAU MO RA'
			self.game_over_options = ('CHOI LAI', 'THOAT')
		else:
			self.menu_title = 'GAME OVER'
			self.game_over_options = ('CHOI LAI', 'RA MAP')

	def handle_game_over_event(self, event):
		if event.type != pygame.KEYDOWN:
			return

		if event.key in (pygame.K_UP, pygame.K_w):
			self.move_game_over_selection(-1)
		if event.key in (pygame.K_DOWN, pygame.K_s):
			self.move_game_over_selection(1)
		if event.key in (pygame.K_RETURN, pygame.K_SPACE):
			self.confirm_game_over_selection()

	def update_game_over_input(self):
		if self.gesture_controller.just_pressed('up'):
			self.move_game_over_selection(-1)
		if self.gesture_controller.just_pressed('down'):
			self.move_game_over_selection(1)
		if self.gesture_controller.just_pressed('confirm'):
			self.confirm_game_over_selection()

	def move_game_over_selection(self, amount):
		self.game_over_index = (self.game_over_index + amount) % len(self.game_over_options)

	def confirm_game_over_selection(self):
		option = self.game_over_options[self.game_over_index]
		if option == 'CHOI LAI' and self.menu_mode == 'death':
			self.restart_current_level()
		elif option == 'CHOI LAI':
			self.start_new_game()
		elif option == 'RA MAP':
			self.return_to_map()
		else: # THOAT
			self.quit_game()

	def restart_current_level(self):
		self.data.health = 5
		self.current_stage = Level(self.tmx_maps[self.data.current_level], self.level_frames, self.audio_files, self.data, self.switch_stage, self.gesture_controller)
		self.game_over = False
		self.menu_mode = None
		self.game_over_index = 0

	def return_to_map(self):
		self.data.health = 5
		self.current_stage = Overworld(self.tmx_overworld, self.data, self.overworld_frames, self.switch_stage, self.gesture_controller)
		self.game_over = False
		self.menu_mode = None
		self.game_over_index = 0

	def quit_game(self):
		self.gesture_controller.close()
		pygame.quit()
		sys.exit()

	def update_quit_gesture(self):
		if not self.gesture_controller.pressed('quit'):
			self.quit_hold_start = None
			return

		current_time = pygame.time.get_ticks()
		if self.quit_hold_start is None:
			self.quit_hold_start = current_time
		if current_time - self.quit_hold_start >= QUIT_HOLD_DURATION:
			self.quit_game()

	def handle_intro_event(self, event):
		if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
			self.app_state = 'play_menu'

	def update_intro(self):
		if pygame.time.get_ticks() - self.intro_start_time >= INTRO_DURATION:
			self.app_state = 'play_menu'

	def draw_intro(self):
		elapsed = pygame.time.get_ticks() - self.intro_start_time
		self.display_surface.fill('#07111f')

		pygame.draw.ellipse(self.display_surface, '#f5f1de', (WINDOW_WIDTH - 210, 70, 90, 90))
		pygame.draw.rect(self.display_surface, '#10243c', (0, WINDOW_HEIGHT - 150, WINDOW_WIDTH, 150))
		for wave in range(0, WINDOW_WIDTH + 80, 80):
			pygame.draw.arc(self.display_surface, '#58a6b6', (wave - 40, WINDOW_HEIGHT - 130, 100, 45), 0, 3.14, 3)

		title, body = INTRO_PANELS[-1][2], INTRO_PANELS[-1][3]
		for start, end, panel_title, panel_body in INTRO_PANELS:
			if start <= elapsed < end:
				title, body = panel_title, panel_body
				break

		title_surf = self.menu_title_font.render(title, True, '#ffd166')
		title_rect = title_surf.get_rect(center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 60))
		self.display_surface.blit(title_surf, title_rect)

		body_surf = self.menu_font.render(body, True, '#f5f1de')
		body_rect = body_surf.get_rect(center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 10))
		self.display_surface.blit(body_surf, body_rect)

		skip_surf = self.preview_font.render('Enter/Space de bo qua intro', True, '#a9b0bd')
		self.display_surface.blit(skip_surf, (24, WINDOW_HEIGHT - 34))

	def handle_story_event(self, event):
		if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
			self.start_story_level()

	def update_story_input(self):
		if self.gesture_controller.just_pressed('confirm'):
			self.start_story_level()

	def draw_story_screen(self):
		chapter = STORY_CHAPTERS[self.story_level]
		self.display_surface.fill('#101520')

		pygame.draw.rect(self.display_surface, '#1f3d4d', (0, WINDOW_HEIGHT - 145, WINDOW_WIDTH, 145))
		for star in range(0, WINDOW_WIDTH, 110):
			y = 72 + (star % 5) * 18
			pygame.draw.circle(self.display_surface, '#ffd166', (star + 42, y), 3)

		stage_surf = self.menu_font.render(f'MAN {self.story_level + 1}', True, '#a9b0bd')
		stage_rect = stage_surf.get_rect(center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 150))
		self.display_surface.blit(stage_surf, stage_rect)

		title_surf = self.story_title_font.render(chapter['title'], True, '#ffd166')
		title_rect = title_surf.get_rect(center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 82))
		self.display_surface.blit(title_surf, title_rect)

		for index, line in enumerate(chapter['lines']):
			line_surf = self.menu_font.render(line, True, '#f5f1de')
			line_rect = line_surf.get_rect(center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + index * 42))
			self.display_surface.blit(line_surf, line_rect)

		guide_surf = self.menu_font.render('Pinch tay phai hoac Enter de vao man', True, '#a9b0bd')
		guide_rect = guide_surf.get_rect(center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 160))
		self.display_surface.blit(guide_surf, guide_rect)

	def handle_play_menu_event(self, event):
		if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
			self.start_new_game()

	def update_play_menu_input(self):
		if self.gesture_controller.just_pressed('confirm'):
			self.start_new_game()

	def draw_play_menu(self):
		self.display_surface.fill('#0b1b2b')

		title_surf = self.menu_title_font.render('SUPER PIRATE WORLD', True, '#ffd166')
		title_rect = title_surf.get_rect(center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 115))
		self.display_surface.blit(title_surf, title_rect)

		play_rect = pygame.Rect(0, 0, 260, 82)
		play_rect.center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 20)
		pygame.draw.rect(self.display_surface, '#f5f1de', play_rect, border_radius = 8)
		pygame.draw.rect(self.display_surface, '#111018', play_rect, 4, border_radius = 8)

		play_surf = self.menu_font.render('PLAY', True, '#111018')
		play_text_rect = play_surf.get_rect(center = play_rect.center)
		self.display_surface.blit(play_surf, play_text_rect)

		guide_surf = self.menu_font.render('Pinch tay phai hoac Enter de bat dau', True, '#a9b0bd')
		guide_rect = guide_surf.get_rect(center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 105))
		self.display_surface.blit(guide_surf, guide_rect)

	def draw_game_over_menu(self):
		self.display_surface.fill('#111018')

		title_surf = self.menu_title_font.render(self.menu_title, True, '#f5f1de')
		title_rect = title_surf.get_rect(center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 120))
		self.display_surface.blit(title_surf, title_rect)

		guide_surf = self.menu_font.render('Tro trai len/xuong - Pinch tay phai de chon', True, '#a9b0bd')
		guide_rect = guide_surf.get_rect(center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 55))
		self.display_surface.blit(guide_surf, guide_rect)

		for index, option in enumerate(self.game_over_options):
			selected = index == self.game_over_index
			color = '#ffd166' if selected else '#f5f1de'
			prefix = '> ' if selected else '  '
			option_surf = self.menu_font.render(prefix + option, True, color)
			option_rect = option_surf.get_rect(center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + index * 55 + 25))
			self.display_surface.blit(option_surf, option_rect)

	def run(self):
		while True:
			dt = self.clock.tick() / 1000
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.quit_game()
				if self.app_state == 'intro':
					self.handle_intro_event(event)
				elif self.app_state == 'play_menu':
					self.handle_play_menu_event(event)
				elif self.app_state == 'story':
					self.handle_story_event(event)
				elif self.game_over:
					self.handle_game_over_event(event)

			self.gesture_controller.update()
			self.update_quit_gesture()

			if self.app_state == 'intro':
				self.update_intro()
				self.draw_intro()
			elif self.app_state == 'play_menu':
				self.update_play_menu_input()
				self.draw_play_menu()
			elif self.app_state == 'story':
				self.update_story_input()
				self.draw_story_screen()
			elif self.game_over:
				self.update_game_over_input()
				self.draw_game_over_menu()
			else:
				self.current_stage.run(dt)
				self.ui.update(dt)
				self.check_game_over()

			self.gesture_controller.draw_preview(self.display_surface)
			
			pygame.display.update()

if __name__ == '__main__':
	game = Game()
	game.run()
