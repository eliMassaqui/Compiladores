import ast
import subprocess
import os
import shutil
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QTextEdit, QPushButton, QLabel, QProgressBar, QTabWidget)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# --- CORE ENGINE: COMPILER ---

class MiniCompiler:
    def __init__(self, port="COM5"):
        self.port = port
        
        # Localização dinâmica das ferramentas Wandi Studio
        user_documents = os.path.join(os.path.expanduser("~"), "Documents")
        self.arduino_tools_dir = os.path.join(user_documents, "Wandi Studio", "Engine", "arduino")
        self.sketch_dir = os.path.join(self.arduino_tools_dir, "build_sketch")
        self.ino_path = os.path.join(self.sketch_dir, "build_sketch.ino")
        
        self.possible_cli_paths = [
            "arduino-cli",
            os.path.join(self.arduino_tools_dir, "arduino-cli.exe"),
            os.path.join(os.getcwd(), "arduino-cli.exe"),
        ]

    def _find_cli(self) -> str:
        """Localiza o arduino-cli no sistema Deep Blue."""
        for path in self.possible_cli_paths:
            if shutil.which(path) or os.path.exists(path):
                return f'"{path}"' 
        return None

    def translate(self, py_code: str) -> str:
        """Traduz Python para C++ respeitando a lógica original."""
        try:
            tree = ast.parse(py_code)
            cpp_lines = ["// Gerado via Wandi Engine - DEEP BLUE SYSTEM", ""]
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    cpp_lines.append(f"void {node.name}() {{")
                    
                    for stmt in node.body:
                        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                            name = stmt.value.func.id
                            
                            args = []
                            for a in stmt.value.args:
                                if isinstance(a, ast.Constant):
                                    args.append(a.value)
                                elif isinstance(a, ast.Name):
                                    args.append(a.id)

                            # MAPEAMENTO WIRING
                            if name == "pinMode":
                                mode = str(args[1]).upper()
                                cpp_lines.append(f"  pinMode({args[0]}, {mode});")
                                
                            elif name == "digitalWrite":
                                val = str(args[1]).upper()
                                status = "HIGH" if val in ["1", "TRUE", "HIGH"] else "LOW"
                                cpp_lines.append(f"  digitalWrite({args[0]}, {status});")
                                
                            elif name == "delay":
                                cpp_lines.append(f"  delay({args[0]});")
                                
                    cpp_lines.append("}\n")
            
            return "\n".join(cpp_lines)
        except Exception as e:
            # ALERTA DE IDENTAÇÃO: Regra essencial do projeto
            return f"// ERRO DE SISTEMA: Verifique a IDENTAÇÃO ou Sintaxe.\n// Detalhe: {e}"

    def upload(self, cpp_code: str):
        """Compila e grava o código via Deep Blue CLI."""
        cli_bin = self._find_cli()
        if not cli_bin:
            return f"ERRO: arduino-cli não localizado em {self.arduino_tools_dir}"

        if not os.path.exists(self.sketch_dir):
            os.makedirs(self.sketch_dir, exist_ok=True)
            
        with open(self.ino_path, "w") as f:
            f.write(cpp_code)

        command = f'{cli_bin} compile --upload -p {self.port} -b arduino:avr:uno "{self.sketch_dir}"'
        
        try:
            process = subprocess.run(command, shell=True, capture_output=True, text=True)
            if process.returncode == 0:
                return f"SUCESSO: Sequência Deep Blue completa na {self.port}\n{process.stdout}"
            return f"ERRO NA GRAVAÇÃO:\n{process.stderr}"
        except Exception as e:
            return f"FALHA CRÍTICA: {e}"

# --- UI ENGINE: DEEP BLUE INTERFACE ---

class CompileWorker(QThread):
    finished = pyqtSignal(str, str)
    progress = pyqtSignal(int, str)

    def __init__(self, compiler, py_source):
        super().__init__()
        self.compiler = compiler
        self.py_source = py_source

    def run(self):
        self.progress.emit(25, "Iniciando Investigação AST...")
        cpp_code = self.compiler.translate(self.py_source)
        
        if "// ERRO" in cpp_code:
            self.finished.emit(f"FALHA NO ANALISADOR:\n{cpp_code}", cpp_code)
            return

        self.progress.emit(75, "Sincronizando Hardware via Deep Blue...")
        result = self.compiler.upload(cpp_code)
        
        self.progress.emit(100, "Sincronização Finalizada.")
        self.finished.emit(result, cpp_code)

class ArduinoIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WANDI ENGINE - DEEP BLUE COMPILER")
        self.compiler = MiniCompiler(port="COM5")
        self.init_ui()
        self.apply_deep_blue_style()

    def init_ui(self):
        layout = QVBoxLayout()
        
        self.status_label = QLabel("> SYSTEM_STATUS: ONLINE")
        layout.addWidget(self.status_label)

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
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        self.btn_run = QPushButton("EXECUTE_DEEP_BLUE_SEQUENCE")
        self.btn_run.clicked.connect(self.start_process)
        layout.addWidget(self.btn_run)

        self.tabs = QTabWidget()
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.tabs.addTab(self.console, "DEEP_BLUE_LOG")

        self.cpp_viewer = QTextEdit()
        self.cpp_viewer.setReadOnly(True)
        self.tabs.addTab(self.cpp_viewer, "WIRING_SOURCE")
        layout.addWidget(self.tabs)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def apply_deep_blue_style(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #000814; }
            QLabel { color: #00B4D8; font-family: 'Consolas'; font-size: 12px; }
            QTextEdit { 
                background-color: #001220; color: #CAF0F8; 
                border: 1px solid #003566; font-family: 'Consolas'; font-size: 14px;
            }
            QTabWidget::pane { border: 1px solid #003566; background: #000814; }
            QTabBar::tab {
                background: #001D3D; color: #00B4D8; padding: 10px;
                font-family: 'Consolas'; border: 1px solid #003566;
            }
            QTabBar::tab:selected { background: #003566; color: white; border-bottom: 2px solid #ADE8F4; }
            QProgressBar { background-color: #001220; border-radius: 0px; }
            QProgressBar::chunk { background-color: #0077B6; }
            QPushButton {
                background-color: #003566; color: #CAF0F8; border: 1px solid #00B4D8;
                padding: 15px; font-family: 'Consolas'; font-weight: bold;
            }
            QPushButton:hover { background-color: #023E8A; }
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
        self.console.append("\n[FINAL_REPORT]:\n" + result)
        self.btn_run.setEnabled(True)
        self.status_label.setText("> STATUS: SYSTEM_IDLE")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ArduinoIDE()
    window.show()
    sys.exit(app.exec())