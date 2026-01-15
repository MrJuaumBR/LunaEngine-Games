import json
import os
import subprocess
import sys
import requests
import zipfile
import shutil
import threading
from pathlib import Path
from tkinter import *
from tkinter import ttk, messagebox, font
from PIL import Image, ImageTk
import webbrowser

class GameLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Game Launcher")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Carregar configurações
        self.config = self.load_config()
        self.theme = self.load_theme(self.config.get('theme', 'dark'))
        
        # Carregar dados dos jogos
        self.data = self.load_data()
        self.games = self.data.get('games', [])
        self.github_base = self.data.get('github_base_url', '')
        
        # Variáveis de estado
        self.downloading = False
        self.download_queue = []
        
        # Setup da interface
        self.setup_ui()
        
        # Verificar jogos instalados
        self.update_games_status()
        
    def load_config(self):
        """Carrega as configurações do usuário"""
        default_config = {
            "theme": "dark",
            "language": "en",
            "download_path": "games",
            "check_updates_on_start": True,
            "github_token": ""
        }
        
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                # Garantir que todas as chaves existam
                for key in default_config:
                    if key not in config:
                        config[key] = default_config[key]
                return config
        except FileNotFoundError:
            # Criar arquivo de configuração padrão
            with open('config.json', 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
    
    def save_config(self):
        """Salva as configurações do usuário"""
        with open('config.json', 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def load_theme(self, theme_name):
        """Carrega o tema selecionado"""
        theme_file = f"assets/{theme_name}_theme.json"
        default_theme = {
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
            "success_color": "#4CAF50"
        }
        
        try:
            with open(theme_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return default_theme
    
    def load_data(self):
        """Carrega os dados dos jogos"""
        try:
            with open('./data.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            messagebox.showerror("Error", "data.json file not found!")
            return {"games": []}
    
    def setup_ui(self):
        """Configura a interface do usuário"""
        # Configurar cores
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
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Refresh", command=self.refresh_games)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Settings menu
        settings_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        
        # Theme submenu
        theme_menu = Menu(settings_menu, tearoff=0)
        settings_menu.add_cascade(label="Theme", menu=theme_menu)
        theme_menu.add_radiobutton(label="Dark", command=lambda: self.change_theme('dark'))
        theme_menu.add_radiobutton(label="Light", command=lambda: self.change_theme('light'))
        
        # Help menu
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="GitHub Repository", command=lambda: webbrowser.open("https://github.com"))
    
    def create_header(self):
        """Cria o cabeçalho"""
        header_frame = Frame(self.root, bg=self.theme['accent_color'], height=100)
        header_frame.pack(fill="x", pady=(0, 10))
        header_frame.pack_propagate(False)
        
        title = Label(
            header_frame,
            text="🎮 Game Library",
            font=("Arial", 28, "bold"),
            bg=self.theme['accent_color'],
            fg=self.theme['text_color']
        )
        title.pack(expand=True)
        
        subtitle = Label(
            header_frame,
            text="Browse and play your favorite games",
            font=("Arial", 12),
            bg=self.theme['accent_color'],
            fg=self.theme['text_color']
        )
        subtitle.pack(expand=True)
    
    def create_main_area(self):
        """Cria a área principal com lista de jogos"""
        main_container = Frame(self.root, bg=self.theme['bg_color'])
        main_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Frame para os cards dos jogos
        self.games_frame = Frame(main_container, bg=self.theme['bg_color'])
        self.games_frame.pack(fill="both", expand=True)
        
        # Container com scrollbar
        self.canvas = Canvas(self.games_frame, bg=self.theme['bg_color'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.games_frame, orient="vertical", command=self.canvas.yview)
        
        self.scrollable_frame = Frame(self.canvas, bg=self.theme['bg_color'])
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Posicionar
        self.canvas.pack(side="left", fill="both", expand=True, padx=(0, 5))
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
        
        self.game_cards = []
        
        for game in self.games:
            card = self.create_game_card(game)
            self.game_cards.append(card)
    
    def create_game_card(self, game):
        """Cria um card individual para o jogo"""
        card_frame = Frame(
            self.scrollable_frame,
            bg=self.theme['card_color'],
            relief="ridge",
            borderwidth=1
        )
        card_frame.pack(fill="x", pady=10, padx=5)
        
        # Conteúdo do card
        content_frame = Frame(card_frame, bg=self.theme['card_color'])
        content_frame.pack(fill="x", padx=15, pady=15)
        
        # Ícone e informações básicas
        info_frame = Frame(content_frame, bg=self.theme['card_color'])
        info_frame.pack(fill="x", pady=(0, 10))
        
        # Status (instalado/não instalado)
        status = "✅ Installed" if os.path.exists(game['path']) else "❌ Not Installed"
        
        # Título e status
        title_frame = Frame(info_frame, bg=self.theme['card_color'])
        title_frame.pack(fill="x")
        
        title = Label(
            title_frame,
            text=game['name'],
            font=("Arial", 18, "bold"),
            bg=self.theme['card_color'],
            fg=self.theme['text_color'],
            anchor="w"
        )
        title.pack(side="left")
        
        status_label = Label(
            title_frame,
            text=status,
            font=("Arial", 10),
            bg=self.theme['card_color'],
            fg=self.theme['success_color'] if "Installed" in status else self.theme['error_color'],
            anchor="w"
        )
        status_label.pack(side="right")
        
        # Descrição
        desc = Label(
            info_frame,
            text=game['description'],
            font=("Arial", 11),
            bg=self.theme['card_color'],
            fg=self.theme['text_color'],
            anchor="w",
            wraplength=700,
            justify="left"
        )
        desc.pack(fill="x", pady=(5, 10))
        
        # Informações adicionais
        meta_frame = Frame(info_frame, bg=self.theme['card_color'])
        meta_frame.pack(fill="x")
        
        version = Label(
            meta_frame,
            text=f"Version: {game['version']}",
            font=("Arial", 9),
            bg=self.theme['card_color'],
            fg=self.theme['highlight_color']
        )
        version.pack(side="left", padx=(0, 15))
        
        # Botões de ação
        button_frame = Frame(content_frame, bg=self.theme['card_color'])
        button_frame.pack(fill="x")
        
        if os.path.exists(game['path']):
            # Jogo instalado - botão Play
            play_btn = Button(
                button_frame,
                text="🎮 Play",
                font=("Arial", 10, "bold"),
                bg=self.theme['button_bg'],
                fg=self.theme['button_fg'],
                padx=20,
                pady=8,
                cursor="hand2",
                command=lambda g=game: self.play_game(g)
            )
            play_btn.pack(side="left", padx=(0, 10))
            
            # Botão para reinstalar/atualizar
            reinstall_btn = Button(
                button_frame,
                text="🔄 Reinstall",
                font=("Arial", 10),
                bg=self.theme['secondary_color'],
                fg=self.theme['text_color'],
                padx=15,
                pady=8,
                cursor="hand2",
                command=lambda g=game: self.install_game(g, force=True)
            )
            reinstall_btn.pack(side="left")
        else:
            # Jogo não instalado - botão Install
            install_btn = Button(
                button_frame,
                text="📥 Install",
                font=("Arial", 10, "bold"),
                bg=self.theme['button_bg'],
                fg=self.theme['button_fg'],
                padx=20,
                pady=8,
                cursor="hand2",
                command=lambda g=game: self.install_game(g)
            )
            install_btn.pack(side="left")
        
        return card_frame
    
    def create_status_bar(self):
        """Cria a barra de status"""
        self.status_bar = Frame(self.root, bg=self.theme['secondary_color'], height=30)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.pack_propagate(False)
        
        self.status_label = Label(
            self.status_bar,
            text="Ready",
            font=("Arial", 9),
            bg=self.theme['secondary_color'],
            fg=self.theme['text_color']
        )
        self.status_label.pack(side="left", padx=10)
        
        # Progress bar para downloads
        self.progress_var = DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.status_bar,
            variable=self.progress_var,
            mode='determinate',
            length=200
        )
        self.progress_bar.pack(side="right", padx=10)
        self.progress_bar.pack_forget()  # Esconder inicialmente
    
    def _on_mousewheel(self, event):
        """Controla o scroll com mouse wheel"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def update_status(self, message, is_error=False):
        """Atualiza a mensagem na barra de status"""
        color = self.theme['error_color'] if is_error else self.theme['text_color']
        self.status_label.config(text=message, fg=color)
        self.root.update_idletasks()
    
    def update_games_status(self):
        """Atualiza o status de todos os jogos"""
        self.create_game_cards()
    
    def refresh_games(self):
        """Atualiza a lista de jogos"""
        self.data = self.load_data()
        self.games = self.data.get('games', [])
        self.update_games_status()
        self.update_status("Game list refreshed")
    
    def change_theme(self, theme_name):
        """Muda o tema da aplicação"""
        self.config['theme'] = theme_name
        self.save_config()
        self.theme = self.load_theme(theme_name)
        
        # Reiniciar a interface
        for widget in self.root.winfo_children():
            widget.destroy()
        self.setup_ui()
    
    def show_about(self):
        """Mostra janela 'About'"""
        about_text = """Game Launcher v1.0

A simple launcher for downloading and playing games from GitHub.

Features:
• Download games directly from GitHub
• Light and dark themes
• Automatic dependency installation
• Game library management

Created with Python and Tkinter"""
        
        messagebox.showinfo("About Game Launcher", about_text)
    
    def install_game(self, game, force=False):
        """Instala um jogo do GitHub"""
        if not force and os.path.exists(game['path']):
            response = messagebox.askyesno(
                "Game Already Installed",
                f"{game['name']} is already installed.\n\n"
                "Do you want to reinstall it?\n"
                "(Existing files will be overwritten)"
            )
            if not response:
                return
        
        # Confirmar instalação
        confirm_msg = f"Install {game['name']} v{game['version']}?\n\n" + \
                     f"Description: {game['description']}\n\n" + \
                     "The game will be downloaded from GitHub."
        
        if not messagebox.askyesno("Confirm Installation", confirm_msg):
            return
        
        # Iniciar download em thread separada
        thread = threading.Thread(target=self.download_game_thread, args=(game,))
        thread.daemon = True
        thread.start()
    
    def download_game_thread(self, game):
        """Thread para download do jogo"""
        self.downloading = True
        self.show_progress_bar()
        
        try:
            # URL do arquivo no GitHub
            download_url = f"{self.github_base}/{game['github_path']}"
            
            self.update_status(f"Downloading {game['name']}...")
            
            # Criar pasta temporária
            temp_dir = Path("temp_download")
            temp_dir.mkdir(exist_ok=True)
            
            # Nome do arquivo ZIP
            zip_filename = temp_dir / f"{game['name'].replace(' ', '_')}.zip"
            
            # Download com progresso
            response = requests.get(download_url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            
            if total_size == 0:
                raise Exception("Could not determine file size")
            
            downloaded = 0
            with open(zip_filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress = (downloaded / total_size) * 100
                        self.progress_var.set(progress)
            
            self.update_status(f"Extracting {game['name']}...")
            
            # Extrair arquivo
            extract_path = Path(game['path']).parent
            extract_path.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            # Limpar arquivos temporários
            shutil.rmtree(temp_dir)
            
            # Instalar dependências
            if 'requirements' in game and game['requirements']:
                self.update_status(f"Installing dependencies for {game['name']}...")
                for req in game['requirements']:
                    subprocess.run([sys.executable, "-m", "pip", "install", req], 
                                 capture_output=True, text=True)
            
            self.update_status(f"{game['name']} installed successfully!", is_error=False)
            messagebox.showinfo("Installation Complete", 
                              f"{game['name']} has been successfully installed!\n\n"
                              f"You can now play the game.")
            
            # Atualizar interface
            self.root.after(0, self.update_games_status)
            
        except Exception as e:
            self.update_status(f"Error installing {game['name']}: {str(e)}", is_error=True)
            messagebox.showerror("Installation Error", 
                               f"Failed to install {game['name']}:\n{str(e)}")
        
        finally:
            self.downloading = False
            self.hide_progress_bar()
    
    def show_progress_bar(self):
        """Mostra a barra de progresso"""
        self.progress_var.set(0)
        self.progress_bar.pack(side="right", padx=10)
    
    def hide_progress_bar(self):
        """Esconde a barra de progresso"""
        self.progress_bar.pack_forget()
    
    def play_game(self, game):
        """Executa um jogo"""
        try:
            game_path = game['path']
            
            if not os.path.exists(game_path):
                messagebox.showerror("Error", 
                                   f"Game file not found:\n{game_path}\n\n"
                                   "Try reinstalling the game.")
                return
            
            self.update_status(f"Launching {game['name']}...")
            
            # Determinar como executar
            if game_path.endswith('.py'):
                # Executar script Python
                subprocess.Popen([sys.executable, game_path], 
                               creationflags=subprocess.CREATE_NEW_CONSOLE 
                               if sys.platform == "win32" else 0)
            elif game_path.endswith('.exe'):
                # Executar executável
                subprocess.Popen([game_path])
            else:
                # Tentar abrir com programa padrão
                if sys.platform == "win32":
                    os.startfile(game_path)
                else:
                    subprocess.Popen(['xdg-open', game_path])
            
            self.update_status(f"{game['name']} launched")
            
        except Exception as e:
            self.update_status(f"Error launching {game['name']}: {str(e)}", is_error=True)
            messagebox.showerror("Launch Error", 
                               f"Could not launch {game['name']}:\n{str(e)}")

def main():
    root = Tk()
    
    # Configurações iniciais da janela
    root.title("Game Launcher")
    root.geometry("900x700")
    
    # Verificar dependências
    try:
        import requests
        from PIL import Image
    except ImportError:
        print("Installing required packages...")
        subprocess.run([sys.executable, "-m", "pip", "install", "requests", "pillow"])
    
    # Iniciar aplicação
    app = GameLauncher(root)
    
    # Centralizar janela
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()