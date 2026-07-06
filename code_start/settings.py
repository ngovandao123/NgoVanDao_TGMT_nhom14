import pygame, sys
from pathlib import Path
from pygame.math import Vector2 as vector

BASE_DIR = Path(__file__).resolve().parent.parent

def project_path(*parts):
	return str(BASE_DIR.joinpath(*parts))

WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
TILE_SIZE = 64
ANIMATION_SPEED = 6

# layers 
Z_LAYERS = {
	'bg': 0,
	'clouds': 1,
	'bg tiles': 2,
	'path': 3,
	'bg details': 4,
	'main': 5,
	'water': 6,
	'fg': 7
}
