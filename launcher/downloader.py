import os, sys, requests, json, shutil, hashlib
from typing import Dict, List, Optional, Tuple
import zipfile
from pathlib import Path as PathLib

class Downloader:
    def __init__(self, github_data: dict = None):
        self.check_files()
        if github_data:
            load = requests.get(github_data).json()
            if 'message' in load: # Check if the request was successful
                print(load['message'])
                print("We will use the cached data instead.")
            else:
                json.dump(load, open('./cache/github_data.json', 'w+'))
            self.github_data = json.load(open('./cache/github_data.json', 'r'))
        self.installed_games = self.load_installed_games()
        
        self.get_games()
        
    def check_files(self):
        """Create necessary directories"""
        base_path = os.getcwd()
        
        required_dirs = [
            'games',
            'temp',
            os.path.join('assets', 'fonts'),
            os.path.join('assets', 'icons'),
            'cache',
            'config'
        ]
        
        for dir_path in required_dirs:
            full_path = os.path.join(base_path, dir_path)
            if not os.path.exists(full_path):
                os.makedirs(full_path, exist_ok=True)
        
        # Create installed games registry
        registry_path = os.path.join(base_path, 'config', 'installed_games.json')
        if not os.path.exists(registry_path):
            with open(registry_path, 'w') as f:
                json.dump({"games": {}}, f)
    
    def load_installed_games(self) -> Dict:
        """Load installed games registry"""
        registry_path = os.path.join(os.getcwd(), 'config', 'installed_games.json')
        try:
            with open(registry_path, 'r') as f:
                return json.load(f)
        except:
            return {"games": {}}
    
    def save_installed_games(self):
        """Save installed games registry"""
        registry_path = os.path.join(os.getcwd(), 'config', 'installed_games.json')
        with open(registry_path, 'w') as f:
            json.dump(self.installed_games, f, indent=2)
    
    def is_game_installed(self, game_name: str) -> bool:
        """Check if game is installed"""
        return game_name in self.installed_games.get("games", {})
    
    def get_installed_version(self, game_name: str) -> Optional[str]:
        """Get installed version of a game"""
        if self.is_game_installed(game_name):
            return self.installed_games["games"][game_name].get("version")
        return None
    
    def compare_versions(self, current_version: str, new_version: str) -> int:
        """
        Compare version strings (format: x.y.z)
        Returns: -1 if current < new, 0 if equal, 1 if current > new
        """
        def parse_version(v: str) -> List[int]:
            return [int(part) for part in v.split('.')]
        
        current_parts = parse_version(current_version)
        new_parts = parse_version(new_version)
        
        # Pad with zeros if lengths differ
        max_len = max(len(current_parts), len(new_parts))
        current_parts.extend([0] * (max_len - len(current_parts)))
        new_parts.extend([0] * (max_len - len(new_parts)))
        
        for cur, new in zip(current_parts, new_parts):
            if cur < new:
                return -1
            elif cur > new:
                return 1
        return 0
    
    def needs_update(self, game_name: str, remote_version: str) -> Tuple[bool, Optional[str]]:
        """
        Check if game needs update
        Returns: (needs_update, current_version_if_any)
        """
        if not self.is_game_installed(game_name):
            return (True, None)
        
        current_version = self.get_installed_version(game_name)
        if not current_version:
            return (True, None)
        
        comparison = self.compare_versions(current_version, remote_version)
        if comparison < 0:
            return (True, current_version)
        else:
            return (False, current_version)
    
    def get_game_files_urls(self, fileurl:str) -> Dict:
        game_files_data = {}
        value = requests.get(fileurl).json()
        for v in value:
            if v['type'] == 'dir':
                game_files_data[v['name']] = self.get_game_files_urls(v['url'])
            else:
                game_files_data[v['name']] = v['url']
        return game_files_data
    
    def get_games(self) -> list[dict]:
        if self.github_data is None:
            return []
        games_files = []
        for value in self.github_data:
            if value['type'] == 'dir':
                games_files.append(self.get_game_files_urls(value['url']))
        return games_files
    
    def download_game(self, game_data: Dict, progress_callback=None) -> bool:
        """
        Download and install a game
        game_data should contain: game_name, game_version, download_url (optional)
        """
        game_name = game_data["game_name"]
        game_version = game_data["game_version"]
        
        print(f"Starting download: {game_name} v{game_version}")
        
        # Check if already up to date
        needs_update, current_version = self.needs_update(game_name, game_version)
        if not needs_update:
            print(f"Game {game_name} is already up to date (v{current_version})")
            return True
        
        if current_version:
            print(f"Updating from v{current_version} to v{game_version}")
        
        # In a real implementation, you would:
        # 1. Download from github_data or provided URL
        # 2. Extract to games folder
        # 3. Update registry
        
        # Simulated download for now
        game_folder = os.path.join(os.getcwd(), 'games', game_name)
        
        # Create game folder
        os.makedirs(game_folder, exist_ok=True)
        
        # Create a dummy game file
        with open(os.path.join(game_folder, 'game.json'), 'w') as f:
            json.dump(game_data, f, indent=2)
        
        # Update registry
        self.installed_games["games"][game_name] = {
            "version": game_version,
            "installed_date": "2024-01-01",  # In real implementation, use datetime
            "size": game_data.get("total_size", 0),
            "files": game_data.get("total_files", 0),
            "author": game_data.get("game_author", ""),
            "category": game_data.get("game_category", ""),
            "tags": game_data.get("game_tags", [])
        }
        
        self.save_installed_games()
        
        print(f"Successfully installed {game_name} v{game_version}")
        return True
    
    def uninstall_game(self, game_name: str) -> bool:
        """Uninstall a game"""
        if not self.is_game_installed(game_name):
            print(f"Game {game_name} is not installed")
            return False
        
        game_folder = os.path.join(os.getcwd(), 'games', game_name)
        
        # Remove game folder
        if os.path.exists(game_folder):
            shutil.rmtree(game_folder)
        
        # Remove from registry
        del self.installed_games["games"][game_name]
        self.save_installed_games()
        
        print(f"Successfully uninstalled {game_name}")
        return True
    
    def get_installation_status(self, game_name: str) -> Dict:
        """Get detailed installation status for a game"""
        if self.is_game_installed(game_name):
            game_info = self.installed_games["games"][game_name]
            return {
                "installed": True,
                "version": game_info["version"],
                "needs_update": False,  # Would need remote data to check
                "installed_date": game_info.get("installed_date"),
                "size": game_info.get("size", 0)
            }
        return {"installed": False}
    
    def get_all_installed_games(self) -> List[str]:
        """Get list of all installed game names"""
        return list(self.installed_games.get("games", {}).keys())
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        temp_path = os.path.join(os.getcwd(), 'temp')
        if os.path.exists(temp_path):
            shutil.rmtree(temp_path)
            os.makedirs(temp_path)

if __name__ == '__main__':
    # Test the downloader
    downloader = Downloader()
    print("Downloader initialized")
    print(f"Installed games: {downloader.get_all_installed_games()}")