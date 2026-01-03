import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QTextEdit, QPushButton, QLabel, QProgressBar, QTabWidget)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from compiler_engine import MiniCompiler

# --- WORKER THREAD (Mantido conforme anterior) ---
class CompileWorker(QThread):
    finished = pyqtSignal(str, str)
    progress = pyqtSignal(int, str)

    def __init__(self, compiler, py_source):
        super().__init__()
        self.compiler = compiler
        self.py_source = py_source

    def run(self):
        self.progress.emit(20, "Iniciando Investigação AST...")
        cpp_code = self.compiler.translate(self.py_source)
        
        if "// Erro" in cpp_code:
            self.finished.emit(f"FALHA NA TRADUÇÃO:\n{cpp_code}", cpp_code)
            return

        self.progress.emit(60, "Sincronizando com arduino-cli...")
        result = self.compiler.upload(cpp_code)
        
        self.progress.emit(100, "Ciclo completo.")
        self.finished.emit(result, cpp_code)

# --- MAIN WINDOW ---
class ArduinoIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WANDI ENGINE - COMPILER INVESTIGATION")
        self.compiler = MiniCompiler(port="COM5")
        self.init_ui()
        self.apply_hacker_style()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header Status
        self.status_label = QLabel("> SYSTEM_READY: WAITING_FOR_COMMAND")
        layout.addWidget(self.status_label)

        # ÁREA DE CÓDIGO COM TEMPLATE INICIAL
        self.code_input = QTextEdit()
        self.code_input.setObjectName("code_input")
        
        # PONTO SEGURO PARA ALTERAÇÃO: Este é o código que aparecerá ao abrir
        initial_code = (
            "def setup():\n"
            "    pinMode(13, OUTPUT)\n"
            "\n"
            "def loop():\n"
            "    digital_write(13, HIGH)\n"
            "    delay(500)\n"
            "    digital_write(13, LOW)\n"
            "    delay(500)"
        )
        self.code_input.setPlainText(initial_code)
        layout.addWidget(self.code_input)

        # Progress e Botão
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        layout.addWidget(self.progress_bar)

        self.btn_run = QPushButton("RUN_TRANSPILER_AND_UPLOAD")
        self.btn_run.clicked.connect(self.start_process)
        layout.addWidget(self.btn_run)

        # Sistema de Abas
        self.tabs = QTabWidget()
        
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setObjectName("console")
        self.tabs.addTab(self.console, "TERMINAL_LOG")

        self.cpp_viewer = QTextEdit()
        self.cpp_viewer.setReadOnly(True)
        self.cpp_viewer.setObjectName("cpp_viewer")
        self.tabs.addTab(self.cpp_viewer, "GENERATED_CPP_SOURCE")

        layout.addWidget(self.tabs)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def apply_hacker_style(self):
        # Estilo Deep Blue Hacker (Mantido para consistência)
        self.setStyleSheet("""
            QMainWindow { background-color: #000814; }
            QLabel { color: #00CCFF; font-family: 'Consolas'; font-size: 11px; }
            QTextEdit { 
                background-color: #001220; color: #00F0FF; 
                border: 1px solid #003366; font-family: 'Consolas'; font-size: 13px;
            }
            QTabWidget::pane { border: 1px solid #003366; background: #000814; }
            QTabBar::tab {
                background: #001D3D; color: #00CCFF; padding: 8px 20px;
                font-family: 'Consolas'; border: 1px solid #003366;
            }
            QTabBar::tab:selected { background: #003566; color: white; border-bottom: 2px solid #00F0FF; }
            QProgressBar { background-color: #001220; border-radius: 3px; }
            QProgressBar::chunk { background-color: #00F0FF; }
            QPushButton {
                background-color: #003566; color: white; border: 1px solid #00F0FF;
                padding: 12px; font-family: 'Consolas'; font-weight: bold;
            }
            QPushButton:hover { background-color: #004080; border: 1px solid #00FFFF; }
        """)

    def start_process(self):
        source = self.code_input.toPlainText()
        self.btn_run.setEnabled(False)
        self.console.clear()
        self.cpp_viewer.clear()
        self.tabs.setCurrentIndex(0) 
        
        self.worker = CompileWorker(self.compiler, source)
        self.worker.progress.connect(self.update_ui_status)
        self.worker.finished.connect(self.on_process_finished)
        self.worker.start()

    def update_ui_status(self, val, msg):
        self.progress_bar.setValue(val)
        self.status_label.setText(f"> {msg.upper()}")
        self.console.append(f"[SYSTEM]: {msg}")

    def on_process_finished(self, upload_result, cpp_code):
        self.cpp_viewer.setText(cpp_code)
        self.console.append("\n[UPLOAD_RESULT]:\n" + upload_result)
        self.btn_run.setEnabled(True)
        
        if "SUCESSO" in upload_result:
            self.status_label.setText("> STATUS: MISSION_SUCCESS")
        else:
            self.status_label.setText("> STATUS: CORE_FAILURE")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ArduinoIDE()
    window.show()
    sys.exit(app.exec())