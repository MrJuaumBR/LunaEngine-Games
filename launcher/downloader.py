import os, sys, requests, json, shutil, hashlib
from typing import Dict, List, Optional, Tuple, Callable
import zipfile
from pathlib import Path as PathLib
import tempfile

class Downloader:
    def __init__(self, games_data:dict):
        self.check_files()
        self.games_data = games_data
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
    
    def get_games(self):
        base_url = 'https://github.com/MrJuaumBR/LunaEngine-Games/raw/refs/heads/main/games/'
        if self.games_data is None:
            return []
        self.games_urls = {}
        for value in self.games_data['games']:
            if 'game_compact_file' in value:
                self.games_urls[value['game_name']] =base_url + value['game_compact_file'] + '.zip'
    
    def download_file(self, url: str, save_path: str, progress_callback=None) -> bool:
        """
        Download a file from URL with progress tracking
        """
        try:
            print(f"Downloading from: {url}")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Get total file size
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            # Create parent directory if it doesn't exist
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        downloaded += len(chunk)
                        
                        # Calculate progress percentage if total_size is known
                        if total_size > 0 and progress_callback:
                            percent = (downloaded / total_size) * 100
                            # Call progress callback if provided
                            progress_callback(percent, downloaded, total_size)
            
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"\nDownload failed: {e}")
            return False
        except Exception as e:
            print(f"\nError during download: {e}")
            return False
    
    def extract_zip(self, zip_path: str, extract_to: str, progress_callback=None) -> bool:
        """
        Extract ZIP file with progress tracking
        """
        try:
            if not os.path.exists(zip_path):
                print(f"ZIP file not found: {zip_path}")
                return False
            
            # Create extraction directory
            os.makedirs(extract_to, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Get total number of files
                file_list = zip_ref.namelist()
                total_files = len(file_list)
                
                for i, file in enumerate(file_list, 1):
                    try:
                        zip_ref.extract(file, extract_to)
                        
                        # Update progress
                        if progress_callback:
                            progress_callback(i, total_files)
                        else:
                            percent = (i / total_files) * 100
                            print(f"\rExtracting: {percent:.1f}% ({i}/{total_files} files)", end='', flush=True)
                    
                    except Exception as e:
                        print(f"\nError extracting {file}: {e}")
                        # Continue with other files
            
            print()  # New line after progress
            return True
            
        except zipfile.BadZipFile:
            print(f"Invalid ZIP file: {zip_path}")
            return False
        except Exception as e:
            print(f"Error extracting ZIP: {e}")
            return False
    
    def verify_download(self, game_name: str, game_folder: str) -> bool:
        """
        Verify downloaded game integrity
        """
        # Check if game folder exists
        if not os.path.exists(game_folder):
            return False
        
        # Check for essential files (customize based on your game structure)
        essential_files = ['game.json', 'main.py']  # Add your essential files
        
        for file in essential_files:
            if not os.path.exists(os.path.join(game_folder, file)):
                print(f"Missing essential file: {file}")
                return False
        
        return True
    
    def download_game(self, game_data: Dict, progress_callback: Callable[[float, str], None]=None) -> bool:
        """
        Download and install a game with queue support
        """
        game_name = game_data["game_name"]
        game_version = game_data["game_version"]
        game_url = self.games_urls.get(game_name)
        
        if not game_url:
            print(f"No download URL found for {game_name}")
            if progress_callback:
                progress_callback(100, f"Error: No download URL for {game_name}")
            return False
        
        print(f"Starting download: {game_name} v{game_version}")
        
        # Check if already up to date
        needs_update, current_version = self.needs_update(game_name, game_version)
        if not needs_update:
            print(f"Game {game_name} is already up to date (v{current_version})")
            if progress_callback:
                progress_callback(100, f"{game_name} is already up to date")
            return True
        
        if current_version:
            print(f"Updating from v{current_version} to v{game_version}")
        
        # Create temp directory for download
        temp_dir = os.path.join(os.getcwd(), 'temp', game_name)
        os.makedirs(temp_dir, exist_ok=True)
        
        # Define paths
        zip_filename = f"{game_name}_{game_version}.zip"
        zip_path = os.path.join(temp_dir, zip_filename)
        game_folder = os.path.join(os.getcwd(), 'games', game_name)
        
        try:
            # Download the game
            if progress_callback:
                progress_callback(0, f"Starting download: {game_name}")
            
            def download_progress(percent, downloaded, total):
                if progress_callback:
                    # Map to overall progress (0-50% for download)
                    overall_percent = percent * 0.5
                    progress_callback(overall_percent, f"Downloading: {percent:.1f}%")
            
            download_success = self.download_file(game_url, zip_path, download_progress)
            
            if not download_success:
                print(f"Failed to download {game_name}")
                if progress_callback:
                    progress_callback(100, f"Failed to download {game_name}")
                return False
            
            # Extract the game
            if progress_callback:
                progress_callback(50, f"Extracting {game_name}...")
            
            def extract_progress(current, total):
                if progress_callback:
                    # Map to overall progress (50-100% for extraction)
                    percent = (current / total) * 100
                    overall_percent = 50 + (percent * 0.5)
                    progress_callback(overall_percent, f"Extracting: {current}/{total} files")
            
            # Remove old game folder if exists (for update)
            if os.path.exists(game_folder):
                shutil.rmtree(game_folder)
            
            extract_success = self.extract_zip(zip_path, game_folder, extract_progress)
            
            if not extract_success:
                print(f"Failed to extract {game_name}")
                if progress_callback:
                    progress_callback(100, f"Failed to extract {game_name}")
                return False
            
            # Create or update game.json with metadata
            game_metadata = {
                "name": game_name,
                "version": game_version,
                "author": game_data.get("game_author", ""),
                "category": game_data.get("game_category", ""),
                "tags": game_data.get("game_tags", []),
                "description": game_data.get("game_description", ""),
                "total_size": game_data.get("total_size", 0),
                "total_files": game_data.get("total_files", 0),
                "installed_date": self._get_current_date(),
                "download_url": game_url
            }
            
            metadata_path = os.path.join(game_folder, 'game.json')
            with open(metadata_path, 'w') as f:
                json.dump(game_metadata, f, indent=2)
            
            # Verify download
            if progress_callback:
                progress_callback(95, f"Verifying {game_name}...")
            
            if not self.verify_download(game_name, game_folder):
                print(f"Verification failed for {game_name}")
                if progress_callback:
                    progress_callback(100, f"Verification failed for {game_name}")
                return False
            
            # Update registry
            self.installed_games["games"][game_name] = {
                "version": game_version,
                "installed_date": game_metadata["installed_date"],
                "size": game_data.get("total_size", 0),
                "files": game_data.get("total_files", 0),
                "author": game_data.get("game_author", ""),
                "category": game_data.get("game_category", ""),
                "tags": game_data.get("game_tags", []),
                "description": game_data.get("game_description", ""),
                "path": game_folder
            }
            
            self.save_installed_games()
            
            # Cleanup temp file
            try:
                os.remove(zip_path)
                os.rmdir(temp_dir)
            except:
                pass  # Ignore cleanup errors
            
            if progress_callback:
                progress_callback(100, f"Successfully installed {game_name}")
            
            print(f"\n✓ Successfully installed {game_name} v{game_version}")
            print(f"  Location: {game_folder}")
            
            return True
            
        except Exception as e:
            print(f"\n✗ Error installing {game_name}: {e}")
            # Cleanup on failure
            if os.path.exists(game_folder):
                shutil.rmtree(game_folder)
            
            if progress_callback:
                progress_callback(100, f"Error: {str(e)[:50]}...")
            
            return False
    
    def _get_current_date(self) -> str:
        """Get current date in YYYY-MM-DD format"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")
    
    def uninstall_game(self, game_name: str) -> bool:
        """Uninstall a game"""
        if not self.is_game_installed(game_name):
            print(f"Game {game_name} is not installed")
            return False
        
        game_folder = os.path.join(os.getcwd(), 'games', game_name)
        
        # Remove game folder
        if os.path.exists(game_folder):
            try:
                shutil.rmtree(game_folder)
            except Exception as e:
                print(f"Error removing game folder: {e}")
                return False
        
        # Remove from registry
        del self.installed_games["games"][game_name]
        self.save_installed_games()
        
        print(f"Successfully uninstalled {game_name}")
        return True
    
    def get_installation_status(self, game_name: str) -> Dict:
        """Get detailed installation status for a game"""
        if self.is_game_installed(game_name):
            game_info = self.installed_games["games"][game_name]
            
            # Check if needs update (requires comparing with remote version)
            needs_update = False
            if self.games_data:
                for game in self.games_data.get('games', []):
                    if game.get('game_name') == game_name:
                        remote_version = game.get('game_version')
                        if remote_version:
                            needs_update, _ = self.needs_update(game_name, remote_version)
                        break
            
            return {
                "installed": True,
                "version": game_info["version"],
                "needs_update": needs_update,
                "installed_date": game_info.get("installed_date"),
                "size": game_info.get("size", 0),
                "author": game_info.get("author", ""),
                "category": game_info.get("category", ""),
                "path": game_info.get("path", "")
            }
        return {"installed": False}
    
    def get_all_installed_games(self) -> List[str]:
        """Get list of all installed game names"""
        return list(self.installed_games.get("games", {}).keys())
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        temp_path = os.path.join(os.getcwd(), 'temp')
        if os.path.exists(temp_path):
            try:
                shutil.rmtree(temp_path)
                os.makedirs(temp_path)
                print("Cleaned up temp files")
            except Exception as e:
                print(f"Error cleaning temp files: {e}")
    
    def get_game_info(self, game_name: str) -> Optional[Dict]:
        """Get game information from games_data"""
        if not self.games_data:
            return None
        
        for game in self.games_data.get('games', []):
            if game.get('game_name') == game_name:
                return game
        return None

if __name__ == '__main__':
    # Example usage
    sample_games_data = {
        "games": [
            {
                "game_name": "SampleGame",
                "game_version": "1.0.0",
                "game_author": "Author Name",
                "game_category": "Adventure",
                "game_tags": ["rpg", "adventure"],
                "game_description": "A sample game",
                "total_size": 1000000,
                "total_files": 50,
                "game_compact_file": "samplegame"
            }
        ]
    }
    
    downloader = Downloader(sample_games_data)
    print("Downloader initialized")
    print(f"Available games: {list(downloader.games_urls.keys())}")
    print(f"Installed games: {downloader.get_all_installed_games()}")
    
    # Example: Download a game
    if sample_games_data["games"]:
        game_to_download = sample_games_data["games"][0]
        success = downloader.download_game(game_to_download)
        if success:
            print(f"Successfully downloaded {game_to_download['game_name']}")
        else:
            print(f"Failed to download {game_to_download['game_name']}")