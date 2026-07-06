from settings import *

PREVIEW_SIZE = (220, 165)
PREVIEW_MARGIN = 12
CAMERA_INDEX = 0
MIRROR_CAMERA = True
SWAP_HAND_LABELS = False
DIRECTION_THRESHOLD = 0.08
CONFIRM_COOLDOWN = 2000


class GestureController:
	def __init__(self):
		self.enabled = False
		self.status = 'Gesture: inactive'
		self.frame = None
		self.preview_font = pygame.font.Font(None, 18)
		self.state = self.empty_state()
		self.previous_state = self.empty_state()
		self.confirm_ready_time = 0

		try:
			import cv2
			import mediapipe as mp
		except ImportError:
			self.cv2 = None
			self.mp_hands = None
			self.status = 'Install opencv-python + mediapipe'
			return

		self.cv2 = cv2
		self.mp_hands = mp.solutions.hands
		self.mp_draw = mp.solutions.drawing_utils
		self.hands = self.mp_hands.Hands(
			static_image_mode = False,
			max_num_hands = 2,
			model_complexity = 0,
			min_detection_confidence = 0.6,
			min_tracking_confidence = 0.6)
		self.capture = cv2.VideoCapture(CAMERA_INDEX)

		if not self.capture.isOpened():
			self.status = 'Camera unavailable'
			return

		self.enabled = True
		self.status = 'Gesture ready'

	def empty_state(self):
		return {
			'left': False,
			'right': False,
			'up': False,
			'down': False,
			'jump': False,
			'attack': False,
			'confirm': False,
			'quit': False}

	def update(self):
		self.previous_state = self.state.copy()
		self.state = self.empty_state()

		if not self.enabled:
			return

		success, frame = self.capture.read()
		if not success:
			self.status = 'Camera frame missing'
			return

		if MIRROR_CAMERA:
			frame = self.cv2.flip(frame, 1)

		rgb_frame = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB)
		results = self.hands.process(rgb_frame)
		self.status = 'Show both hands'

		if results.multi_hand_landmarks and results.multi_handedness:
			for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
				self.mp_draw.draw_landmarks(
					rgb_frame,
					hand_landmarks,
					self.mp_hands.HAND_CONNECTIONS)

				label = handedness.classification[0].label.lower()
				if SWAP_HAND_LABELS:
					label = 'right' if label == 'left' else 'left'

				landmarks = hand_landmarks.landmark
				if label == 'left':
					self.read_navigation_hand(landmarks)
				elif label == 'right':
					self.read_action_hand(landmarks)

		self.frame = rgb_frame

	def read_navigation_hand(self, landmarks):
		direction = self.index_direction(landmarks)
		if direction == 'LEFT':
			self.state['left'] = True
		elif direction == 'RIGHT':
			self.state['right'] = True
		elif direction == 'UP':
			self.state['up'] = True
			self.state['jump'] = True
		elif direction == 'DOWN':
			self.state['down'] = True

	def read_action_hand(self, landmarks):
		self.state['attack'] = self.single_index_up(landmarks)
		self.state['confirm'] = self.is_pinch(landmarks)
		self.state['quit'] = self.two_fingers_up(landmarks)

	def index_direction(self, landmarks):
		tip = landmarks[8]
		base = landmarks[5]
		dx = tip.x - base.x
		dy = tip.y - base.y

		if dx > DIRECTION_THRESHOLD:
			return 'RIGHT'
		if dx < -DIRECTION_THRESHOLD:
			return 'LEFT'
		if dy < -DIRECTION_THRESHOLD:
			return 'UP'
		if dy > DIRECTION_THRESHOLD:
			return 'DOWN'
		return 'NONE'

	def index_finger_up(self, landmarks):
		return landmarks[8].y < landmarks[6].y and landmarks[8].y < landmarks[5].y

	def single_index_up(self, landmarks):
		index_up = self.index_finger_up(landmarks)
		other_fingers_down = all(landmarks[tip].y > landmarks[pip].y for tip, pip in ((12, 10), (16, 14), (20, 18)))
		return index_up and other_fingers_down

	def two_fingers_up(self, landmarks):
		index_up = self.index_finger_up(landmarks)
		middle_up = landmarks[12].y < landmarks[10].y and landmarks[12].y < landmarks[9].y
		ring_down = landmarks[16].y > landmarks[14].y
		pinky_down = landmarks[20].y > landmarks[18].y
		return index_up and middle_up and ring_down and pinky_down

	def is_fist(self, landmarks):
		folded_fingers = 0
		for tip, pip in ((8, 6), (12, 10), (16, 14), (20, 18)):
			if landmarks[tip].y > landmarks[pip].y:
				folded_fingers += 1
		return folded_fingers >= 3

	def is_pinch(self, landmarks):
		thumb_tip = vector(landmarks[4].x, landmarks[4].y)
		index_tip = vector(landmarks[8].x, landmarks[8].y)
		return thumb_tip.distance_to(index_tip) < 0.055

	def pressed(self, action):
		return self.state.get(action, False)

	def just_pressed(self, action):
		if action == 'confirm':
			if not self.state.get('confirm', False):
				return False
			current_time = pygame.time.get_ticks()
			if current_time < self.confirm_ready_time:
				return False
			if self.previous_state.get('confirm', False):
				return False
			self.confirm_ready_time = current_time + CONFIRM_COOLDOWN
			return True
		return self.state.get(action, False) and not self.previous_state.get(action, False)

	def draw_preview(self, display_surface):
		left = WINDOW_WIDTH - PREVIEW_SIZE[0] - PREVIEW_MARGIN
		top = PREVIEW_MARGIN
		preview_rect = pygame.Rect((left, top), PREVIEW_SIZE)

		if self.frame is not None:
			frame_surface = pygame.surfarray.make_surface(self.frame.swapaxes(0, 1))
			frame_surface = pygame.transform.smoothscale(frame_surface, PREVIEW_SIZE)
			display_surface.blit(frame_surface, preview_rect)
		else:
			pygame.draw.rect(display_surface, '#161616', preview_rect)

		pygame.draw.rect(display_surface, '#f5f1de', preview_rect, 2)
		self.draw_labels(display_surface, preview_rect)

	def draw_zones(self, display_surface, preview_rect):
		left_line = preview_rect.left + int(preview_rect.width * 0.4)
		right_line = preview_rect.left + int(preview_rect.width * 0.6)
		top_line = preview_rect.top + int(preview_rect.height * 0.35)
		bottom_line = preview_rect.top + int(preview_rect.height * 0.65)

		color = '#f5f1de'
		pygame.draw.line(display_surface, color, (left_line, preview_rect.top), (left_line, preview_rect.bottom), 1)
		pygame.draw.line(display_surface, color, (right_line, preview_rect.top), (right_line, preview_rect.bottom), 1)
		pygame.draw.line(display_surface, color, (preview_rect.left, top_line), (preview_rect.right, top_line), 1)
		pygame.draw.line(display_surface, color, (preview_rect.left, bottom_line), (preview_rect.right, bottom_line), 1)

	def draw_labels(self, display_surface, preview_rect):
		actions = [name.upper() for name, active in self.state.items() if active]
		action_text = ' '.join(actions) if actions else self.status
		label = self.preview_font.render(action_text, True, '#ffffff')
		bg_rect = label.get_rect(topleft = (preview_rect.left + 6, preview_rect.bottom - 22)).inflate(8, 4)
		pygame.draw.rect(display_surface, '#000000', bg_rect)
		display_surface.blit(label, (preview_rect.left + 10, preview_rect.bottom - 18))

	def close(self):
		if hasattr(self, 'capture') and self.capture:
			self.capture.release()
		if hasattr(self, 'hands') and self.hands:
			self.hands.close()
