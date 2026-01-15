import os, sys, json, requests, shutil
from typing import Literal, Optional, List, Dict, Set, Tuple
import customtkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import io
from downloader import Downloader

run_mode: Literal['--local', '--remote'] = '--local'

if len(sys.argv) >= 2:
    if sys.argv[1] in ['--local', '--remote']: 
        run_mode = sys.argv[1]
        
class Path:
    fonts = os.path.join(os.getcwd(), 'assets', 'fonts')
    icons = os.path.join(os.getcwd(), 'assets', 'icons')
    games = os.path.join(os.getcwd(), 'games')
    temp = os.path.join(os.getcwd(), 'temp')
    cache = os.path.join(os.getcwd(), 'cache')
    config = os.path.join(os.getcwd(), 'config')
    github = 'https://api.github.com/repos/MrJuaumBR/LunaEngine-Games/contents/games'
    data_remote = 'https://raw.githubusercontent.com/MrJuaumBR/LunaEngine-Games/refs/heads/main/games/data.json'
    
# Load fonts if they exist
if os.path.exists(Path.fonts):
    roboto_mono_path = os.path.join(Path.fonts, 'RobotoMono.ttf')
    roboto_serif_path = os.path.join(Path.fonts, 'RobotoSerif.ttf')
    
    if os.path.exists(roboto_mono_path):
        tk.FontManager.load_font(roboto_mono_path)
    if os.path.exists(roboto_serif_path):
        tk.FontManager.load_font(roboto_serif_path)

class ThemeManager:
    THEMES = {
        'dark': {
            'name': 'Dark',
            'bg': '#121212',
            'fg': '#1e1e1e',
            'card_bg': '#252525',
            'card_border': '#333333',
            'text_primary': '#ffffff',
            'text_secondary': '#aaaaaa',
            'text_accent': '#4ecdc4',
            'button_primary': '#2ecc71',
            'button_primary_hover': '#27ae60',
            'button_secondary': '#3498db',
            'button_secondary_hover': '#2980b9',
            'button_update': '#e74c3c',
            'button_update_hover': '#c0392b',
            'tag_bg': '#3a3a3a',
            'scrollbar': '#444444',
            'success': '#2ecc71',
            'info': '#3498db',
            'warning': '#f39c12',
            'danger': '#e74c3c',
            'sidebar': '#1a1a1a',
            'sidebar_border': '#2a2a2a',
            'input_bg': '#2a2a2a',
            'input_border': '#3a3a3a',
            'installed_badge': '#2ecc71',
            'update_badge': '#e74c3c'
        },
        'light': {
            'name': 'Light',
            'bg': '#f5f5f5',
            'fg': '#ffffff',
            'card_bg': '#ffffff',
            'card_border': '#e0e0e0',
            'text_primary': '#333333',
            'text_secondary': '#666666',
            'text_accent': '#2c82c9',
            'button_primary': '#4a90e2',
            'button_primary_hover': '#3a7bc8',
            'button_secondary': '#50c878',
            'button_secondary_hover': '#40b868',
            'button_update': '#ff6b6b',
            'button_update_hover': '#ff5252',
            'tag_bg': '#f0f0f0',
            'scrollbar': '#cccccc',
            'success': '#50c878',
            'info': '#4a90e2',
            'warning': '#ffa500',
            'danger': '#ff6b6b',
            'sidebar': '#2c3e50',
            'sidebar_border': '#34495e',
            'input_bg': '#ffffff',
            'input_border': '#dddddd',
            'installed_badge': '#50c878',
            'update_badge': '#ff6b6b'
        },
        'ocean': {
            'name': 'Ocean',
            'bg': '#0a192f',
            'fg': '#112240',
            'card_bg': '#172a45',
            'card_border': '#303C55',
            'text_primary': '#e6f1ff',
            'text_secondary': '#8892b0',
            'text_accent': '#64ffda',
            'button_primary': '#00b894',
            'button_primary_hover': '#00a085',
            'button_secondary': '#0984e3',
            'button_secondary_hover': '#0770c4',
            'button_update': '#fd79a8',
            'button_update_hover': '#e66797',
            'tag_bg': '#1d3658',
            'scrollbar': '#2d4a7a',
            'success': '#00b894',
            'info': '#0984e3',
            'warning': '#fdcb6e',
            'danger': '#fd79a8',
            'sidebar': '#0c223a',
            'sidebar_border': '#1a3458',
            'input_bg': '#1d3658',
            'input_border': '#2d4a7a',
            'installed_badge': '#00b894',
            'update_badge': '#fd79a8'
        },
        'purple': {
            'name': 'Purple',
            'bg': '#1a1a2e',
            'fg': '#16213e',
            'card_bg': '#0f3460',
            'card_border': '#1a508b',
            'text_primary': '#e2e2e2',
            'text_secondary': '#b8b8b8',
            'text_accent': '#ff9a76',
            'button_primary': '#8a2be2',
            'button_primary_hover': '#7a1ad2',
            'button_secondary': '#da70d6',
            'button_secondary_hover': '#ca60c6',
            'button_update': '#ff6b6b',
            'button_update_hover': '#ff5252',
            'tag_bg': '#2d2d5c',
            'scrollbar': '#3d3d7c',
            'success': '#8a2be2',
            'info': '#da70d6',
            'warning': '#ffa500',
            'danger': '#ff6b6b',
            'sidebar': '#151530',
            'sidebar_border': '#252550',
            'input_bg': '#2d2d5c',
            'input_border': '#3d3d7c',
            'installed_badge': '#8a2be2',
            'update_badge': '#ff6b6b'
        },
        'draconic': {
            'name': 'Draconic',
            'bg': '#0c0c0c',
            'fg': '#1a1a1a',
            'card_bg': '#2a1a1a',
            'card_border': '#3a2a2a',
            'text_primary': '#ffcc00',
            'text_secondary': '#cc9900',
            'text_accent': '#ff3333',
            'button_primary': '#cc3300',
            'button_primary_hover': '#bb2200',
            'button_secondary': '#993300',
            'button_secondary_hover': '#882200',
            'button_update': '#ff6600',
            'button_update_hover': '#ff5500',
            'tag_bg': '#3a2a2a',
            'scrollbar': '#4a3a3a',
            'success': '#cc3300',
            'info': '#993300',
            'warning': '#ff6600',
            'danger': '#ff3333',
            'sidebar': '#1a0c0c',
            'sidebar_border': '#2a1a1a',
            'input_bg': '#2a1a1a',
            'input_border': '#3a2a2a',
            'installed_badge': '#cc3300',
            'update_badge': '#ff3333'
        }
    }
    
    @classmethod
    def get_theme(cls, theme_name: str) -> dict:
        return cls.THEMES.get(theme_name, cls.THEMES['dark'])
    
    @classmethod
    def get_theme_names(cls) -> list:
        return list(cls.THEMES.keys())

class FilterManager:
    SORT_OPTIONS = {
        'name': 'Name (A-Z)',
        'name_desc': 'Name (Z-A)',
        'author': 'Author (A-Z)',
        'author_desc': 'Author (Z-A)',
        'size': 'Size (Smallest)',
        'size_desc': 'Size (Largest)',
        'files': 'Files (Fewest)',
        'files_desc': 'Files (Most)',
        'version': 'Version (Oldest)',
        'version_desc': 'Version (Newest)',
        'installed': 'Installed First',
        'not_installed': 'Not Installed First'
    }
    
    INSTALLATION_FILTERS = {
        'all': 'All Games',
        'installed': 'Installed Only',
        'not_installed': 'Not Installed',
        'updates': 'Updates Available'
    }
    
    @staticmethod
    def sort_games(games: List[Dict], sort_by: str, downloader: Downloader) -> List[Dict]:
        """Sort games with installation awareness"""
        if sort_by == 'installed':
            return sorted(games, key=lambda x: (not downloader.is_game_installed(x['game_name']), x['game_name'].lower()))
        elif sort_by == 'not_installed':
            return sorted(games, key=lambda x: (downloader.is_game_installed(x['game_name']), x['game_name'].lower()))
        
        if sort_by == 'name':
            return sorted(games, key=lambda x: x['game_name'].lower())
        elif sort_by == 'name_desc':
            return sorted(games, key=lambda x: x['game_name'].lower(), reverse=True)
        elif sort_by == 'author':
            return sorted(games, key=lambda x: x['game_author'].lower())
        elif sort_by == 'author_desc':
            return sorted(games, key=lambda x: x['game_author'].lower(), reverse=True)
        elif sort_by == 'size':
            return sorted(games, key=lambda x: x['total_size'])
        elif sort_by == 'size_desc':
            return sorted(games, key=lambda x: x['total_size'], reverse=True)
        elif sort_by == 'files':
            return sorted(games, key=lambda x: x['total_files'])
        elif sort_by == 'files_desc':
            return sorted(games, key=lambda x: x['total_files'], reverse=True)
        elif sort_by == 'version':
            return sorted(games, key=lambda x: [int(n) for n in x['game_version'].split('.')])
        elif sort_by == 'version_desc':
            return sorted(games, key=lambda x: [int(n) for n in x['game_version'].split('.')], reverse=True)
        return games
    
    @staticmethod
    def filter_games(games: List[Dict], filters: Dict, downloader: Downloader) -> List[Dict]:
        """Filter games based on multiple criteria"""
        filtered = games
        
        # Search filter
        if filters.get('search'):
            search_lower = filters['search'].lower()
            filtered = [g for g in filtered if 
                    search_lower in g['game_name'].lower() or 
                    search_lower in g['game_description'].lower() or
                    search_lower in g['game_author'].lower() or
                    search_lower in g['game_category'].lower() or  # Added category
                    any(search_lower in tag.lower() for tag in g['game_tags'])]  # Already includes tags
        
        # Category filter
        if filters.get('category') and filters['category'] != 'all':
            filtered = [g for g in filtered if g['game_category'].lower() == filters['category'].lower()]
        
        # Tags filter
        if filters.get('tags') and len(filters['tags']) > 0:
            filtered = [g for g in filtered if 
                    any(tag.lower() in [t.lower() for t in g['game_tags']] 
                        for tag in filters['tags'])]
        
        # Author filter
        if filters.get('author') and filters['author'] != 'all':
            filtered = [g for g in filtered if g['game_author'].lower() == filters['author'].lower()]
        
        # Installation status filter
        installation_filter = filters.get('installation', 'all')
        if installation_filter == 'installed':
            filtered = [g for g in filtered if downloader.is_game_installed(g['game_name'])]
        elif installation_filter == 'not_installed':
            filtered = [g for g in filtered if not downloader.is_game_installed(g['game_name'])]
        elif installation_filter == 'updates':
            filtered = [g for g in filtered if 
                    downloader.is_game_installed(g['game_name']) and 
                    downloader.needs_update(g['game_name'], g['game_version'])[0]]
        
        return filtered

class TagManager:
    """Manages tag selection and display"""
    
    @staticmethod
    def create_tag_widgets(parent, tags: Set[str], selected_tags: Set[str], 
                          theme: Dict, on_tag_toggle=None, max_height=150):
        """Create scrollable tag selection widget"""
        frame = tk.CTkFrame(parent, fg_color="transparent")
        
        # Label
        tk.CTkLabel(frame,
                   text="Tags:",
                   font=("RobotoMono", 11),
                   text_color=theme['text_secondary']).pack(anchor="w", pady=(0, 8))
        
        # Scrollable tag container
        tag_container = tk.CTkScrollableFrame(frame, 
                                             height=max_height,
                                             fg_color=theme['input_bg'],
                                             border_width=1,
                                             border_color=theme['input_border'])
        tag_container.pack(fill="x", pady=(0, 10))
        
        # Dictionary to store tag buttons for later reference
        tag_buttons = {}
        
        # Create tag buttons
        sorted_tags = sorted(list(tags))
        for tag in sorted_tags:
            is_selected = tag in selected_tags
            
            btn_color = theme['button_primary'] if is_selected else theme['input_bg']
            hover_color = theme['button_primary_hover'] if is_selected else theme['sidebar_border']
            text_color = theme['text_primary'] if is_selected else theme['text_secondary']
            
            btn = tk.CTkButton(tag_container,
                              text=tag,
                              font=("RobotoMono", 10),
                              fg_color=btn_color,
                              hover_color=hover_color,
                              text_color=text_color,
                              height=30,
                              anchor="w",
                              command=lambda t=tag: on_tag_toggle(t) if on_tag_toggle else None)
            btn.pack(fill="x", padx=5, pady=2)
            tag_buttons[tag] = btn
        
        # Clear tags button
        clear_btn = tk.CTkButton(frame,
                                text="Clear Tags",
                                font=("RobotoMono", 10),
                                fg_color=theme['button_secondary'],
                                hover_color=theme['button_secondary_hover'],
                                command=lambda: on_tag_toggle('clear_all') if on_tag_toggle else None,
                                height=30)
        clear_btn.pack(fill="x")
        
        # Store tag buttons in frame for access
        frame.tag_buttons = tag_buttons
        frame.tag_container = tag_container
        frame.clear_btn = clear_btn
        
        return frame

class ResponsiveGameCard(tk.CTkFrame):
    mom: 'App'
    def __init__(self, master, game_data, game_id, theme: dict, downloader: Downloader, refresh_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.game_data = game_data
        self.game_id = game_id
        self.theme = theme
        self.downloader = downloader
        self.refresh_callback = refresh_callback
        self.install_status = downloader.get_installation_status(game_data['game_name'])
        
        self.configure(fg_color=theme['card_bg'], 
                      corner_radius=12, 
                      border_width=1, 
                      border_color=theme['card_border'])
        
        self.create_widgets()
    
    def create_widgets(self):
        # Main container
        main_frame = tk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=12, pady=12)
        
        # Status badge
        self.create_status_badge(main_frame)
        
        # Title and version
        title_frame = tk.CTkFrame(main_frame, fg_color="transparent", height=30)
        title_frame.pack(fill="x", pady=(0, 8))
        
        # Title
        title_label = tk.CTkLabel(title_frame, 
                                 text=self.game_data["game_name"], 
                                 font=("RobotoSerif", 16, "bold"),
                                 text_color=self.theme['text_primary'],
                                 anchor="w")
        title_label.pack(side="left", fill="x", expand=True)
        
        # Version with update indicator
        version_text = f"v{self.game_data['game_version']}"
        if self.install_status['installed']:
            needs_update, current_version = self.downloader.needs_update(
                self.game_data['game_name'], 
                self.game_data['game_version']
            )
            if needs_update:
                version_text = f"v{current_version} → v{self.game_data['game_version']}"
        
        version_label = tk.CTkLabel(title_frame, 
                                   text=version_text,
                                   font=("RobotoMono", 10),
                                   text_color=self.theme['text_secondary'])
        version_label.pack(side="right")
        
        # Tags (compact)
        tags_frame = tk.CTkFrame(main_frame, fg_color="transparent", height=24)
        tags_frame.pack(fill="x", pady=(0, 8))
        
        for i, tag in enumerate(self.game_data["game_tags"][:2]):
            tk.CTkLabel(tags_frame, 
                       text=tag,
                       font=("RobotoMono", 9),
                       text_color=self.theme['text_accent'],
                       fg_color=self.theme['tag_bg'],
                       corner_radius=10,
                       padx=6, pady=2).pack(side="left", padx=(0, 4))
        
        # Description
        desc_text = tk.CTkTextbox(main_frame, 
                                 height=50,
                                 fg_color=self.theme['fg'], 
                                 text_color=self.theme['text_secondary'], 
                                 border_width=0,
                                 font=("RobotoMono", 10), 
                                 wrap="word")
        desc_text.insert("1.0", self.game_data["game_description"][:100] + 
                        ("..." if len(self.game_data["game_description"]) > 100 else ""))
        desc_text.configure(state="disabled")
        desc_text.pack(fill="x", pady=(0, 8))
        
        # Info bar
        info_frame = tk.CTkFrame(main_frame, fg_color="transparent")
        info_frame.pack(fill="x", pady=(0, 8))
        
        # Author
        tk.CTkLabel(info_frame,
                   text=self.game_data['game_author'][:15],
                   font=("RobotoMono", 9),
                   text_color=self.theme['text_secondary'],
                   anchor="w").pack(side="left", fill="x", expand=True)
        
        # Size
        tk.CTkLabel(info_frame,
                   text=f"{self.game_data['total_size']:.1f}MB",
                   font=("RobotoMono", 9),
                   text_color=self.theme['text_secondary']).pack(side="right")
        
        # Files
        tk.CTkLabel(info_frame,
                   text=f"{self.game_data['total_files']} files",
                   font=("RobotoMono", 9),
                   text_color=self.theme['text_secondary']).pack(side="right", padx=(0, 8))
        
        # Action buttons based on installation status
        self.create_action_buttons(main_frame)
    
    def create_status_badge(self, parent):
        """Create installation status badge"""
        status_frame = tk.CTkFrame(parent, fg_color="transparent", height=24)
        status_frame.pack(fill="x", pady=(0, 8))
        
        if self.install_status['installed']:
            needs_update, current_version = self.downloader.needs_update(
                self.game_data['game_name'], 
                self.game_data['game_version']
            )
            
            if needs_update:
                # Update available
                badge = tk.CTkLabel(status_frame,
                                   text="UPDATE AVAILABLE",
                                   font=("RobotoMono", 9, "bold"),
                                   text_color="#ffffff",
                                   fg_color=self.theme['update_badge'],
                                   corner_radius=10,
                                   padx=8, pady=2)
                badge.pack(side="left")
            else:
                # Installed and up to date
                badge = tk.CTkLabel(status_frame,
                                   text="INSTALLED",
                                   font=("RobotoMono", 9, "bold"),
                                   text_color="#ffffff",
                                   fg_color=self.theme['installed_badge'],
                                   corner_radius=10,
                                   padx=8, pady=2)
                badge.pack(side="left")
        else:
            # Not installed
            badge = tk.CTkLabel(status_frame,
                               text="NOT INSTALLED",
                               font=("RobotoMono", 9, "bold"),
                               text_color=self.theme['text_secondary'],
                               fg_color=self.theme['tag_bg'],
                               corner_radius=10,
                               padx=8, pady=2)
            badge.pack(side="left")
    
    def create_action_buttons(self, parent):
        """Create action buttons based on installation status"""
        button_frame = tk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x")
        
        if self.install_status['installed']:
            needs_update, current_version = self.downloader.needs_update(
                self.game_data['game_name'], 
                self.game_data['game_version']
            )
            
            if needs_update:
                # Update button
                update_btn = tk.CTkButton(button_frame,
                                        text="UPDATE",
                                        fg_color=self.theme['button_update'],
                                        hover_color=self.theme['button_update_hover'],
                                        font=("RobotoMono", 11, "bold"),
                                        height=28,
                                        command=self.update_game)
                update_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
                
                # Play button
                play_btn = tk.CTkButton(button_frame,
                                       text="PLAY",
                                       fg_color=self.theme['button_primary'],
                                       hover_color=self.theme['button_primary_hover'],
                                       font=("RobotoMono", 11),
                                       height=28,
                                       command=self.play_game)
                play_btn.pack(side="left", fill="x", expand=True, padx=(4, 0))
                
                # Uninstall button (small)
                uninstall_btn = tk.CTkButton(button_frame,
                                           text="✕",
                                           width=100,
                                           fg_color=self.theme['danger'],
                                           hover_color="#ff5252",
                                           font=("RobotoMono", 11),
                                           height=28,
                                           command=self.uninstall_game)
                uninstall_btn.pack(side="left", padx=(4, 0))
            else:
                # Play button (primary)
                play_btn = tk.CTkButton(button_frame,
                                       text="PLAY",
                                       fg_color=self.theme['button_primary'],
                                       hover_color=self.theme['button_primary_hover'],
                                       font=("RobotoMono", 11, "bold"),
                                       height=28,
                                       command=self.play_game)
                play_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
                
                # Info button
                info_btn = tk.CTkButton(button_frame,
                                       text="INFO",
                                       fg_color=self.theme['button_secondary'],
                                       hover_color=self.theme['button_secondary_hover'],
                                       font=("RobotoMono", 11),
                                       height=28,
                                       width=40,
                                       command=self.show_details)
                info_btn.pack(side="left", fill="x", expand=True, padx=(4, 4))
                
                # Uninstall button
                uninstall_btn = tk.CTkButton(button_frame,
                                           text="UNINSTALL",
                                           fg_color=self.theme['danger'],
                                           hover_color="#ff5252",
                                           font=("RobotoMono", 11),
                                           height=28,
                                           width=80,
                                           command=self.uninstall_game)
                uninstall_btn.pack(side="right", fill="x", expand=True, padx=(4, 4))
        else:
            # Install button
            install_btn = tk.CTkButton(button_frame,
                                      text="INSTALL",
                                      fg_color=self.theme['button_primary'],
                                      hover_color=self.theme['button_primary_hover'],
                                      font=("RobotoMono", 11, "bold"),
                                      height=28,
                                      command=self.install_game)
            install_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
            
            # Info button
            info_btn = tk.CTkButton(button_frame,
                                   text="INFO",
                                   fg_color=self.theme['button_secondary'],
                                   hover_color=self.theme['button_secondary_hover'],
                                   font=("RobotoMono", 11),
                                   height=28,
                                   command=self.show_details)
            info_btn.pack(side="right", fill="x", expand=True, padx=(4, 0))
    
    def install_game(self):
        print(f"Installing: {self.game_data['game_name']}")
        # Get the main app instance from the master hierarchy
        if hasattr(self, 'mom') and hasattr(self.mom, 'add_to_download_queue'):
            self.mom.add_to_download_queue(self.game_data, 'install')
        else:
            print(f"Could not find main app instance to add {self.game_data['game_name']} to queue")
    
    def update_game(self):
        print(f"Updating: {self.game_data['game_name']}")
        # Get the main app instance
        if hasattr(self, 'mom') and hasattr(self.mom, 'add_to_download_queue'):
            self.mom.add_to_download_queue(self.game_data, 'update')
    
    def uninstall_game(self):
        print(f"Uninstalling: {self.game_data['game_name']}")
        success = self.downloader.uninstall_game(self.game_data['game_name'])
        if success and self.refresh_callback:
            self.refresh_callback()
    
    def play_game(self):
        # First things first
        if hasattr(self, 'mom'):
            if self.mom.game_open:
                # Warn that a game is already open
                messagebox.showwarning("Game already open", "A game is already open. Please close the currently open game before playing another one.")
                return
            else:
                self.mom.game_open = True
            
            
    
    def show_details(self):
        # Create details dialog
        dialog = tk.CTkToplevel(self)
        dialog.title(f"Details - {self.game_data['game_name']}")
        dialog.geometry("500x600")
        dialog.minsize(400, 500)
        dialog.transient(self.master)
        dialog.grab_set()
        dialog.configure(fg_color=self.theme['bg'])
        
        # Scrollable content
        scroll_frame = tk.CTkScrollableFrame(dialog, fg_color=self.theme['bg'])
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Installation status
        status_text = "Not installed"
        status_color = self.theme['text_secondary']
        
        if self.install_status['installed']:
            needs_update, current_version = self.downloader.needs_update(
                self.game_data['game_name'], 
                self.game_data['game_version']
            )
            if needs_update:
                status_text = f"Installed (v{current_version}) - Update available"
                status_color = self.theme['update_badge']
            else:
                status_text = f"Installed (v{current_version}) - Up to date"
                status_color = self.theme['installed_badge']
        
        tk.CTkLabel(scroll_frame,
                   text=status_text,
                   font=("RobotoMono", 11, "bold"),
                   text_color=status_color).pack(anchor="w", pady=(0, 15))
        
        # Game info
        info_grid = [
            ("Name", self.game_data['game_name']),
            ("Version", self.game_data['game_version']),
            ("Author", self.game_data['game_author']),
            ("Category", self.game_data['game_category']),
            ("Size", f"{self.game_data['total_size']:.2f} MB"),
            ("Files", str(self.game_data['total_files']))
        ]
        
        for label, value in info_grid:
            frame = tk.CTkFrame(scroll_frame, fg_color="transparent")
            frame.pack(fill="x", pady=3)
            
            tk.CTkLabel(frame,
                       text=f"{label}:",
                       font=("RobotoMono", 11, "bold"),
                       text_color=self.theme['text_secondary'],
                       width=80,
                       anchor="w").pack(side="left")
            
            tk.CTkLabel(frame,
                       text=value,
                       font=("RobotoMono", 11),
                       text_color=self.theme['text_primary'],
                       anchor="w").pack(side="left", fill="x", expand=True)
        
        # Description
        tk.CTkLabel(scroll_frame,
                   text="Description:",
                   font=("RobotoMono", 11, "bold"),
                   text_color=self.theme['text_secondary']).pack(anchor="w", pady=(15, 5))
        
        desc_text = tk.CTkTextbox(scroll_frame,
                                 height=100,
                                 fg_color=self.theme['fg'],
                                 text_color=self.theme['text_secondary'],
                                 border_width=0,
                                 font=("RobotoMono", 11))
        desc_text.insert("1.0", self.game_data['game_description'])
        desc_text.configure(state="disabled")
        desc_text.pack(fill="x", pady=(0, 10))
        
        # All tags
        tk.CTkLabel(scroll_frame,
                   text="Tags:",
                   font=("RobotoMono", 11, "bold"),
                   text_color=self.theme['text_secondary']).pack(anchor="w", pady=(5, 5))
        
        tags_frame = tk.CTkFrame(scroll_frame, fg_color="transparent")
        tags_frame.pack(fill="x", pady=(0, 10))
        
        for tag in self.game_data['game_tags']:
            tk.CTkLabel(tags_frame,
                       text=tag,
                       font=("RobotoMono", 10),
                       text_color=self.theme['text_accent'],
                       fg_color=self.theme['tag_bg'],
                       corner_radius=12,
                       padx=8, pady=3).pack(side="left", padx=(0, 5))
        
        # Requirements
        tk.CTkLabel(scroll_frame,
                   text="Requirements:",
                   font=("RobotoMono", 11, "bold"),
                   text_color=self.theme['text_secondary']).pack(anchor="w", pady=(5, 5))
        
        for req in self.game_data['requirements']:
            tk.CTkLabel(scroll_frame,
                       text=f"• {req}",
                       font=("RobotoMono", 10),
                       text_color=self.theme['text_primary'],
                       anchor="w").pack(anchor="w", pady=1)
        
        close_btn = tk.CTkButton(dialog,
                                text="Close",
                                command=dialog.destroy,
                                fg_color=self.theme['button_secondary'],
                                hover_color=self.theme['button_secondary_hover'])
        close_btn.pack(pady=(0, 20))

class App(tk.CTk):
    game_open: bool = False
    game_open_name: str = ""
    game_open_thread: Thread = None
    def __init__(self):
        super().__init__()
        
        # Set appearance
        theme_preference = self.load_theme_preference()
        self.current_theme = theme_preference
        self.theme_config = ThemeManager.get_theme(theme_preference)
        
        tk.set_appearance_mode("light" if theme_preference == "light" else "dark")
        
        self.title('LunaLauncher')
        self.geometry('1300x850')
        self.minsize(1000, 650)
        
        # Theme and data initialization
        self.game_data: dict = {}
        self.game_cards = []
        
        # Load game data FIRST
        self.get_game_data()
        
        # Initialize downloader with game data
        self.downloader = Downloader(self.game_data)
        
        # Download queue system
        self.download_queue = []
        self.current_download = None
        self.download_progress = {}
        
        # Filter state
        self.current_filters = {
            'category': 'all',
            'tags': set(),
            'author': 'all',
            'sort_by': 'name',
            'search': '',
            'installation': 'all'
        }
        
        # Filter data
        self.all_tags = set()
        self.all_authors = set()
        self.all_categories = set()
        
        # Create UI FIRST
        self.create_menu()
        self.create_progress_display()
        
        # Now load initial data and populate UI
        self.load_initial_data()
    
    def get_game_data(self):
        """Load game data from local or remote"""
        if run_mode == '--local':
            possible_paths = [
                os.path.join(Path.games, 'data.json'),
                os.path.join(os.getcwd(), 'data.json'),
                os.path.join(os.path.dirname(os.getcwd()), 'games', 'data.json')
            ]
            
            data_loaded = False
            for data_path in possible_paths:
                if os.path.exists(data_path):
                    try:
                        with open(data_path, 'r', encoding='utf-8') as f:
                            self.game_data = json.load(f)
                        print(f"Loaded data from: {data_path}")
                        data_loaded = True
                        break
                    except Exception as e:
                        print(f"Error loading {data_path}: {e}")
            
            if not data_loaded:
                print("Warning: Could not find data.json in local mode")
                self.game_data = {
                    "info": {"version": "0.0.0", "author": "Unknown", "total_games": 0},
                    "games": []
                }
        else:
            try:
                print(f"Loading remote data from: {Path.data_remote}")
                response = requests.get(Path.data_remote, timeout=10)
                response.raise_for_status()
                self.game_data = response.json()
                print(f"Successfully loaded remote data")
            except Exception as e:
                print(f"Error loading remote data: {e}")
                self.game_data = {
                    "info": {"version": "0.0.0", "author": "Unknown", "total_games": 0},
                    "games": []
                }
    
    def load_initial_data(self):
        """Load data and populate UI after creation"""
        # Extract filter data from game data
        self.extract_filter_data()
        
        # Update filter widgets
        self.update_filter_widgets()
        
        # Apply filters to populate games
        self.apply_filters()
    
    def extract_filter_data(self):
        """Extract unique filter values from game data"""
        self.all_tags.clear()
        self.all_authors.clear()
        self.all_categories.clear()
        
        if "games" in self.game_data:
            for game in self.game_data.get('games', []):
                self.all_authors.add(game['game_author'])
                self.all_categories.add(game['game_category'])
                for tag in game['game_tags']:
                    self.all_tags.add(tag)
    
    def apply_filters(self):
        """Apply filters and refresh display"""
        # Check if UI is initialized
        if not hasattr(self, 'games_container'):
            print("UI not initialized yet, skipping apply_filters")
            return
        
        # Remove loading label if exists
        if hasattr(self, 'loading_label'):
            self.loading_label.destroy()
            del self.loading_label
        
        # Clear current cards
        for card in self.game_cards:
            card.destroy()
        self.game_cards.clear()
        
        # Check if we have games data
        if "games" not in self.game_data or len(self.game_data['games']) == 0:
            empty_label = tk.CTkLabel(self.games_container,
                                    text="No games found\nTry refreshing or check your connection",
                                    font=("RobotoSerif", 16),
                                    text_color=self.theme_config['text_secondary'],
                                    justify="center")
            empty_label.pack(pady=100, fill="both", expand=True)
            
            if hasattr(self, 'games_header'):
                self.games_header.configure(text="No Games Available")
            
            if hasattr(self, 'stats_label'):
                self.stats_label.configure(text="")
            
            return
        
        # Filter games
        filtered_games = FilterManager.filter_games(
            self.game_data.get('games', []),
            self.current_filters,
            self.downloader
        )
        
        # Sort games
        sorted_games = FilterManager.sort_games(
            filtered_games, 
            self.current_filters['sort_by'],
            self.downloader
        )
        
        # Update count
        self.update_game_count(len(sorted_games), len(self.game_data.get('games', [])))
        
        # Create container frame for cards using grid
        if hasattr(self, 'cards_container'):
            self.cards_container.destroy()
        
        self.cards_container = tk.CTkFrame(self.games_container, fg_color="transparent")
        self.cards_container.pack(fill="both", expand=True)
        
        # Calculate number of columns based on container width
        container_width = self.games_container.winfo_width()
        card_width = 280
        spacing = 20
        
        # Use default if container not yet rendered
        if container_width > 10:
            num_columns = max(1, int((container_width - 40) / (card_width + spacing)))
        else:
            num_columns = 3
        
        # Create cards using grid
        for i, game in enumerate(sorted_games):
            row = i // num_columns
            col = i % num_columns
            
            card = ResponsiveGameCard(
                self.cards_container, 
                game, 
                i, 
                self.theme_config,
                self.downloader,
                self.refresh_games,
                width=card_width, 
                height=340
            )
            card.mom = self
            self.game_cards.append(card)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nw")
        
        # Configure grid columns to be equal width
        for col in range(num_columns):
            self.cards_container.grid_columnconfigure(col, weight=1, uniform="card_col")
        
        # Update stats
        installed_count = len(self.downloader.get_all_installed_games())
        total_games = len(self.game_data.get('games', []))
        
        if hasattr(self, 'stats_label'):
            self.stats_label.configure(text=f"Installed: {installed_count}/{total_games}")
        
        # Bind resize event
        self.games_container.bind('<Configure>', self.on_container_resize)
    
    def on_container_resize(self, event=None):
        """Handle container resize to adjust grid columns"""
        if hasattr(self, 'cards_container') and hasattr(self, 'game_cards') and self.game_cards:
            container_width = self.games_container.winfo_width()
            card_width = 280
            spacing = 20
            num_columns = max(1, int((container_width - 40) / (card_width + spacing)))
            
            # Re-grid existing cards
            for i, card in enumerate(self.game_cards):
                row = i // num_columns
                col = i % num_columns
                card.grid(row=row, column=col, padx=10, pady=10, sticky="nw")
            
            # Reconfigure grid columns
            for col in range(num_columns):
                self.cards_container.grid_columnconfigure(col, weight=1, uniform="card_col")
    
    def update_game_count(self, filtered_count: int, total_count: int):
        """Update game count display"""
        if not hasattr(self, 'games_header'):
            return
            
        if filtered_count == total_count:
            self.games_header.configure(text=f"Games ({total_count})")
        else:
            self.games_header.configure(text=f"Games ({filtered_count} of {total_count})")
    
    def show_theme_menu(self):
        """Show theme selection menu (legacy method, now replaced by settings)"""
        self.show_settings()  # Redirect to settings page
    
    def on_tag_toggle(self, tag: str):
        """Handle tag selection/deselection"""
        if tag == 'clear_all':
            self.current_filters['tags'].clear()
            if hasattr(self, 'tag_frame') and hasattr(self.tag_frame, 'tag_buttons'):
                for btn in self.tag_frame.tag_buttons.values():
                    btn.configure(fg_color=self.theme_config['input_bg'],
                                text_color=self.theme_config['text_secondary'])
        else:
            if tag in self.current_filters['tags']:
                self.current_filters['tags'].remove(tag)
                if hasattr(self, 'tag_frame') and hasattr(self.tag_frame, 'tag_buttons') and tag in self.tag_frame.tag_buttons:
                    self.tag_frame.tag_buttons[tag].configure(
                        fg_color=self.theme_config['input_bg'],
                        text_color=self.theme_config['text_secondary']
                    )
            else:
                self.current_filters['tags'].add(tag)
                if hasattr(self, 'tag_frame') and hasattr(self.tag_frame, 'tag_buttons') and tag in self.tag_frame.tag_buttons:
                    self.tag_frame.tag_buttons[tag].configure(
                        fg_color=self.theme_config['button_primary'],
                        text_color=self.theme_config['text_primary']
                    )
        
        self.apply_filters()
    
    def on_installation_filter_change(self, choice):
        """Handle installation filter change"""
        for key, value in FilterManager.INSTALLATION_FILTERS.items():
            if value == choice:
                self.current_filters['installation'] = key
                break
        self.apply_filters()
    
    def change_theme(self, theme_name: str):
        """Change application theme and save preference"""
        self.current_theme = theme_name
        self.theme_config = ThemeManager.get_theme(theme_name)
        
        # Save theme preference
        self.save_theme_preference(theme_name)
        
        tk.set_appearance_mode("light" if theme_name == "light" else "dark")
        self.configure(fg_color=self.theme_config['bg'])
        
        # Refresh display
        self.apply_filters()

    def save_theme_preference(self, theme_name: str):
        """Save theme preference to config file"""
        try:
            config_path = os.path.join(Path.config, 'settings.json')
            settings = {}
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    settings = json.load(f)
            
            settings['theme'] = theme_name
            
            with open(config_path, 'w') as f:
                json.dump(settings, f, indent=2)
                
            print(f"Theme preference saved: {theme_name}")
        except Exception as e:
            print(f"Error saving theme preference: {e}")

    def load_theme_preference(self):
        """Load theme preference from config file"""
        try:
            config_path = os.path.join(Path.config, 'settings.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    settings = json.load(f)
                    theme = settings.get('theme', 'dark')
                    return theme
        except:
            pass
        return 'dark'
    
    def show_theme_menu(self):
        """Show theme selection menu"""
        theme_menu = tk.CTkToplevel(self)
        theme_menu.title("Select Theme")
        theme_menu.geometry("250x150")
        theme_menu.transient(self)
        theme_menu.grab_set()
        theme_menu.configure(fg_color=self.theme_config['bg'])
        
        tk.CTkLabel(theme_menu,
                   text="Choose Theme:",
                   font=("RobotoSerif", 14, "bold"),
                   text_color=self.theme_config['text_primary']).pack(pady=10)
        
        for theme_name in ThemeManager.get_theme_names():
            theme_data = ThemeManager.get_theme(theme_name)
            btn = tk.CTkButton(theme_menu,
                             text=theme_data['name'],
                             fg_color=self.theme_config['button_primary'],
                             hover_color=self.theme_config['button_primary_hover'],
                             command=lambda t=theme_name: [self.change_theme(t), theme_menu.destroy()])
            btn.pack(pady=2, padx=30, fill="x")
    
    def refresh_games(self):
        """Refresh all game data"""
        self.get_game_data()
        self.downloader.games_data = self.game_data
        self.downloader.get_games()
        
        self.extract_filter_data()
        self.update_filter_widgets()
        self.apply_filters()
    
    def update_filter_widgets(self):
        """Update filter widgets with current data"""
        # Update category dropdown
        categories = ['all'] + sorted(list(self.all_categories))
        self.category_var.set('all')
        self.category_dropdown.configure(values=categories)
        
        # Update author dropdown
        authors = ['all'] + sorted(list(self.all_authors))
        self.author_var.set('all')
        self.author_dropdown.configure(values=authors)
        
        # Update sort dropdown
        self.sort_var.set(FilterManager.SORT_OPTIONS['name'])
        
        # Update installation filter
        self.installation_var.set(FilterManager.INSTALLATION_FILTERS['all'])
        
        # Remove old tag frame if exists
        if hasattr(self, 'tag_frame'):
            try:
                self.tag_frame.destroy()
            except:
                pass
        
        # Create tag widgets only if we have tags
        if self.all_tags:
            self.tag_frame = TagManager.create_tag_widgets(
                self.sidebar,
                self.all_tags,
                self.current_filters['tags'],
                self.theme_config,
                self.on_tag_toggle,
                max_height=180
            )
            
            # Insert tag frame before sort dropdown
            self.tag_frame.pack(fill="x", padx=15, pady=(0, 15), before=self.sort_dropdown)
        else:
            # Create placeholder for tags
            self.tag_frame = tk.CTkFrame(self.sidebar, fg_color="transparent")
            self.tag_frame.pack(fill="x", padx=15, pady=(0, 15), before=self.sort_dropdown)
            tk.CTkLabel(self.tag_frame,
                       text="Tags:",
                       font=("RobotoMono", 11),
                       text_color=self.theme_config['text_secondary']).pack(anchor="w", pady=(0, 8))
            tk.CTkLabel(self.tag_frame,
                       text="No tags available",
                       font=("RobotoMono", 10),
                       text_color=self.theme_config['text_secondary']).pack(anchor="w")
    
    def create_progress_display(self):
        """Create progress bar and queue display"""
        # Progress bar at the bottom
        self.progress_frame = tk.CTkFrame(self.main_container, 
                                         height=60, 
                                         fg_color=self.theme_config['card_bg'],
                                         border_width=1,
                                         border_color=self.theme_config['card_border'])
        
        # Place in grid at row 1 (below the main content at row 0)
        self.progress_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        self.progress_frame.grid_propagate(False)
        
        # Initially hidden
        self.progress_frame.grid_remove()
        
        # Progress content
        self.progress_label = tk.CTkLabel(self.progress_frame,
                                         text="",
                                         font=("RobotoMono", 11),
                                         text_color=self.theme_config['text_primary'])
        self.progress_label.pack(pady=(10, 5), padx=20, anchor="w")
        
        self.progress_bar = tk.CTkProgressBar(self.progress_frame,
                                             height=6,
                                             fg_color=self.theme_config['input_bg'],
                                             progress_color=self.theme_config['button_primary'])
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 10))
        self.progress_bar.set(0)
        
        # Queue label
        self.queue_label = tk.CTkLabel(self.progress_frame,
                                      text="",
                                      font=("RobotoMono", 10),
                                      text_color=self.theme_config['text_secondary'])
        self.queue_label.pack(pady=(0, 10), padx=20, anchor="w")
    
    def add_to_download_queue(self, game_data, action='install'):
        """Add a game to the download queue"""
        self.download_queue.append({
            'game': game_data,
            'action': action,
            'status': 'pending',
            'progress': 0
        })
        print(f"Added {game_data['game_name']} to download queue")
        
        # Start processing if not already downloading
        if not self.current_download:
            self.process_download_queue()
        
        self.update_queue_display()
    
    def process_download_queue(self):
        """Process the next item in the download queue"""
        if not self.download_queue:
            self.current_download = None
            self.hide_progress()
            return
        
        # Get the next item
        item = self.download_queue[0]
        self.current_download = item
        
        # Show progress frame
        self.show_progress()
        
        # Update display
        action_text = "Installing" if item['action'] == 'install' else "Updating"
        self.progress_label.configure(text=f"{action_text}: {item['game']['game_name']}")
        self.update_queue_display()
        
        # Start the actual download
        self.start_download(item)
    
    def start_download(self, item):
        """Start downloading a game from the queue"""
        def progress_callback(percent, status):
            self.on_download_progress(item['game']['game_name'], percent, status)
        
        # Start the download
        self.downloader.download_game(
            item['game'], 
            progress_callback=progress_callback
        )
    
    def on_download_progress(self, game_name, percent, status):
        """Handle download progress updates"""
        if self.current_download and self.current_download['game']['game_name'] == game_name:
            self.progress_bar.set(percent / 100)
            self.current_download['progress'] = percent
            
            # Update status text
            self.progress_label.configure(
                text=f"{status} - {game_name} ({percent:.1f}%)"
            )
            
            if percent >= 100:
                # Download complete
                if self.download_queue:
                    self.download_queue.pop(0)
                
                # Force reload installed games registry
                self.downloader.installed_games = self.downloader.load_installed_games()
                
                # Process next in queue
                self.progress_bar.set(0)
                self.current_download = None
                self.process_download_queue()
                
                self.get_game_data()
                self.downloader.games_data = self.game_data
                self.extract_filter_data()
                self.update_filter_widgets()
                self.apply_filters()
    
    def show_progress(self):
        """Show progress display"""
        self.progress_frame.grid()
    
    def hide_progress(self):
        """Hide progress display"""
        self.progress_frame.grid_remove()
    
    def update_queue_display(self):
        """Update queue status display"""
        if self.download_queue:
            total = len(self.download_queue)
            current = 1 if self.current_download else 0
            remaining = total - current
            
            queue_text = f"Queue: {current}/{total}"
            if remaining > 0:
                queue_text += f" ({remaining} waiting)"
            
            self.queue_label.configure(text=queue_text)
        else:
            self.queue_label.configure(text="")
    
    def clear_download_queue(self):
        """Clear the download queue"""
        self.download_queue.clear()
        self.current_download = None
        self.hide_progress()
    
    def create_menu(self):
        """Create the main interface"""
        # Main container
        self.main_container = tk.CTkFrame(self, fg_color=self.theme_config['bg'])
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configure grid
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(1, weight=0)
        
        # Sidebar (Filters)
        self.sidebar = tk.CTkFrame(self.main_container,
                                width=320,
                                corner_radius=10,
                                fg_color=self.theme_config['sidebar'],
                                border_width=1,
                                border_color=self.theme_config['sidebar_border'])
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.sidebar.grid_propagate(False)
        
        # Title
        tk.CTkLabel(self.sidebar,
                   text="FILTERS & SORT",
                   font=("RobotoMono", 18, "bold"),
                   text_color=self.theme_config['text_primary']).pack(pady=(20, 15), padx=20)
        
        # Search
        tk.CTkLabel(self.sidebar,
                   text="Search:",
                   font=("RobotoMono", 11),
                   text_color=self.theme_config['text_secondary']).pack(anchor="w", padx=20, pady=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.current_filters.update({'search': self.search_var.get()}) or self.apply_filters())
        search_entry = tk.CTkEntry(self.sidebar,
                   textvariable=self.search_var,
                   placeholder_text="Search games...",
                   fg_color=self.theme_config['input_bg'],
                   border_color=self.theme_config['input_border'],
                   height=35)
        search_entry.pack(fill="x", padx=20, pady=(0, 15))
        
        # Installation filter
        tk.CTkLabel(self.sidebar,
                   text="Installation:",
                   font=("RobotoMono", 11),
                   text_color=self.theme_config['text_secondary']).pack(anchor="w", padx=20, pady=(0, 5))
        
        self.installation_var = tk.StringVar(value=FilterManager.INSTALLATION_FILTERS['all'])
        self.installation_dropdown = tk.CTkOptionMenu(self.sidebar,
                                                     variable=self.installation_var,
                                                     values=list(FilterManager.INSTALLATION_FILTERS.values()),
                                                     command=self.on_installation_filter_change,
                                                     fg_color=self.theme_config['input_bg'],
                                                     button_color=self.theme_config['button_secondary'],
                                                     button_hover_color=self.theme_config['button_secondary_hover'],
                                                     height=35)
        self.installation_dropdown.pack(fill="x", padx=20, pady=(0, 15))
        
        # Category filter
        tk.CTkLabel(self.sidebar,
                   text="Category:",
                   font=("RobotoMono", 11),
                   text_color=self.theme_config['text_secondary']).pack(anchor="w", padx=20, pady=(0, 5))
        
        self.category_var = tk.StringVar(value="all")
        self.category_dropdown = tk.CTkOptionMenu(self.sidebar,
                                                 variable=self.category_var,
                                                 values=['all'],
                                                 command=lambda c: self.current_filters.update({'category': c}) or self.apply_filters(),
                                                 fg_color=self.theme_config['input_bg'],
                                                 button_color=self.theme_config['button_secondary'],
                                                 button_hover_color=self.theme_config['button_secondary_hover'],
                                                 height=35)
        self.category_dropdown.pack(fill="x", padx=20, pady=(0, 15))
        
        # Author filter
        tk.CTkLabel(self.sidebar,
                   text="Author:",
                   font=("RobotoMono", 11),
                   text_color=self.theme_config['text_secondary']).pack(anchor="w", padx=20, pady=(0, 5))
        
        self.author_var = tk.StringVar(value="all")
        self.author_dropdown = tk.CTkOptionMenu(self.sidebar,
                                               variable=self.author_var,
                                               values=['all'],
                                               command=lambda a: self.current_filters.update({'author': a}) or self.apply_filters(),
                                               fg_color=self.theme_config['input_bg'],
                                               button_color=self.theme_config['button_secondary'],
                                               button_hover_color=self.theme_config['button_secondary_hover'],
                                               height=35)
        self.author_dropdown.pack(fill="x", padx=20, pady=(0, 15))
        
        # Sort by
        tk.CTkLabel(self.sidebar,
                   text="Sort by:",
                   font=("RobotoMono", 11),
                   text_color=self.theme_config['text_secondary']).pack(anchor="w", padx=20, pady=(0, 5))
        
        self.sort_var = tk.StringVar(value=FilterManager.SORT_OPTIONS['name'])
        self.sort_dropdown = tk.CTkOptionMenu(self.sidebar,
                                             variable=self.sort_var,
                                             values=list(FilterManager.SORT_OPTIONS.values()),
                                             command=lambda s: self.current_filters.update({'sort_by': 
                                                                                          [k for k, v in FilterManager.SORT_OPTIONS.items() if v == s][0]}) or self.apply_filters(),
                                             fg_color=self.theme_config['input_bg'],
                                             button_color=self.theme_config['button_secondary'],
                                             button_hover_color=self.theme_config['button_secondary_hover'],
                                             height=35)
        self.sort_dropdown.pack(fill="x", padx=20, pady=(0, 20))
        
        # Action buttons
        action_frame = tk.CTkFrame(self.sidebar, fg_color="transparent")
        action_frame.pack(side="bottom", fill="x", padx=20, pady=20)
        
        # Clear Queue button
        tk.CTkButton(action_frame,
                    text="Clear Queue",
                    fg_color=self.theme_config['warning'],
                    hover_color=self.theme_config['button_update_hover'],
                    command=self.clear_download_queue,
                    height=35).pack(fill="x", pady=(0, 10))
        
        # Clear filters
        tk.CTkButton(action_frame,
                    text="Clear Filters",
                    fg_color=self.theme_config['button_secondary'],
                    hover_color=self.theme_config['button_secondary_hover'],
                    command=self.clear_filters,
                    height=35).pack(fill="x", pady=(0, 10))
        
        # Change theme
        tk.CTkButton(action_frame,
                    text="Change Theme",
                    fg_color=self.theme_config['button_primary'],
                    hover_color=self.theme_config['button_primary_hover'],
                    command=self.show_theme_menu,
                    height=35).pack(fill="x", pady=(0, 10))
        
        # Refresh button
        tk.CTkButton(action_frame,
                    text="Refresh All",
                    fg_color=self.theme_config['info'],
                    hover_color=self.theme_config['button_secondary_hover'],
                    command=self.refresh_games,
                    height=35).pack(fill="x", pady=(0, 10))
        
        # Mode indicator
        mode_color = self.theme_config['success'] if run_mode == "--local" else self.theme_config['info']
        mode_text = "LOCAL MODE" if run_mode == "--local" else "REMOTE MODE"
        tk.CTkLabel(action_frame,
                   text=mode_text,
                   font=("RobotoMono", 10, "bold"),
                   text_color=mode_color).pack(pady=(10, 0))
        
        # Main content area
        self.content_frame = tk.CTkFrame(self.main_container, fg_color=self.theme_config['bg'])
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        
        # Header
        header_frame = tk.CTkFrame(self.content_frame, fg_color="transparent", height=60)
        header_frame.pack(fill="x", pady=(0, 15))
        header_frame.pack_propagate(False)
        
        # Left side: Title and refresh button
        title_frame = tk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side="left", padx=20)
        
        self.games_header = tk.CTkLabel(title_frame,
                                    text="Loading...",
                                    font=("RobotoSerif", 24, "bold"),
                                    text_color=self.theme_config['text_primary'])
        self.games_header.pack(side="left")
        
        # Add refresh button next to title
        self.refresh_btn = tk.CTkButton(title_frame,
                                    text="Refresh Games",
                                    width=40,
                                    height=40,
                                    fg_color=self.theme_config['button_secondary'],
                                    hover_color=self.theme_config['button_secondary_hover'],
                                    font=("RobotoMono", 16, "bold"),
                                    command=self.refresh_games)
        self.refresh_btn.pack(side="left", padx=(10, 0))
        
        # Right side: Stats and settings button
        right_frame = tk.CTkFrame(header_frame, fg_color="transparent")
        right_frame.pack(side="right", padx=20)
        
        self.stats_label = tk.CTkLabel(right_frame,
                                    text="",
                                    font=("RobotoMono", 11),
                                    text_color=self.theme_config['text_secondary'])
        self.stats_label.pack(side="right", padx=(0, 10))
        
        # Add settings button
        self.settings_btn = tk.CTkButton(right_frame,
                                        text="Settings",
                                        width=40,
                                        height=40,
                                        fg_color=self.theme_config['button_secondary'],
                                        hover_color=self.theme_config['button_secondary_hover'],
                                        font=("RobotoMono", 16),
                                        command=self.show_settings)
        self.settings_btn.pack(side="right", padx=(0, 30))
        
        # Games container
        self.games_container = tk.CTkScrollableFrame(self.content_frame,
                                                    fg_color=self.theme_config['bg'],
                                                    scrollbar_button_color=self.theme_config['scrollbar'])
        self.games_container.pack(fill="both", expand=True)
        
        # Show loading message
        self.loading_label = tk.CTkLabel(self.games_container,
                                        text="Loading games...",
                                        font=("RobotoSerif", 16),
                                        text_color=self.theme_config['text_secondary'])
        self.loading_label.pack(pady=100)
        
    def show_settings(self):
        """Show settings dialog"""
        settings_dialog = tk.CTkToplevel(self)
        settings_dialog.title("Settings")
        settings_dialog.geometry("500x600")
        settings_dialog.minsize(400, 500)
        settings_dialog.transient(self)
        settings_dialog.grab_set()
        settings_dialog.configure(fg_color=self.theme_config['bg'])
        
        # Title
        tk.CTkLabel(settings_dialog,
                text="Settings",
                font=("RobotoSerif", 24, "bold"),
                text_color=self.theme_config['text_primary']).pack(pady=(20, 30))
        
        # Scrollable content
        scroll_frame = tk.CTkScrollableFrame(settings_dialog, 
                                            fg_color=self.theme_config['bg'])
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Theme Selection
        tk.CTkLabel(scroll_frame,
                text="Theme",
                font=("RobotoSerif", 16, "bold"),
                text_color=self.theme_config['text_primary']).pack(anchor="w", pady=(0, 10))
        
        theme_frame = tk.CTkFrame(scroll_frame, fg_color="transparent")
        theme_frame.pack(fill="x", pady=(0, 20))
        
        # Current theme display
        current_theme_label = tk.CTkLabel(theme_frame,
                                        text=f"Current: {self.current_theme.title()}",
                                        font=("RobotoMono", 12),
                                        text_color=self.theme_config['text_secondary'])
        current_theme_label.pack(side="left", padx=(0, 20))
        
        # Theme selection buttons in a grid
        theme_grid_frame = tk.CTkFrame(scroll_frame, fg_color="transparent")
        theme_grid_frame.pack(fill="x", pady=(0, 20))
        
        theme_names = ThemeManager.get_theme_names()
        for i, theme_name in enumerate(theme_names):
            theme_data = ThemeManager.get_theme(theme_name)
            row = i // 2
            col = i % 2
            
            btn = tk.CTkButton(theme_grid_frame,
                            text=theme_data['name'],
                            fg_color=theme_data['button_primary'],
                            hover_color=theme_data['button_primary_hover'],
                            command=lambda t=theme_name, l=current_theme_label: [
                                self.change_theme(t),
                                l.configure(text=f"Current: {t.title()}"),
                                settings_dialog.destroy()
                            ])
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
        
        # Configure grid columns
        theme_grid_frame.grid_columnconfigure(0, weight=1)
        theme_grid_frame.grid_columnconfigure(1, weight=1)
        
        # System Tools
        tk.CTkLabel(scroll_frame,
                text="System Tools",
                font=("RobotoSerif", 16, "bold"),
                text_color=self.theme_config['text_primary']).pack(anchor="w", pady=(0, 10))
        
        tools_frame = tk.CTkFrame(scroll_frame, fg_color="transparent")
        tools_frame.pack(fill="x", pady=(0, 20))
        
        # Clear Cache button
        tk.CTkButton(tools_frame,
                    text="Clear Cache",
                    fg_color=self.theme_config['warning'],
                    hover_color=self.theme_config['button_update_hover'],
                    command=lambda: self.clear_cache(settings_dialog),
                    height=35).pack(fill="x", pady=(0, 10))
        
        # Clear Temp Files button
        tk.CTkButton(tools_frame,
                    text="Clear Temp Files",
                    fg_color=self.theme_config['warning'],
                    hover_color=self.theme_config['button_update_hover'],
                    command=lambda: self.clear_temp_files(settings_dialog),
                    height=35).pack(fill="x", pady=(0, 10))
        
        # Links Section
        tk.CTkLabel(scroll_frame,
                text="Links",
                font=("RobotoSerif", 16, "bold"),
                text_color=self.theme_config['text_primary']).pack(anchor="w", pady=(0, 10))
        
        links_frame = tk.CTkFrame(scroll_frame, fg_color="transparent")
        links_frame.pack(fill="x", pady=(0, 20))
        
        # GitHub button
        tk.CTkButton(links_frame,
                    text="GitHub Repository",
                    fg_color=self.theme_config['info'],
                    hover_color=self.theme_config['button_secondary_hover'],
                    command=lambda: self.open_link("https://github.com/MrJuaumBR/LunaEngine-Games/"),
                    height=35,
                    image=self.create_icon_image("github")).pack(fill="x", pady=(0, 10))
        
        # YouTube button
        tk.CTkButton(links_frame,
                    text="YouTube Channel",
                    fg_color=self.theme_config['danger'],
                    hover_color="#ff0000",
                    command=lambda: self.open_link("https://www.youtube.com/@mrjuaumbr"),
                    height=35,
                    image=self.create_icon_image("youtube")).pack(fill="x", pady=(0, 10))
        
        # Discord button
        tk.CTkButton(links_frame,
                    text="Discord Server",
                    fg_color="#5865F2",
                    hover_color="#4752C4",
                    command=lambda: self.open_link("https://discord.gg/fb84sHDX7R"),
                    height=35,
                    image=self.create_icon_image("discord")).pack(fill="x", pady=(0, 10))
        
        # Close button
        tk.CTkButton(settings_dialog,
                    text="Close",
                    fg_color=self.theme_config['button_secondary'],
                    hover_color=self.theme_config['button_secondary_hover'],
                    command=settings_dialog.destroy,
                    height=40).pack(pady=(0, 20))
        
    def create_icon_image(self, icon_type: str):
        """Create simple icon images for buttons"""
        # This is a placeholder - you can replace with actual icons
        # For now, we'll use text icons
        return None  # You can add actual icons later

    def open_link(self, url: str):
        """Open a URL in the default browser"""
        import webbrowser
        try:
            webbrowser.open(url)
            print(f"Opened: {url}")
        except Exception as e:
            print(f"Error opening link: {e}")

    def clear_cache(self, parent_window=None):
        """Clear the cache directory"""
        try:
            cache_path = os.path.join(os.getcwd(), 'cache')
            if os.path.exists(cache_path):
                shutil.rmtree(cache_path)
                os.makedirs(cache_path)
                print("Cache cleared successfully")
                
                # Show success message
                if parent_window:
                    self.show_message("Success", "Cache cleared successfully", parent_window)
                else:
                    print("Cache cleared successfully")
            else:
                if parent_window:
                    self.show_message("Info", "Cache directory doesn't exist", parent_window)
                else:
                    print("Cache directory doesn't exist")
                    
        except Exception as e:
            print(f"Error clearing cache: {e}")
            if parent_window:
                self.show_message("Error", f"Failed to clear cache: {str(e)}", parent_window)

    def clear_temp_files(self, parent_window=None):
        """Clear temporary files"""
        try:
            temp_path = os.path.join(os.getcwd(), 'temp')
            if os.path.exists(temp_path):
                shutil.rmtree(temp_path)
                os.makedirs(temp_path)
                print("Temp files cleared successfully")
                
                # Show success message
                if parent_window:
                    self.show_message("Success", "Temporary files cleared successfully", parent_window)
                else:
                    print("Temp files cleared successfully")
            else:
                if parent_window:
                    self.show_message("Info", "Temp directory doesn't exist", parent_window)
                else:
                    print("Temp directory doesn't exist")
                    
        except Exception as e:
            print(f"Error clearing temp files: {e}")
            if parent_window:
                self.show_message("Error", f"Failed to clear temp files: {str(e)}", parent_window)

    def show_message(self, title: str, message: str, parent):
        """Show a message dialog"""
        msg_dialog = tk.CTkToplevel(parent)
        msg_dialog.title(title)
        msg_dialog.geometry("400x200")
        msg_dialog.transient(parent)
        msg_dialog.grab_set()
        msg_dialog.configure(fg_color=self.theme_config['bg'])
        
        tk.CTkLabel(msg_dialog,
                text=title,
                font=("RobotoSerif", 18, "bold"),
                text_color=self.theme_config['text_primary']).pack(pady=(20, 10))
        
        tk.CTkLabel(msg_dialog,
                text=message,
                font=("RobotoMono", 12),
                text_color=self.theme_config['text_secondary'],
                wraplength=350).pack(pady=(0, 20), padx=20)
        
        tk.CTkButton(msg_dialog,
                    text="OK",
                    fg_color=self.theme_config['button_primary'],
                    hover_color=self.theme_config['button_primary_hover'],
                    command=msg_dialog.destroy).pack(pady=(0, 20))
    
    def clear_filters(self):
        """Clear all filters"""
        self.search_var.set('')
        self.category_var.set('all')
        self.author_var.set('all')
        self.installation_var.set(FilterManager.INSTALLATION_FILTERS['all'])
        self.sort_var.set(FilterManager.SORT_OPTIONS['name'])
        
        self.current_filters = {
            'category': 'all',
            'tags': set(),
            'author': 'all',
            'sort_by': 'name',
            'search': '',
            'installation': 'all'
        }
        
        # Reset tag buttons if they exist
        if hasattr(self, 'tag_frame') and hasattr(self.tag_frame, 'tag_buttons'):
            for btn in self.tag_frame.tag_buttons.values():
                btn.configure(fg_color=self.theme_config['input_bg'],
                            text_color=self.theme_config['text_secondary'])
        
        self.apply_filters()

if __name__ == '__main__':
    app = App()
    app.mainloop()