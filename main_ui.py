import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QTextEdit, QPushButton, QLabel, QProgressBar, QTabWidget)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from compiler_engine import MiniCompiler

class CompileWorker(QThread):
    """Thread para processamento em background (Evita travar o App)."""
    finished = pyqtSignal(str, str)
    progress = pyqtSignal(int, str)

    def __init__(self, compiler, py_source):
        super().__init__()
        self.compiler = compiler
        self.py_source = py_source

    def run(self):
        self.progress.emit(25, "Executando Investigação AST...")
        cpp_code = self.compiler.translate(self.py_source)
        
        if "// ERRO" in cpp_code:
            self.finished.emit(f"FALHA NO ANALISADOR:\n{cpp_code}", cpp_code)
            return

        self.progress.emit(75, "Enviando para Hardware via CLI...")
        result = self.compiler.upload(cpp_code)
        
        self.progress.emit(100, "Processo Finalizado.")
        self.finished.emit(result, cpp_code)

class ArduinoIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WANDI ENGINE - DEEP BLUE COMPILER")
        self.compiler = MiniCompiler(port="COM5")
        self.init_ui()
        self.apply_hacker_style()

    def init_ui(self):
        layout = QVBoxLayout()
        
        self.status_label = QLabel("> STATUS: READY")
        layout.addWidget(self.status_label)

        # Editor de Código com Código Inicial padrão Wiring
        self.code_input = QTextEdit()
        self.code_input.setObjectName("code_input")
        initial_code = (
            "def setup():\n"
            "    pinMode(13, OUTPUT)\n"
            "\n"
            "def loop():\n"
            "    digitalWrite(13, HIGH)\n"
            "    delay(500)\n"
            "    digitalWrite(13, LOW)\n"
            "    delay(500)"
        )
        self.code_input.setPlainText(initial_code)
        layout.addWidget(self.code_input)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        self.btn_run = QPushButton("RUN_ENGINE_SEQUENCE")
        self.btn_run.clicked.connect(self.start_process)
        layout.addWidget(self.btn_run)

        # Sistema de Abas Separadas (Log e Código Gerado)
        self.tabs = QTabWidget()
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.tabs.addTab(self.console, "TERMINAL_LOG")

        self.cpp_viewer = QTextEdit()
        self.cpp_viewer.setReadOnly(True)
        self.tabs.addTab(self.cpp_viewer, "GENERATED_WIRING_SOURCE")
        layout.addWidget(self.tabs)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def apply_hacker_style(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #000814; }
            QLabel { color: #00CCFF; font-family: 'Consolas'; font-size: 12px; }
            QTextEdit { 
                background-color: #001220; color: #00F0FF; 
                border: 1px solid #003366; font-family: 'Consolas'; font-size: 14px;
            }
            QTabWidget::pane { border: 1px solid #003366; background: #000814; }
            QTabBar::tab {
                background: #001D3D; color: #00CCFF; padding: 10px;
                font-family: 'Consolas'; border: 1px solid #003366;
            }
            QTabBar::tab:selected { background: #003566; color: white; border-bottom: 2px solid #00F0FF; }
            QProgressBar { background-color: #001220; border-radius: 4px; }
            QProgressBar::chunk { background-color: #00F0FF; }
            QPushButton {
                background-color: #003566; color: white; border: 1px solid #00F0FF;
                padding: 15px; font-family: 'Consolas'; font-weight: bold;
            }
            QPushButton:hover { background-color: #004080; }
        """)

    def start_process(self):
        source = self.code_input.toPlainText()
        self.btn_run.setEnabled(False)
        self.console.clear()
        self.cpp_viewer.clear()
        self.tabs.setCurrentIndex(0) 
        
        self.worker = CompileWorker(self.compiler, source)
        self.worker.progress.connect(self.update_status)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def update_status(self, val, msg):
        self.progress_bar.setValue(val)
        self.status_label.setText(f"> {msg.upper()}")
        self.console.append(f"[SYS]: {msg}")

    def on_finished(self, result, cpp):
        self.cpp_viewer.setText(cpp)
        self.console.append("\n[RESULTADO]:\n" + result)
        self.btn_run.setEnabled(True)
        self.status_label.setText("> STATUS: OPERATION_COMPLETE")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ArduinoIDE()
    window.show()
    sys.exit(app.exec())