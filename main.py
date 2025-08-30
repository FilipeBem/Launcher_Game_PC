import sys
import os
import json
import requests
import base64
import random
import pygame
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QFileDialog, QListWidget, QListWidgetItem, QMessageBox, QInputDialog, QComboBox
)
from PyQt5.QtGui import QPixmap, QIcon, QPalette, QBrush

SAVE_FILE = "jogos.json"
CAPA_DIR = "capas"
BACKGROUND_DEFAULT = "background.jpg"
BACKGROUND_LUA = "lua.jpg"
BACKGROUND_PASTO = "pasto.jpg"

if not os.path.exists(CAPA_DIR):
    os.makedirs(CAPA_DIR)

class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Meu Launcher de Jogos")
        self.setGeometry(100, 100, 1000, 600)

        # ===== Layout principal =====
        main_layout = QHBoxLayout(self)

        # Barra lateral
        self.sidebar_index = 0
        self.sidebar_buttons = []

        sidebar = QVBoxLayout()
        sidebar.setSpacing(5)
        sidebar.setContentsMargins(5, 5, 5, 5)

        # Steam
        self.steam_btn = QPushButton()
        self.steam_btn.setIcon(QIcon("icons/steam.png"))
        self.steam_btn.setIconSize(QSize(127, 127))
        self.steam_btn.setFixedSize(100, 100)
        self.steam_btn.clicked.connect(lambda: self.abrir_programa("C:/Program Files (x86)/Steam/steam.exe"))
        sidebar.addWidget(self.steam_btn)
        self.sidebar_buttons.append(self.steam_btn)

        # Epic
        self.epic_btn = QPushButton()
        self.epic_btn.setIcon(QIcon("icons/epic.png"))
        self.epic_btn.setIconSize(QSize(95, 95))
        self.epic_btn.setFixedSize(100, 100)
        self.epic_btn.clicked.connect(lambda: self.abrir_programa("C:/Program Files (x86)/Epic Games/Launcher/Portal/Binaries/Win32/EpicGamesLauncher.exe"))
        sidebar.addWidget(self.epic_btn)
        self.sidebar_buttons.append(self.epic_btn)

        # Incluir Jogo
        self.add_game_btn = QPushButton("Incluir Jogo")
        self.add_game_btn.clicked.connect(self.adicionar_jogo)
        sidebar.addWidget(self.add_game_btn)
        self.sidebar_buttons.append(self.add_game_btn)

        # Remover Jogo
        self.remove_game_btn = QPushButton("Remover Jogo")
        self.remove_game_btn.clicked.connect(self.remover_jogo)
        sidebar.addWidget(self.remove_game_btn)
        self.sidebar_buttons.append(self.remove_game_btn)

        # Temas
        self.temas_btn = QPushButton("Temas")
        self.temas_btn.clicked.connect(self.abrir_temas)
        sidebar.addWidget(self.temas_btn)
        self.sidebar_buttons.append(self.temas_btn)

        main_layout.addLayout(sidebar)

        # Lista de jogos
        self.games_list = QListWidget()
        self.games_list.itemClicked.connect(self.selecionar_jogo)
        self.games_list.setStyleSheet("""
        QListWidget {
            background-color: rgba(0, 50, 150, 0.4);
            color: white;
            border-radius: 10px;
            font-size: 18px;
            padding: 5px;
        }
        QListWidget::item:selected {
            background-color: rgba(0, 150, 255, 0.5);
            color: yellow;
            font-weight: bold;
        }
        """)
        main_layout.addWidget(self.games_list, 2)

        # Área da capa e botões de ação
        fundo_layout = QVBoxLayout()
        self.fundo = QLabel()
        self.fundo.setAlignment(Qt.AlignCenter)
        self.fundo.setStyleSheet("background-color: rgba(0, 50, 150, 0.3); border-radius: 10px;")
        fundo_layout.addWidget(self.fundo)

        self.play_button = QPushButton("Jogar")
        self.play_button.clicked.connect(self.jogar)
        fundo_layout.addWidget(self.play_button)

        self.capa_button = QPushButton("Alterar Capa")
        self.capa_button.clicked.connect(self.alterar_capa)
        fundo_layout.addWidget(self.capa_button)

        main_layout.addLayout(fundo_layout, 4)

        # ===== Dados =====
        self.jogos = self.carregar_jogos()
        self.atualizar_lista()

        # ===== Estilo dos botões =====
        self.tema_atual = "azul"
        self.estilizar_botoes()

        # ===== Background =====
        self.set_background_image()

        # ===== Controle =====
        pygame.init()
        pygame.joystick.init()
        self.joystick = None
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()

        self.timer = QTimer()
        self.timer.timeout.connect(self.ler_joystick)
        self.timer.start(100)

        # ===== Trilha sonora =====
        pygame.mixer.init()
        self.musicas = [
            os.path.join("musicas", "Maroon 5 - Lucky Strike Lyrics Video (Overexposed).mp3"),
            os.path.join("musicas", "shell_shocked_assassin_s_creed_gmv_aac_78023.mp3"),
            os.path.join("musicas", "tubidy_aac_80693.mp3")
        ]
        self.trilha_sonora()
        self.timer_trilha = QTimer()
        self.timer_trilha.timeout.connect(self.verificar_musica)
        self.timer_trilha.start(100)
        pygame.mixer.music.set_volume(0.1)  # volume inicial

    # ===== Função de temas =====
    def abrir_temas(self):
        tema, ok = QInputDialog.getItem(self, "Escolher Tema", "Selecione o tema:", ["Azul", "Lua", "Pasto"], 0, False)
        if ok:
            self.tema_atual = tema.lower()
            self.estilizar_botoes()
            self.set_background_image()

    def estilizar_botoes(self):
        if self.tema_atual == "azul":
            cor_bg = "rgba(0, 50, 150, 0.4)"
            cor_hover = "rgba(0, 150, 255, 0.5)"
        elif self.tema_atual == "lua":
            cor_bg = "rgba(30, 30, 30, 0.7)"
            cor_hover = "rgba(80, 80, 80, 0.8)"
        elif self.tema_atual == "pasto":
            cor_bg = "rgba(50, 100, 50, 0.5)"
            cor_hover = "rgba(100, 200, 100, 0.7)"
        else:
            cor_bg = "rgba(0, 50, 150, 0.4)"
            cor_hover = "rgba(0, 150, 255, 0.5)"

        botao_style = f"""
        QPushButton {{
            background-color: {cor_bg};
            color: white;
            border-radius: 10px;
            font-size: 16px;
            padding: 8px;
        }}
        QPushButton:hover {{
            background-color: {cor_hover};
            color: yellow;
        }}
        """
        for btn in self.sidebar_buttons + [self.play_button, self.capa_button]:
            btn.setStyleSheet(botao_style)

    def set_background_image(self):
        if self.tema_atual == "azul":
            img = BACKGROUND_DEFAULT
        elif self.tema_atual == "lua":
            img = BACKGROUND_LUA
        elif self.tema_atual == "pasto":
            img = BACKGROUND_PASTO
        else:
            img = BACKGROUND_DEFAULT

        if os.path.exists(img):
            palette = QPalette()
            bg = QPixmap(img).scaled(self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            palette.setBrush(QPalette.Window, QBrush(bg))
            self.setPalette(palette)
            self.setAutoFillBackground(True)

    # ===== Outras funções do launcher =====
    def abrir_programa(self, caminho):
        os.system(f'start "" "{caminho}"')

    def carregar_jogos(self):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r") as f:
                return json.load(f)
        return []

    def salvar_jogos(self):
        with open(SAVE_FILE, "w") as f:
            json.dump(self.jogos, f, indent=4)

    def atualizar_lista(self):
        self.games_list.clear()
        for jogo in self.jogos:
            item = QListWidgetItem(jogo["nome"])
            item.setData(Qt.UserRole, jogo)
            self.games_list.addItem(item)

    def adicionar_jogo(self):
        caminho, _ = QFileDialog.getOpenFileName(self, "Selecione o executável do jogo", "", "Executáveis (*.exe)")
        if caminho:
            nome = os.path.basename(caminho).replace(".exe", "")
            jogo = {"nome": nome, "caminho": caminho, "capa": None}
            self.jogos.append(jogo)
            self.salvar_jogos()
            self.atualizar_lista()
            self.games_list.setCurrentRow(self.games_list.count() - 1)
            self.selecionar_jogo(self.games_list.currentItem())

    def remover_jogo(self):
        item = self.games_list.currentItem()
        if item:
            jogo = item.data(Qt.UserRole)
            resposta = QMessageBox.question(self, "Remover Jogo", f"Remover {jogo['nome']}?")
            if resposta == QMessageBox.Yes:
                self.jogos.remove(jogo)
                self.salvar_jogos()
                self.atualizar_lista()
                self.fundo.clear()

    def selecionar_jogo(self, item):
        jogo = item.data(Qt.UserRole)
        self.jogo_selecionado = jogo
        self.redimensionar_capa()

    def redimensionar_capa(self):
        if hasattr(self, "jogo_selecionado") and self.jogo_selecionado.get("capa") and os.path.exists(self.jogo_selecionado["capa"]):
            pixmap = QPixmap(self.jogo_selecionado["capa"]).scaled(
                self.fundo.width(), self.fundo.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.fundo.setPixmap(pixmap)
        elif hasattr(self, "jogo_selecionado"):
            self.fundo.setText(self.jogo_selecionado["nome"])

    def alterar_capa(self):
        if hasattr(self, "jogo_selecionado"):
            resposta = QMessageBox.question(
                self,
                "Alterar Capa",
                "Deseja escolher a capa via arquivo local (Sim) ou link/Base64 da internet (Não)?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            caminho_imagem = None
            if resposta == QMessageBox.Yes:
                caminho_imagem, _ = QFileDialog.getOpenFileName(
                    self, "Selecione a capa do jogo", "", "Imagens (*.png *.jpg *.jpeg)"
                )
            else:
                url, ok = QInputDialog.getText(self, "Capa do Jogo", "Digite a URL ou cole Base64:")
                if ok and url:
                    try:
                        if url.startswith("data:image"):
                            header, encoded = url.split(",", 1)
                            extensao = header.split("/")[1].split(";")[0]
                            caminho_imagem = os.path.join(CAPA_DIR, f"{self.jogo_selecionado['nome']}.{extensao}")
                            with open(caminho_imagem, "wb") as f:
                                f.write(base64.b64decode(encoded))
                        else:
                            response = requests.get(url)
                            if response.status_code == 200:
                                extensao = os.path.splitext(url)[1] or ".png"
                                caminho_imagem = os.path.join(CAPA_DIR, f"{self.jogo_selecionado['nome']}{extensao}")
                                with open(caminho_imagem, "wb") as f:
                                    f.write(response.content)
                            else:
                                QMessageBox.warning(self, "Erro", "Não foi possível baixar a imagem.")
                    except Exception as e:
                        QMessageBox.warning(self, "Erro", f"Ocorreu um erro: {e}")

            if caminho_imagem:
                self.jogo_selecionado["capa"] = caminho_imagem
                self.salvar_jogos()
                self.redimensionar_capa()

    def jogar(self):
        if hasattr(self, "jogo_selecionado"):
            os.startfile(self.jogo_selecionado["caminho"])

    # ===== Teclado =====
    def keyPressEvent(self, event):
        row = self.games_list.currentRow()
        if event.key() == Qt.Key_Up and row > 0:
            self.games_list.setCurrentRow(row - 1)
            self.selecionar_jogo(self.games_list.currentItem())
        elif event.key() == Qt.Key_Down and row < self.games_list.count() - 1:
            self.games_list.setCurrentRow(row + 1)
            self.selecionar_jogo(self.games_list.currentItem())
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.jogar()
        elif event.key() == Qt.Key_Escape:
            self.close()

    # ===== Controle =====
    def ler_joystick(self):
        if not self.joystick:
            return
        pygame.event.pump()
        hat = self.joystick.get_hat(0)
        if hat == (0, 1):
            self.navegar_lista(-1)
        elif hat == (0, -1):
            self.navegar_lista(1)
        if self.joystick.get_button(0):
            self.acionar_selecao()
        if self.joystick.get_button(1):
            self.close()
        if self.joystick.get_button(4):  # LB
            self.selecionar_sidebar(-1)
        if self.joystick.get_button(5):  # RB
            self.selecionar_sidebar(1)

    def navegar_lista(self, sentido):
        if self.games_list.count() == 0:
            return
        row = self.games_list.currentRow()
        row = (row + sentido) % self.games_list.count()
        self.games_list.setCurrentRow(row)
        self.selecionar_jogo(self.games_list.currentItem())

    def selecionar_sidebar(self, sentido):
        self.sidebar_index = (self.sidebar_index + sentido) % len(self.sidebar_buttons)
        botao_style_base = """
            QPushButton {
                background-color: rgba(0, 50, 150, 0.4);
                color: white;
                border-radius: 10px;
                font-size: 16px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: rgba(0, 150, 255, 0.5);
                color: yellow;
            }
        """
        for i, btn in enumerate(self.sidebar_buttons):
            if i == self.sidebar_index:
                btn.setStyleSheet(botao_style_base + "border: 3px solid yellow;")
            else:
                btn.setStyleSheet(botao_style_base)

    def acionar_selecao(self):
        if self.sidebar_index == 0:
            self.abrir_programa("C:/Program Files (x86)/Steam/steam.exe")
        elif self.sidebar_index == 1:
            self.abrir_programa("C:/Program Files (x86)/Epic Games/Launcher/Portal/Binaries/Win32/EpicGamesLauncher.exe")
        elif self.sidebar_index == 2:
            self.jogar()
        else:  # Temas
            self.abrir_temas()

    # ===== Trilha sonora =====
    def trilha_sonora(self):
        if not self.musicas:
            return
        musica = random.choice(self.musicas)
        pygame.mixer.music.load(musica)
        pygame.mixer.music.play()
        pygame.mixer.music.set_endevent(pygame.USEREVENT)

    def verificar_musica(self):
        for event in pygame.event.get():
            if event.type == pygame.USEREVENT:
                self.trilha_sonora()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.redimensionar_capa()
        self.set_background_image()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Launcher()
    window.show()
    sys.exit(app.exec_())
