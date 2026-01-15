#!/usr/bin/env python3
"""
Game Launcher for LunaEngine Games
Supports both GitHub and local modes
"""

import json
import os
import sys
import subprocess
import argparse
import webbrowser
from pathlib import Path
from tkinter import *
from tkinter import ttk, messagebox, font
import requests

# Adicionar o diretório atual ao path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class GameLauncher:
    def __init__(self, root, mode='local'):
        self.root = root
        self.mode = mode  # 'github' ou 'local'
        self.root.title(f"LunaEngine Games Launcher [{mode.capitalize()} Mode]")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Determinar caminhos base
        self.base_dir = Path(__file__).parent.parent  # Pasta LunaEngine-Games
        self.launcher_dir = Path(__file__).parent      # Pasta Launcher
        self.games_dir = self.base_dir / "games"       # Pasta games
        
        # Carregar configurações
        self.config = self.load_config()
        self.theme = self.load_theme(self.config.get('theme', 'dark'))
        
        # Carregar dados dos jogos
        self.data = self.load_data()
        self.games = self.data.get('games', [])
        
        # URLs do GitHub
        if self.mode == 'github':
            self.github_raw_url = "https://github.com/MrJuaumBR/LunaEngine-Games/raw/main"
            self.github_api_url = "https://api.github.com/repos/MrJuaumBR/LunaEngine-Games/contents"
        
        # Setup da interface
        self.setup_ui()
        
        # Verificar jogos instalados
        self.update_games_status()
        
        # Centralizar janela
        self.center_window()
    
    def center_window(self):
        """Centraliza a janela na tela"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def load_config(self):
        """Carrega as configurações do usuário"""
        config_path = self.launcher_dir / "config.json"
        default_config = {
            "theme": "dark",
            "language": "en",
            "auto_update": False,
            "last_mode": "local"
        }
        
        try:
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    # Garantir que todas as chaves existam
                    for key in default_config:
                        if key not in config:
                            config[key] = default_config[key]
                    return config
        except Exception as e:
            print(f"Error loading config: {e}")
        
        # Criar configuração padrão
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config
    
    def save_config(self):
        """Salva as configurações do usuário"""
        config_path = self.launcher_dir / "config.json"
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def load_theme(self, theme_name):
        """Carrega o tema selecionado"""
        theme_file = self.launcher_dir / "assets" / f"{theme_name}_theme.json"
        
        # Tema escuro padrão
        default_dark_theme = {
            "name": "dark",
            "bg_color": "#1a1a2e",
            "card_color": "#16213e",
            "text_color": "#e6e6e6",
            "accent_color": "#0f3460",
            "button_bg": "#4CAF50",
            "button_fg": "white",
            "secondary_color": "#2d4059",
            "highlight_color": "#00adb5",
            "error_color": "#ff6b6b",
            "success_color": "#4CAF50",
            "warning_color": "#ffa726",
            "border_color": "#30475e"
        }
        
        # Tema claro
        default_light_theme = {
            "name": "light",
            "bg_color": "#f5f7fa",
            "card_color": "#ffffff",
            "text_color": "#2d4059",
            "accent_color": "#3498db",
            "button_bg": "#3498db",
            "button_fg": "white",
            "secondary_color": "#ecf0f1",
            "highlight_color": "#e74c3c",
            "error_color": "#e74c3c",
            "success_color": "#2ecc71",
            "warning_color": "#f39c12",
            "border_color": "#bdc3c7"
        }
        
        try:
            if theme_file.exists():
                with open(theme_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        
        # Retornar tema padrão baseado no nome
        if theme_name == "light":
            return default_light_theme
        return default_dark_theme
    
    def load_data(self):
        """Carrega os dados dos jogos baseado no modo"""
        if self.mode == 'local':
            # Modo local: carregar do arquivo data.json na pasta games
            data_path = self.games_dir / "data.json"
            if data_path.exists():
                try:
                    with open(data_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Corrigir paths para serem absolutos
                        for game in data.get('games', []):
                            if 'path' in game:
                                # Converter path relativo para absoluto
                                game['full_path'] = str(self.games_dir / game['path'])
                        return data
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to load data.json: {e}")
            else:
                messagebox.showwarning("Warning", 
                    f"data.json not found in {self.games_dir}\n"
                    "Running in local mode with auto-detected games.")
                return self.scan_local_games()
        else:
            # Modo GitHub: tentar baixar data.json
            try:
                response = requests.get(f"{self.github_raw_url}/games/data.json", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    # Adicionar URLs para download
                    for game in data.get('games', []):
                        game['download_url'] = f"{self.github_raw_url}/games/{game['path'].replace('main.py', '')}"
                    return data
                else:
                    messagebox.showerror("Error", 
                        f"Failed to fetch data from GitHub\nStatus: {response.status_code}")
            except Exception as e:
                messagebox.showerror("Error", f"Network error: {e}")
        
        return {"games": []}
    
    def scan_local_games(self):
        """Escaneia a pasta local de jogos"""
        games = []
        
        if not self.games_dir.exists():
            self.games_dir.mkdir(parents=True)
            return {"games": []}
        
        # Procurar por pastas de jogos
        for item in self.games_dir.iterdir():
            if item.is_dir():
                # Ignorar pastas que não são jogos
                if item.name.startswith('.') or item.name == '__pycache__':
                    continue
                
                # Procurar por main.py
                main_file = item / "main.py"
                if not main_file.exists():
                    # Procurar por qualquer arquivo .py
                    py_files = list(item.glob("*.py"))
                    if py_files:
                        main_file = py_files[0]
                    else:
                        continue
                
                # Criar entrada do jogo
                game_data = {
                    "name": item.name.replace('_', ' ').title(),
                    "path": f"{item.name}/{main_file.name}",
                    "full_path": str(main_file),
                    "version": "1.0.0",
                    "description": f"A game located in {item.name} folder",
                    "icon": "",
                    "requirements": []
                }
                
                # Verificar se existe requirements.txt
                req_file = item / "requirements.txt"
                if req_file.exists():
                    try:
                        with open(req_file, 'r') as f:
                            game_data["requirements"] = [line.strip() for line in f if line.strip()]
                    except:
                        pass
                
                games.append(game_data)
        
        return {"games": games}
    
    def setup_ui(self):
        """Configura a interface do usuário"""
        self.root.configure(bg=self.theme['bg_color'])
        
        # Criar menu
        self.create_menu()
        
        # Cabeçalho
        self.create_header()
        
        # Área principal
        self.create_main_area()
        
        # Barra de status
        self.create_status_bar()
    
    def create_menu(self):
        """Cria a barra de menu"""
        menubar = Menu(self.root, bg=self.theme['secondary_color'], fg=self.theme['text_color'])
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = Menu(menubar, tearoff=0, bg=self.theme['card_color'], fg=self.theme['text_color'])
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Refresh Games", command=self.refresh_games)
        
        if self.mode == 'github':
            file_menu.add_command(label="Switch to Local Mode", 
                                command=self.switch_to_local_mode)
        else:
            file_menu.add_command(label="Switch to GitHub Mode", 
                                command=self.switch_to_github_mode)
        
        file_menu.add_separator()
        file_menu.add_command(label="Open Games Folder", command=self.open_games_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Settings menu
        settings_menu = Menu(menubar, tearoff=0, bg=self.theme['card_color'], fg=self.theme['text_color'])
        menubar.add_cascade(label="Settings", menu=settings_menu)
        
        # Theme submenu
        theme_menu = Menu(settings_menu, tearoff=0, bg=self.theme['card_color'], fg=self.theme['text_color'])
        settings_menu.add_cascade(label="Theme", menu=theme_menu)
        theme_menu.add_radiobutton(label="Dark Theme", 
                                  command=lambda: self.change_theme('dark'),
                                  variable=StringVar(value=self.config['theme']),
                                  value='dark')
        theme_menu.add_radiobutton(label="Light Theme", 
                                  command=lambda: self.change_theme('light'),
                                  variable=StringVar(value=self.config['theme']),
                                  value='light')
        
        # Help menu
        help_menu = Menu(menubar, tearoff=0, bg=self.theme['card_color'], fg=self.theme['text_color'])
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="View on GitHub", 
                            command=lambda: webbrowser.open("https://github.com/MrJuaumBR/LunaEngine-Games"))
    
    def create_header(self):
        """Cria o cabeçalho"""
        header_frame = Frame(self.root, bg=self.theme['accent_color'], height=100)
        header_frame.pack(fill="x", pady=(0, 10))
        header_frame.pack_propagate(False)
        
        # Título com ícone do modo
        mode_icon = "💻" if self.mode == 'local' else "🌐"
        title_text = f"{mode_icon} LunaEngine Games Launcher"
        
        title = Label(
            header_frame,
            text=title_text,
            font=("Arial", 24, "bold"),
            bg=self.theme['accent_color'],
            fg=self.theme['text_color']
        )
        title.pack(expand=True, pady=(20, 5))
        
        # Subtítulo
        if self.mode == 'local':
            subtitle_text = "Playing games from local folder"
        else:
            subtitle_text = "Downloading and playing games from GitHub"
        
        subtitle = Label(
            header_frame,
            text=subtitle_text,
            font=("Arial", 11),
            bg=self.theme['accent_color'],
            fg=self.theme['text_color']
        )
        subtitle.pack(expand=True)
    
    def create_main_area(self):
        """Cria a área principal com lista de jogos"""
        main_container = Frame(self.root, bg=self.theme['bg_color'])
        main_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Container com scrollbar
        canvas_frame = Frame(main_container, bg=self.theme['bg_color'])
        canvas_frame.pack(fill="both", expand=True)
        
        self.canvas = Canvas(canvas_frame, bg=self.theme['bg_color'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        
        self.scrollable_frame = Frame(self.canvas, bg=self.theme['bg_color'])
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Criar cards dos jogos
        self.create_game_cards()
    
    def create_game_cards(self):
        """Cria cards para cada jogo"""
        # Limpar frame anterior
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        if not self.games:
            # Mostrar mensagem quando não há jogos
            no_games_frame = Frame(self.scrollable_frame, bg=self.theme['bg_color'])
            no_games_frame.pack(fill="both", expand=True, pady=100)
            
            if self.mode == 'local':
                message = "No games found.\n\nPlace game folders in the 'games' directory."
            else:
                message = "No games available.\n\nCheck your internet connection or try local mode."
            
            no_games_label = Label(
                no_games_frame,
                text=message,
                font=("Arial", 14),
                bg=self.theme['bg_color'],
                fg=self.theme['text_color'],
                justify="center"
            )
            no_games_label.pack(expand=True)
            return
        
        # Criar cards para cada jogo
        for game in self.games:
            self.create_game_card(game)
    
    def create_game_card(self, game):
        """Cria um card individual para o jogo"""
        # Verificar se o jogo existe
        if self.mode == 'local':
            game_exists = os.path.exists(game.get('full_path', ''))
        else:
            game_exists = False  # No GitHub mode, games need to be downloaded first
        
        card_frame = Frame(
            self.scrollable_frame,
            bg=self.theme['card_color'],
            relief="solid",
            borderwidth=1,
            highlightbackground=self.theme['border_color']
        )
        card_frame.pack(fill="x", pady=8, padx=5)
        
        content_frame = Frame(card_frame, bg=self.theme['card_color'])
        content_frame.pack(fill="x", padx=15, pady=12)
        
        # Linha superior: Nome e Status
        top_frame = Frame(content_frame, bg=self.theme['card_color'])
        top_frame.pack(fill="x", pady=(0, 8))
        
        # Nome do jogo
        name_label = Label(
            top_frame,
            text=game['name'],
            font=("Arial", 16, "bold"),
            bg=self.theme['card_color'],
            fg=self.theme['text_color'],
            anchor="w"
        )
        name_label.pack(side="left")
        
        # Status
        if self.mode == 'local':
            if game_exists:
                status_text = "✅ Installed"
                status_color = self.theme['success_color']
            else:
                status_text = "❌ Missing"
                status_color = self.theme['error_color']
        else:
            status_text = "🌐 Available Online"
            status_color = self.theme['highlight_color']
        
        status_label = Label(
            top_frame,
            text=status_text,
            font=("Arial", 10, "bold"),
            bg=self.theme['card_color'],
            fg=status_color
        )
        status_label.pack(side="right")
        
        # Descrição
        desc_label = Label(
            content_frame,
            text=game['description'],
            font=("Arial", 11),
            bg=self.theme['card_color'],
            fg=self.theme['text_color'],
            anchor="w",
            wraplength=650,
            justify="left"
        )
        desc_label.pack(fill="x", pady=(0, 10))
        
        # Linha inferior: Informações e botões
        bottom_frame = Frame(content_frame, bg=self.theme['card_color'])
        bottom_frame.pack(fill="x")
        
        # Informações
        info_frame = Frame(bottom_frame, bg=self.theme['card_color'])
        info_frame.pack(side="left", fill="y")
        
        version_label = Label(
            info_frame,
            text=f"Version: {game.get('version', '1.0.0')}",
            font=("Arial", 9),
            bg=self.theme['card_color'],
            fg=self.theme['highlight_color']
        )
        version_label.pack(anchor="w")
        
        # Botões
        button_frame = Frame(bottom_frame, bg=self.theme['card_color'])
        button_frame.pack(side="right")
        
        if self.mode == 'local':
            if game_exists:
                # Botão para jogar
                play_btn = Button(
                    button_frame,
                    text="🎮 Play",
                    font=("Arial", 10, "bold"),
                    bg=self.theme['button_bg'],
                    fg=self.theme['button_fg'],
                    padx=20,
                    pady=6,
                    cursor="hand2",
                    command=lambda g=game: self.play_game(g)
                )
                play_btn.pack(side="left", padx=(5, 0))
                
                # Botão para abrir pasta
                folder_btn = Button(
                    button_frame,
                    text="📁 Open Folder",
                    font=("Arial", 10),
                    bg=self.theme['secondary_color'],
                    fg=self.theme['text_color'],
                    padx=15,
                    pady=6,
                    cursor="hand2",
                    command=lambda g=game: self.open_game_folder(g)
                )
                folder_btn.pack(side="left", padx=(5, 0))
            else:
                # Botão para ver detalhes
                details_btn = Button(
                    button_frame,
                    text="ℹ️ Details",
                    font=("Arial", 10),
                    bg=self.theme['secondary_color'],
                    fg=self.theme['text_color'],
                    padx=20,
                    pady=6,
                    cursor="hand2",
                    command=lambda g=game: self.show_game_details(g)
                )
                details_btn.pack(side="left")
        else:
            # Modo GitHub
            if game_exists:
                # Botão para jogar (se já estiver instalado)
                play_btn = Button(
                    button_frame,
                    text="🎮 Play",
                    font=("Arial", 10, "bold"),
                    bg=self.theme['button_bg'],
                    fg=self.theme['button_fg'],
                    padx=20,
                    pady=6,
                    cursor="hand2",
                    command=lambda g=game: self.play_game(g)
                )
                play_btn.pack(side="left", padx=(5, 0))
            else:
                # Botão para instalar
                install_btn = Button(
                    button_frame,
                    text="📥 Install",
                    font=("Arial", 10, "bold"),
                    bg=self.theme['button_bg'],
                    fg=self.theme['button_fg'],
                    padx=20,
                    pady=6,
                    cursor="hand2",
                    command=lambda g=game: self.install_game(g)
                )
                install_btn.pack(side="left", padx=(5, 0))
    
    def create_status_bar(self):
        """Cria a barra de status"""
        self.status_bar = Frame(self.root, bg=self.theme['secondary_color'], height=30)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.pack_propagate(False)
        
        self.status_label = Label(
            self.status_bar,
            text=f"Ready - {len(self.games)} games found | Mode: {self.mode.capitalize()}",
            font=("Arial", 9),
            bg=self.theme['secondary_color'],
            fg=self.theme['text_color']
        )
        self.status_label.pack(side="left", padx=10)
        
        # Ícone do modo
        mode_icon = "💻" if self.mode == 'local' else "🌐"
        mode_label = Label(
            self.status_bar,
            text=mode_icon,
            font=("Arial", 12),
            bg=self.theme['secondary_color'],
            fg=self.theme['text_color']
        )
        mode_label.pack(side="right", padx=10)
    
    def _on_mousewheel(self, event):
        """Controla o scroll com mouse wheel"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def refresh_games(self):
        """Atualiza a lista de jogos"""
        self.data = self.load_data()
        self.games = self.data.get('games', [])
        self.create_game_cards()
        self.status_label.config(
            text=f"Refreshed - {len(self.games)} games found | Mode: {self.mode.capitalize()}"
        )
    
    def change_theme(self, theme_name):
        """Muda o tema da aplicação"""
        self.config['theme'] = theme_name
        self.save_config()
        self.theme = self.load_theme(theme_name)
        
        # Recriar toda a interface
        for widget in self.root.winfo_children():
            widget.destroy()
        self.setup_ui()
    
    def show_about(self):
        """Mostra janela 'About'"""
        about_text = """LunaEngine Games Launcher v1.0

A game launcher for LunaEngine games collection.

Features:
• Play games locally from the games/ folder
• Download games from GitHub (GitHub mode)
• Light and dark themes
• Simple and intuitive interface

GitHub: https://github.com/MrJuaumBR/LunaEngine-Games

Usage:
  python launcher.py              # Local mode
  python launcher.py --github     # GitHub mode"""
        
        messagebox.showinfo("About LunaEngine Games Launcher", about_text)
    
    def play_game(self, game):
        """Executa um jogo"""
        try:
            game_path = game.get('full_path') or game.get('path')
            
            if not game_path or not os.path.exists(game_path):
                messagebox.showerror("Error", 
                                   f"Game file not found:\n{game_path}")
                return
            
            self.status_label.config(text=f"Launching {game['name']}...")
            
            # Determinar como executar
            if game_path.endswith('.py'):
                # Executar script Python
                if sys.platform == "win32":
                    subprocess.Popen(['python', game_path], 
                                   creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:
                    subprocess.Popen(['python3', game_path])
            else:
                # Tentar abrir com programa padrão
                if sys.platform == "win32":
                    os.startfile(game_path)
                else:
                    subprocess.Popen(['xdg-open', game_path])
            
            self.status_label.config(text=f"Launched {game['name']}")
            
        except Exception as e:
            self.status_label.config(text=f"Error launching {game['name']}")
            messagebox.showerror("Launch Error", 
                               f"Could not launch {game['name']}:\n{str(e)}")
    
    def open_game_folder(self, game):
        """Abre a pasta do jogo"""
        try:
            game_folder = Path(game.get('full_path', '')).parent
            if game_folder.exists():
                if sys.platform == "win32":
                    os.startfile(game_folder)
                elif sys.platform == "darwin":
                    subprocess.Popen(['open', str(game_folder)])
                else:
                    subprocess.Popen(['xdg-open', str(game_folder)])
            else:
                messagebox.showerror("Error", "Game folder not found")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder:\n{str(e)}")
    
    def open_games_folder(self):
        """Abre a pasta games/"""
        try:
            if self.games_dir.exists():
                if sys.platform == "win32":
                    os.startfile(self.games_dir)
                elif sys.platform == "darwin":
                    subprocess.Popen(['open', str(self.games_dir)])
                else:
                    subprocess.Popen(['xdg-open', str(self.games_dir)])
            else:
                messagebox.showwarning("Warning", 
                    f"Games folder not found at:\n{self.games_dir}\n"
                    "Creating empty folder...")
                self.games_dir.mkdir(parents=True)
                if sys.platform == "win32":
                    os.startfile(self.games_dir)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open games folder:\n{str(e)}")
    
    def show_game_details(self, game):
        """Mostra detalhes do jogo"""
        details = f"""Game: {game['name']}
Version: {game.get('version', '1.0.0')}
Description: {game['description']}
Path: {game.get('path', 'Unknown')}
Requirements: {', '.join(game.get('requirements', [])) or 'None'}

Status: {'Available' if os.path.exists(game.get('full_path', '')) else 'Not installed'}"""
        
        messagebox.showinfo(f"Game Details - {game['name']}", details)
    
    def install_game(self, game):
        """Instala um jogo do GitHub (modo GitHub)"""
        if self.mode != 'github':
            return
        
        messagebox.showinfo("Coming Soon", 
            "GitHub download feature coming soon!\n\n"
            "For now, please:\n"
            "1. Switch to local mode\n"
            "2. Place game folders in the 'games' directory\n"
            "3. Run in local mode")
    
    def switch_to_local_mode(self):
        """Muda para o modo local"""
        self.config['last_mode'] = 'local'
        self.save_config()
        messagebox.showinfo("Switch Mode", 
            "Switching to Local Mode.\n\n"
            "Please restart the launcher.")
        self.root.quit()
    
    def switch_to_github_mode(self):
        """Muda para o modo GitHub"""
        self.config['last_mode'] = 'github'
        self.save_config()
        messagebox.showinfo("Switch Mode", 
            "Switching to GitHub Mode.\n\n"
            "Please restart the launcher.")
        self.root.quit()
    
    def update_games_status(self):
        """Atualiza o status dos jogos"""
        # Esta função é chamada após criar a interface
        pass


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='LunaEngine Games Launcher')
    parser.add_argument('--github', action='store_true', 
                       help='Run in GitHub mode (download from GitHub)')
    parser.add_argument('--local', action='store_true', 
                       help='Run in local mode (use local games folder)')
    
    args = parser.parse_args()
    
    # Determinar modo
    if args.github:
        mode = 'github'
    elif args.local:
        mode = 'local'
    else:
        # Modo padrão: local
        mode = 'local'
    
    # Criar e executar aplicação
    root = Tk()
    app = GameLauncher(root, mode)
    root.mainloop()


if __name__ == "__main__":
    main()