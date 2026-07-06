from settings import * 
from os import walk
from pathlib import Path

def resolve_path(*path):
	parts = list(path)
	if parts and parts[0] == '..':
		parts = parts[1:]
	return BASE_DIR.joinpath(*parts)

def import_image(*path, alpha = True, format = 'png'):
	full_path = resolve_path(*path).with_suffix(f'.{format}')
	return pygame.image.load(full_path).convert_alpha() if alpha else pygame.image.load(full_path).convert()

def import_folder(*path):
	frames = []
	for folder_path, subfolders, image_names in walk(resolve_path(*path)):
		for image_name in sorted(image_names, key = lambda name: int(name.split('.')[0])):
			full_path = Path(folder_path) / image_name
			frames.append(pygame.image.load(full_path).convert_alpha())
	return frames 

def import_folder_dict(*path):
	frame_dict = {}
	for folder_path, _, image_names in walk(resolve_path(*path)):
		for image_name in image_names:
			full_path = Path(folder_path) / image_name
			surface = pygame.image.load(full_path).convert_alpha()
			frame_dict[image_name.split('.')[0]] = surface
	return frame_dict

def import_sub_folders(*path):
	frame_dict = {}
	for _, sub_folders, __ in walk(resolve_path(*path)): 
		if sub_folders:
			for sub_folder in sub_folders:
				frame_dict[sub_folder] = import_folder(*path, sub_folder)
	return frame_dict
