"""
This file will generate data for games/
Also will make the zipped version
"""

import os, sys, json, shutil, stat

path_root = os.path.dirname(os.path.abspath(__file__))
path_games = path_root + '\\games'

blacklist_folders = ['.venv', '.vscode', '__pycache__']
blacklist_files = ['.md','.txt', '.json', '.pyc', '.aseprite', '.ttf']

def remove_readonly(func, path, excinfo):
    """Handler para remover atributo readonly no Windows"""
    os.chmod(path, stat.S_IWRITE)
    func(path)

class game_info:
    game_name:str
    game_version:str
    game_author:str
    game_tags:list[str]
    game_category:str
    game_description:str
    game_main_file:str
    game_icon:str
    total_files:int
    total_size:float
    requirements:list[str]
    

def count_files(game_path:str) -> tuple[int, float]:
    """
    Returns the number of files and size in MB
    """
    count = 0
    size = 0
    for arch in os.listdir(game_path):
        if os.path.isdir(game_path + '\\' + arch):
            if arch in blacklist_folders:
                continue
            c, s =count_files(game_path + '\\' + arch)
        elif os.path.isfile(game_path + '\\' + arch):
            if arch.split('.')[-1] in blacklist_files:
                continue
            c = 1
            s = (os.path.getsize(game_path + '\\' + arch)) / (1024**2)
        count += c
        size += s
        
    return count, size

def fix_string(text:bytes, is_list:bool = False) -> str:
    if is_list:
        return [str(tag).replace('\r', '').replace('\n', '').replace(' ', '') for tag in list(text.decode('utf-8').split(','))]
    else:
        return text.decode('utf-8').replace('\r', '').replace('\n', '')
    

def get_game_info(game_path) -> game_info:
    gi = game_info()
    
    with open(game_path + '\\info', 'rb') as f:
        gi.game_name = fix_string(f.readline(-1))
        gi.game_version = fix_string(f.readline(-1))
        gi.game_author = fix_string(f.readline(-1))
        gi.game_tags = fix_string(f.readline(-1), True)
        gi.game_category = fix_string(f.readline(-1))
        gi.game_description = fix_string(f.readline(-1))
        gi.game_main_file = fix_string(f.readline(-1))
        gi.game_icon = fix_string(f.readline(-1))
        gi.game_compact_file = f'{gi.game_name}-{gi.game_version}'
        
        
    return gi
    

def create_zip(game:game_info, game_path:str):
    # First, create a temporary folder to get only the clear files
    temp_path = path_root + '\\temp\\' + game.game_name
    os.mkdir(temp_path)
    
    # Get all files
    for arch in os.listdir(game_path):
        if os.path.isdir(game_path + '\\' + arch):
            if arch in blacklist_folders:
                continue
            else:
                shutil.copytree(game_path + '\\' + arch, temp_path + '\\' + arch)
        elif os.path.isfile(game_path + '\\' + arch):
            if arch.split('.')[-1] in blacklist_files:
                continue
            else:
                shutil.copy(game_path + '\\' + arch, temp_path + '\\' + arch)
    
    # Create zip
    shutil.make_archive(path_root + '\\games\\' + game .game_compact_file, 'zip', temp_path)
    
    # Delete temp
    shutil.rmtree(temp_path, onexc=remove_readonly)
    

def loop_through_games():
    if not os.path.exists('./temp'):
        os.makedirs('./temp')
    else:
        shutil.rmtree('./temp', onexc=remove_readonly)
        os.makedirs('./temp')
    games:list[game_info] = []
    for game_folder in os.listdir(path_games):
        game_path = path_games + '\\' + game_folder
        if os.path.isdir(path_games + '\\' + game_folder):
            info = get_game_info(game_path)
            total_files, total_size = count_files(game_path)
            info.total_files = total_files
            info.total_size = total_size
            
            with open(game_path + '\\requirements.txt', 'r') as f:
                info.requirements = f.read().split('\n')
            
            create_zip(info, game_path)
            games.append(info)
        
    with open(path_root + '\\games\\data.json', 'w+') as f:
        f.write(
            json.dumps({
                'info': {
                    'version': '0.0.1',
                    'author': 'MrJuaumBR',
                    'total_games': len(games)
                },
                'games': [game.__dict__ for game in games]
            }, indent=2)
        )
        

if os.path.exists(path_games) and __name__ == '__main__':    
    loop_through_games()
else:
    print("Something went wrong...")