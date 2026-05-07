# ollama_model_manager_gui.py
import os
import sys
import json
import shutil
import tarfile
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from threading import Thread
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

class OllamaManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ollama Model Manager")
        self.root.geometry("950x750")
        
        # Variable para la ruta base
        self.base_path = tk.StringVar()
        
        # Inicializar atributos
        self.export_tree: Optional[ttk.Treeview] = None
        self.import_tree: Optional[ttk.Treeview] = None
        self.export_selected_models: Dict[str, Any] = {}
        self.import_selected_models: Dict[str, Any] = {}
        self.import_models_data: List[Dict[str, Any]] = []
        self.export_selection_counter: Optional[ttk.Label] = None
        self.import_selection_counter: Optional[ttk.Label] = None
        self.export_folder: Optional[ttk.Entry] = None
        self.import_folder: Optional[ttk.Entry] = None
        self.name_format_export = tk.StringVar(value="{modelo}_{tamaño}")
        self.export_btn: Optional[ttk.Button] = None
        self.import_btn: Optional[ttk.Button] = None
        self.export_progress_bar: Optional[ttk.Progressbar] = None
        self.import_progress_bar: Optional[ttk.Progressbar] = None
        self.export_status_label: Optional[ttk.Label] = None
        self.import_status_label: Optional[ttk.Label] = None
        self.config_base_path: Optional[ttk.Entry] = None
        self.path_info_label: Optional[ttk.Label] = None
        
        self.create_widgets()
        
        # Pedir ruta base al iniciar
        self.root.after(100, self.ask_for_base_path)
    
    def ask_for_base_path(self):
        """Solicita la ruta base de Ollama al iniciar el programa"""
        default_path = os.path.expanduser("~/.ollama/models")
        
        # Crear ventana de diálogo personalizada
        dialog = tk.Toplevel(self.root)
        dialog.title("Configuración Inicial")
        dialog.geometry("600x280")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centrar ventana
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (280 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        ttk.Label(dialog, text="Configuración de Ollama", font=("Arial", 14, "bold")).pack(pady=10)
        ttk.Label(dialog, text="Por favor, indique la ruta donde Ollama almacena los modelos:", 
                  font=("Arial", 10)).pack(pady=5)
        
        frame = ttk.Frame(dialog)
        frame.pack(pady=10, padx=20, fill='x')
        
        ttk.Label(frame, text="Ruta base:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        path_entry = ttk.Entry(frame, textvariable=self.base_path, width=50)
        path_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(frame, text="Examinar...", command=lambda: self.select_base_path_dialog(path_entry)).grid(row=0, column=2, padx=5)
        
        # Mostrar ruta por defecto
        self.base_path.set(default_path)
        
        info_frame = ttk.LabelFrame(dialog, text="Información", padding=10)
        info_frame.pack(pady=10, padx=20, fill='x')
        ttk.Label(info_frame, text=f"Ruta por defecto: {default_path}\n"
                                   "Puede modificarla si Ollama está instalado en otra ubicación.\n"
                                   "La ruta debe contener las carpetas 'blobs' y 'manifests'.", 
                  justify='left').pack()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        def confirm_path():
            if self.validate_base_path():
                dialog.destroy()
                self.load_models_list()
                self.load_config_to_ui()  # Cargar la configuración a la pestaña
            else:
                response = messagebox.askyesno("Ruta Inválida", 
                    f"La ruta '{self.base_path.get()}' no parece contener modelos de Ollama.\n"
                    "¿Desea continuar de todos modos?")
                if response:
                    dialog.destroy()
                    self.load_models_list()
                    self.load_config_to_ui()
        
        ttk.Button(btn_frame, text="Confirmar", command=confirm_path).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Salir", command=self.root.quit).pack(side='left', padx=5)
    
    def select_base_path_dialog(self, entry_widget):
        """Selector de ruta en el diálogo inicial"""
        path = filedialog.askdirectory(title="Seleccionar carpeta de modelos de Ollama")
        if path:
            self.base_path.set(path)
    
    def validate_base_path(self) -> bool:
        """Valida si la ruta base contiene modelos de Ollama"""
        manifests_path = os.path.join(self.base_path.get(), "manifests", "registry.ollama.ai", "library")
        return os.path.exists(manifests_path) and len(os.listdir(manifests_path)) > 0
    
    def create_widgets(self):
        # Notebook para pestañas
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Pestaña Exportar Modelos
        self.export_frame = ttk.Frame(notebook)
        notebook.add(self.export_frame, text="📤 Exportar Modelos")
        self.create_export_tab()
        
        # Pestaña Importar Modelos
        self.import_frame = ttk.Frame(notebook)
        notebook.add(self.import_frame, text="📥 Importar Modelos")
        self.create_import_tab()
        
        # Pestaña Configuración
        self.config_frame = ttk.Frame(notebook)
        notebook.add(self.config_frame, text="⚙️ Configuración")
        self.create_config_tab()
        
        # Área de log
        self.log_text = scrolledtext.ScrolledText(self.root, height=8)
        self.log_text.pack(fill='both', padx=10, pady=(0,10))
    
    def create_config_tab(self):
        """Crea la pestaña de configuración"""
        main_frame = ttk.Frame(self.config_frame, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Configuración de ruta base
        path_frame = ttk.LabelFrame(main_frame, text="Ruta Base de Ollama", padding=15)
        path_frame.pack(fill='x', pady=(0, 20))
        
        ttk.Label(path_frame, text="Ubicación de los modelos de Ollama:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky='w')
        
        path_entry_frame = ttk.Frame(path_frame)
        path_entry_frame.grid(row=1, column=0, columnspan=3, pady=10, sticky='ew')
        
        self.config_base_path = ttk.Entry(path_entry_frame, textvariable=self.base_path, width=70)
        self.config_base_path.pack(side='left', padx=(0, 10))
        
        ttk.Button(path_entry_frame, text="📁 Examinar...", command=self.select_config_base_path).pack(side='left')
        
        # Información de la ruta actual
        info_frame = ttk.LabelFrame(main_frame, text="Información", padding=15)
        info_frame.pack(fill='x', pady=(0, 20))
        
        self.path_info_label = ttk.Label(info_frame, text="", justify='left')
        self.path_info_label.pack()
        
        # Botones de acción
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="💾 Guardar Configuración", command=self.save_config_from_ui).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🔄 Refrescar Lista de Modelos", command=lambda: self.refresh_all_lists()).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="📂 Abrir Carpeta de Modelos", command=self.open_models_folder).pack(side='left', padx=5)
        
        # Información de ayuda
        help_frame = ttk.LabelFrame(main_frame, text="Ayuda", padding=15)
        help_frame.pack(fill='both', expand=True, pady=(20, 0))
        
        help_text = """Instrucciones:
• La ruta base debe contener las subcarpetas 'blobs' y 'manifests'
• Por defecto, Ollama guarda los modelos en: ~/.ollama/models
• Cambiar la ruta actualizará automáticamente las listas de modelos
• Puede guardar la configuración para usarla en futuras sesiones
• Haga click en la cabecera "Seleccionar" para seleccionar/deseleccionar todos los modelos"""
        
        ttk.Label(help_frame, text=help_text, justify='left').pack()
    
    def select_config_base_path(self):
        """Selecciona la ruta base desde la pestaña de configuración"""
        path = filedialog.askdirectory(title="Seleccionar carpeta de modelos de Ollama")
        if path:
            self.base_path.set(path)
            self.update_path_info()
            # Refrescar listas de modelos
            self.refresh_all_lists()
            self.log(f"📁 Ruta base cambiada a: {path}")
    
    def update_path_info(self):
        """Actualiza la información de la ruta en la pestaña de configuración"""
        if not self.path_info_label:
            return
            
        base_path = self.base_path.get()
        manifests_path = os.path.join(base_path, "manifests", "registry.ollama.ai", "library")
        blobs_path = os.path.join(base_path, "blobs")
        
        info = f"📂 Ruta actual: {base_path}\n\n"
        
        if os.path.exists(manifests_path):
            models_count = len(os.listdir(manifests_path)) if os.path.exists(manifests_path) else 0
            info += f"✅ Modelos encontrados: {models_count}\n"
        else:
            info += f"⚠️ No se encontraron modelos en esta ruta\n"
        
        if os.path.exists(blobs_path):
            blobs_count = len(os.listdir(blobs_path)) if os.path.exists(blobs_path) else 0
            info += f"✅ Blobs encontrados: {blobs_count}\n"
        else:
            info += f"⚠️ Carpeta 'blobs' no encontrada\n"
        
        # Verificar estructura
        if os.path.exists(manifests_path) and os.path.exists(blobs_path):
            info += "\n✓ Estructura de carpetas válida"
        else:
            info += "\n✗ Estructura de carpetas inválida"
        
        self.path_info_label.config(text=info)
    
    def save_config_from_ui(self):
        """Guarda la configuración desde la pestaña"""
        config_file = os.path.expanduser("~/.ollama_manager_config.json")
        config = {
            'base_path': self.base_path.get(),
            'last_updated': datetime.now().isoformat()
        }
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            self.log("✅ Configuración guardada correctamente")
            messagebox.showinfo("Éxito", "Configuración guardada correctamente")
        except Exception as e:
            self.log(f"❌ Error al guardar configuración: {str(e)}")
            messagebox.showerror("Error", f"No se pudo guardar la configuración:\n{str(e)}")
    
    def load_config_to_ui(self):
        """Carga la configuración guardada y la muestra en la UI"""
        config_file = os.path.expanduser("~/.ollama_manager_config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    if 'base_path' in config:
                        self.base_path.set(config['base_path'])
                        self.log(f"📂 Configuración cargada: {config['base_path']}")
            except Exception as e:
                self.log(f"⚠️ Error al cargar configuración: {str(e)}")
        
        # Actualizar información
        self.update_path_info()
    
    def refresh_all_lists(self):
        """Refresca todas las listas de modelos"""
        self.load_models_list()
        if self.import_folder and self.import_folder.get():
            self.scan_import_models()
        self.log("🔄 Listas de modelos actualizadas")
    
    def open_models_folder(self):
        """Abre la carpeta de modelos en el explorador de archivos"""
        base_path = self.base_path.get()
        if os.path.exists(base_path):
            if sys.platform == 'win32':
                os.startfile(base_path)
            elif sys.platform == 'darwin':
                os.system(f'open "{base_path}"')
            else:
                os.system(f'xdg-open "{base_path}"')
        else:
            messagebox.showerror("Error", f"La carpeta no existe:\n{base_path}")
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Escanea y retorna una lista de modelos disponibles con sus tamaños"""
        models = []
        manifests_path = os.path.join(self.base_path.get(), "manifests", "registry.ollama.ai", "library")
        
        if not os.path.exists(manifests_path):
            return models
        
        for model_name in os.listdir(manifests_path):
            model_dir = os.path.join(manifests_path, model_name)
            if os.path.isdir(model_dir):
                for size_file in os.listdir(model_dir):
                    size_path = os.path.join(model_dir, size_file)
                    if os.path.isfile(size_path):
                        models.append({
                            'name': model_name,
                            'size': size_file,
                            'manifest_path': size_path
                        })
        return sorted(models, key=lambda x: x['name'])
    
    def get_blob_info(self, manifest_path: str) -> str:
        """Obtiene información del tamaño total de los blobs"""
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            total_size = 0
            blob_dir = os.path.join(self.base_path.get(), "blobs")
            
            # Verificar config
            if "config" in manifest and "digest" in manifest["config"]:
                digest = manifest["config"]["digest"]
                blob_file = os.path.join(blob_dir, digest.replace(":", "-", 1))
                if os.path.exists(blob_file):
                    total_size += os.path.getsize(blob_file)
            
            # Verificar layers
            if "layers" in manifest:
                for layer in manifest["layers"]:
                    if "digest" in layer:
                        digest = layer["digest"]
                        blob_file = os.path.join(blob_dir, digest.replace(":", "-", 1))
                        if os.path.exists(blob_file):
                            total_size += os.path.getsize(blob_file)
            
            # Formatear tamaño
            if total_size == 0:
                return "Desconocido"
            elif total_size < 1024**2:
                return f"{total_size / 1024:.1f} KB"
            elif total_size < 1024**3:
                return f"{total_size / (1024**2):.1f} MB"
            else:
                return f"{total_size / (1024**3):.2f} GB"
        except:
            return "Error"
    
    def create_export_tab(self):
        # Frame principal
        main_frame = ttk.Frame(self.export_frame)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Frame para la lista de modelos
        list_frame = ttk.LabelFrame(main_frame, text="Modelos Disponibles para Exportar", padding=10)
        list_frame.pack(fill='both', expand=True)
        
        # Treeview con checkboxes (sin botón seleccionar todo)
        self.create_checkbox_treeview(list_frame, 'export')
        
        # Frame para opciones de exportación
        options_frame = ttk.LabelFrame(main_frame, text="Opciones de Exportación", padding=10)
        options_frame.pack(fill='x', pady=10)
        
        ttk.Label(options_frame, text="Carpeta de destino:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.export_folder = ttk.Entry(options_frame, width=70)
        self.export_folder.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(options_frame, text="Examinar...", command=self.select_export_folder).grid(row=0, column=2, padx=5)
        
        ttk.Label(options_frame, text="Formato de nombre:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        format_combo = ttk.Combobox(options_frame, textvariable=self.name_format_export, width=40)
        format_combo['values'] = (
            "{modelo}_{tamaño}",
            "{modelo}_{tamaño}_{fecha}",
            "ollama_{modelo}_{tamaño}",
            "{modelo}_{tamaño}_export"
        )
        format_combo.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        # Botón exportar
        self.export_btn = ttk.Button(main_frame, text="📦 Exportar Modelos Seleccionados", 
                                     command=self.start_export, state='normal')
        self.export_btn.pack(pady=10)
        
        # Progress bar
        self.export_progress_bar = ttk.Progressbar(main_frame, mode='determinate')
        self.export_progress_bar.pack(fill='x', pady=5)
        self.export_status_label = ttk.Label(main_frame, text="")
        self.export_status_label.pack()
    
    def create_import_tab(self):
        # Frame principal
        main_frame = ttk.Frame(self.import_frame)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Frame para selección de carpeta
        folder_frame = ttk.LabelFrame(main_frame, text="Carpeta con Modelos Exportados", padding=10)
        folder_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(folder_frame, text="Carpeta origen:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.import_folder = ttk.Entry(folder_frame, width=70)
        self.import_folder.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(folder_frame, text="Examinar...", command=self.select_import_folder).grid(row=0, column=2, padx=5)
        ttk.Button(folder_frame, text="🔍 Escanear Modelos", command=self.scan_import_models).grid(row=1, column=1, pady=5)
        
        # Frame para la lista de modelos a importar
        list_frame = ttk.LabelFrame(main_frame, text="Modelos Disponibles para Importar", padding=10)
        list_frame.pack(fill='both', expand=True)
        
        # Treeview con checkboxes para importar (sin botón seleccionar todo)
        self.create_checkbox_treeview(list_frame, 'import')
        
        # Botón importar
        self.import_btn = ttk.Button(main_frame, text="📥 Importar Modelos Seleccionados", 
                                     command=self.start_import, state='disabled')
        self.import_btn.pack(pady=10)
        
        # Progress bar
        self.import_progress_bar = ttk.Progressbar(main_frame, mode='determinate')
        self.import_progress_bar.pack(fill='x', pady=5)
        self.import_status_label = ttk.Label(main_frame, text="")
        self.import_status_label.pack()
    
    def create_checkbox_treeview(self, parent, mode: str):
        """Crea un Treeview con checkboxes para selección de modelos (sin botón seleccionar todo)"""
        # Frame con scrollbar
        frame = ttk.Frame(parent)
        frame.pack(fill='both', expand=True)
        
        scrollbar_y = ttk.Scrollbar(frame)
        scrollbar_y.pack(side='right', fill='y')
        
        scrollbar_x = ttk.Scrollbar(frame, orient='horizontal')
        scrollbar_x.pack(side='bottom', fill='x')
        
        # Treeview con columnas
        columns = ("Seleccionar", "Modelo", "Tamaño/Versión", "Tamaño en Disco")
        tree = ttk.Treeview(frame, columns=columns, show="headings", 
                           yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # Configurar columnas
        tree.heading("Seleccionar", text="☐ Seleccionar")
        tree.heading("Modelo", text="Modelo")
        tree.heading("Tamaño/Versión", text="Tamaño/Versión")
        tree.heading("Tamaño en Disco", text="Tamaño en Disco")
        
        tree.column("Seleccionar", width=80, anchor='center')
        tree.column("Modelo", width=200)
        tree.column("Tamaño/Versión", width=150)
        tree.column("Tamaño en Disco", width=120)
        
        tree.pack(fill='both', expand=True)
        scrollbar_y.config(command=tree.yview)
        scrollbar_x.config(command=tree.xview)
        
        # Frame para controles de selección (solo botón refrescar)
        select_frame = ttk.Frame(parent)
        select_frame.pack(fill='x', pady=5)
        
        ttk.Button(select_frame, text="🔄 Refrescar", 
                  command=lambda: self.refresh_models_list(mode)).pack(side='left', padx=5)
        
        # Agregar contador de selección
        selection_counter = ttk.Label(select_frame, text="Seleccionados: 0")
        selection_counter.pack(side='right', padx=5)
        
        # Almacenar referencia al treeview y contador
        if mode == 'export':
            self.export_tree = tree
            self.export_selection_counter = selection_counter
        else:
            self.import_tree = tree
            self.import_selection_counter = selection_counter
        
        # Bind click en la columna de checkbox
        tree.bind('<ButtonRelease-1>', lambda e: self.on_tree_click(e, mode))
    
    def update_selection_counter(self, mode: str):
        """Actualiza el contador de modelos seleccionados"""
        if mode == 'export':
            count = len(self.export_selected_models)
            if self.export_selection_counter:
                self.export_selection_counter.config(text=f"Seleccionados: {count}")
        else:
            count = len(self.import_selected_models)
            if self.import_selection_counter:
                self.import_selection_counter.config(text=f"Seleccionados: {count}")
    
    def on_tree_click(self, event, mode: str):
        """Maneja el click en el treeview para toggle del checkbox"""
        tree = self.export_tree if mode == 'export' else self.import_tree
        
        # Verificar que tree no sea None
        if tree is None:
            return
            
        region = tree.identify_region(event.x, event.y)
        if region == "heading":
            # Verificar si se hizo click en la columna "Seleccionar"
            column = tree.identify_column(event.x)
            if column == "#1":
                self.toggle_all_visible(mode)
        else:
            # Click en una fila
            item = tree.identify_row(event.y)
            if item:
                # Verificar si el click fue en la primera columna
                bbox = tree.bbox(item, "#1")
                if bbox and bbox[0] <= event.x <= bbox[0] + bbox[2]:
                    self.toggle_model_selection(item, mode)
    
    def toggle_all_visible(self, mode: str):
        """Alterna la selección de todos los modelos visibles"""
        tree = self.export_tree if mode == 'export' else self.import_tree
        
        # Verificar que tree no sea None
        if tree is None:
            return
            
        items = tree.get_children()
        if not items:
            return
        
        # Verificar si todos están seleccionados
        all_selected = all(tree.set(item, "Seleccionar") == "☑" for item in items)
        
        # Si todos están seleccionados, deseleccionar todos; si no, seleccionar todos
        new_value = "☐" if all_selected else "☑"
        
        for item in items:
            tree.set(item, "Seleccionar", new_value)
            
            # Actualizar diccionario de seleccionados
            values = tree.item(item)['values']
            if values and len(values) >= 3:
                model_name = str(values[1])
                model_size = str(values[2])
                model_key = f"{model_name}:{model_size}"
                
                if new_value == "☑":
                    if mode == 'export':
                        self.export_selected_models[model_key] = {'name': model_name, 'size': model_size}
                    else:
                        # Buscar file_path para importación
                        file_path = None
                        for model_data in self.import_models_data:
                            if model_data['name'] == model_name and model_data['size'] == model_size:
                                file_path = model_data['file_path']
                                break
                        self.import_selected_models[model_key] = {
                            'name': model_name, 
                            'size': model_size,
                            'file_path': file_path
                        }
                else:
                    if mode == 'export':
                        self.export_selected_models.pop(model_key, None)
                    else:
                        self.import_selected_models.pop(model_key, None)
        
        self.update_selection_counter(mode)
        self.update_button_state(mode)
    
    def toggle_model_selection(self, item: str, mode: str):
        """Alterna la selección de un modelo individual"""
        tree = self.export_tree if mode == 'export' else self.import_tree
        
        # Verificar que tree no sea None
        if tree is None:
            return
            
        current = tree.set(item, "Seleccionar")
        new_value = "☑" if current == "☐" else "☐"
        tree.set(item, "Seleccionar", new_value)
        
        # Actualizar diccionario de seleccionados
        values = tree.item(item)['values']
        if values and len(values) >= 3:
            model_name = str(values[1])
            model_size = str(values[2])
            model_key = f"{model_name}:{model_size}"
            
            if new_value == "☑":
                if mode == 'export':
                    self.export_selected_models[model_key] = {'name': model_name, 'size': model_size}
                else:
                    # Buscar file_path para importación
                    file_path = None
                    for model_data in self.import_models_data:
                        if model_data['name'] == model_name and model_data['size'] == model_size:
                            file_path = model_data['file_path']
                            break
                    self.import_selected_models[model_key] = {
                        'name': model_name, 
                        'size': model_size,
                        'file_path': file_path
                    }
            else:
                if mode == 'export':
                    self.export_selected_models.pop(model_key, None)
                else:
                    self.import_selected_models.pop(model_key, None)
        
        self.update_selection_counter(mode)
        self.update_button_state(mode)
    
    def update_button_state(self, mode: str):
        """Habilita o deshabilita los botones según haya modelos seleccionados"""
        if mode == 'export':
            if self.export_btn:
                if self.export_selected_models:
                    self.export_btn.config(state='normal')
                else:
                    self.export_btn.config(state='disabled')
        else:
            if self.import_btn:
                if self.import_selected_models:
                    self.import_btn.config(state='normal')
                else:
                    self.import_btn.config(state='disabled')
    
    def load_models_list(self):
        """Carga los modelos en la pestaña de exportación"""
        if self.export_tree is None:
            return
            
        # Limpiar árbol actual
        for item in self.export_tree.get_children():
            self.export_tree.delete(item)
        
        models = self.get_available_models()
        
        if not models:
            self.export_tree.insert("", "end", values=("", "No hay modelos disponibles", "", ""))
            if self.export_btn:
                self.export_btn.config(state='disabled')
            return
        
        for model in models:
            blob_info = self.get_blob_info(model['manifest_path'])
            self.export_tree.insert("", "end", values=("☐", model['name'], model['size'], blob_info))
        
        # Resetear selecciones
        self.export_selected_models.clear()
        self.update_selection_counter('export')
        self.update_button_state('export')
    
    def refresh_models_list(self, mode: str):
        """Refresca la lista de modelos"""
        if mode == 'export':
            self.load_models_list()
        else:
            self.scan_import_models()
        self.log(f"🔄 Lista de modelos {'exportación' if mode == 'export' else 'importación'} actualizada")
    
    def select_export_folder(self):
        """Selecciona la carpeta para exportar"""
        folder = filedialog.askdirectory(title="Seleccionar carpeta para guardar los modelos exportados")
        if folder and self.export_folder:
            self.export_folder.delete(0, tk.END)
            self.export_folder.insert(0, folder)
    
    def select_import_folder(self):
        """Selecciona la carpeta con modelos para importar"""
        folder = filedialog.askdirectory(title="Seleccionar carpeta con modelos exportados")
        if folder and self.import_folder:
            self.import_folder.delete(0, tk.END)
            self.import_folder.insert(0, folder)
            self.scan_import_models()
    
    def scan_import_models(self):
        """Escanea la carpeta seleccionada en busca de archivos .tar"""
        if not self.import_folder:
            return
            
        folder = self.import_folder.get().strip()
        if not folder or not os.path.exists(folder):
            messagebox.showerror("Error", "Seleccione una carpeta válida")
            return
        
        if self.import_tree is None:
            return
            
        # Limpiar árbol actual
        for item in self.import_tree.get_children():
            self.import_tree.delete(item)
        
        self.import_models_data = []
        
        # Buscar archivos .tar
        tar_files = [f for f in os.listdir(folder) if f.endswith('.tar')]
        
        if not tar_files:
            self.import_tree.insert("", "end", values=("", "No hay archivos .tar", "", ""))
            if self.import_btn:
                self.import_btn.config(state='disabled')
            return
        
        for tar_file in tar_files:
            tar_path = os.path.join(folder, tar_file)
            # Intentar extraer información del nombre
            name_parts = tar_file.replace('.tar', '').split('_')
            # Intentar adivinar modelo y tamaño del nombre
            model_name = name_parts[1] if len(name_parts) > 1 else "desconocido"
            model_size = name_parts[2] if len(name_parts) > 2 else "desconocido"
            
            # Obtener tamaño del archivo
            file_size = os.path.getsize(tar_path)
            if file_size < 1024**2:
                size_str = f"{file_size / 1024:.1f} KB"
            elif file_size < 1024**3:
                size_str = f"{file_size / (1024**2):.1f} MB"
            else:
                size_str = f"{file_size / (1024**3):.2f} GB"
            
            self.import_models_data.append({
                'name': model_name,
                'size': model_size,
                'file_path': tar_path,
                'file_size': size_str
            })
            
            self.import_tree.insert("", "end", values=("☐", model_name, model_size, size_str))
        
        # Resetear selecciones
        self.import_selected_models.clear()
        self.update_selection_counter('import')
        self.update_button_state('import')
        
        self.log(f"✅ Escaneados {len(tar_files)} archivos en {folder}")
    
    def start_export(self):
        """Inicia la exportación de los modelos seleccionados"""
        if not self.export_selected_models:
            messagebox.showerror("Error", "Seleccione al menos un modelo para exportar")
            return
        
        if not self.export_folder:
            return
            
        export_folder = self.export_folder.get().strip()
        if not export_folder:
            messagebox.showerror("Error", "Seleccione una carpeta de destino")
            return
        
        if not os.path.exists(export_folder):
            try:
                os.makedirs(export_folder)
            except:
                messagebox.showerror("Error", "No se pudo crear la carpeta de destino")
                return
        
        models_to_export = list(self.export_selected_models.values())
        
        model_list = "\n".join([f"• {m['name']}:{m['size']}" for m in models_to_export])
        if not messagebox.askyesno("Confirmar Exportación", 
            f"Se exportarán {len(models_to_export)} modelos:\n\n{model_list}\n\n"
            f"Carpeta destino: {export_folder}\n\n"
            f"¿Desea continuar?"):
            return
        
        if self.export_btn:
            self.export_btn.config(state='disabled')
        if self.export_progress_bar:
            self.export_progress_bar['value'] = 0
            self.export_progress_bar['maximum'] = len(models_to_export)
        
        thread = Thread(target=self.export_multiple_models, args=(models_to_export, export_folder))
        thread.start()
    
    def export_multiple_models(self, models_to_export: List[Dict[str, Any]], export_folder: str):
        """Exporta múltiples modelos secuencialmente"""
        successful = []
        failed = []
        
        for idx, model in enumerate(models_to_export, 1):
            # Generar nombre de archivo
            formato = self.name_format_export.get()
            fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            nombre_base = formato.format(
                modelo=model['name'],
                tamaño=model['size'],
                fecha=fecha
            )
            output_file = os.path.join(export_folder, f"{nombre_base}.tar")
            
            self.log(f"\n{'='*60}")
            self.log(f"📦 Exportando {idx}/{len(models_to_export)}: {model['name']}:{model['size']}")
            
            try:
                self.root.after(0, self.update_export_status, 
                              f"Exportando {idx}/{len(models_to_export)}: {model['name']}...")
                
                self.export_single_model(model['name'], model['size'], output_file)
                successful.append(f"{model['name']}:{model['size']}")
                self.log(f"✅ Exportado exitosamente: {output_file}")
                
            except Exception as e:
                error_msg = f"❌ Error exportando {model['name']}:{model['size']}: {str(e)}"
                self.log(error_msg)
                failed.append(f"{model['name']}:{model['size']} - {str(e)}")
            
            # Actualizar progreso
            self.root.after(0, self.update_export_progress, idx)
        
        self.root.after(0, self.show_export_summary, successful, failed, export_folder)
    
    def export_single_model(self, model_name: str, model_size: str, output_file: str):
        """Exporta un solo modelo"""
        base_path = self.base_path.get()
        manifest_path = os.path.join(
            base_path, "manifests", "registry.ollama.ai", "library",
            model_name, model_size
        )
        
        if not os.path.isfile(manifest_path):
            raise Exception(f"No se encontró el modelo {model_name}:{model_size}")
        
        with open(manifest_path, "r") as f:
            manifest_json = json.load(f)
        
        # Extraer digests
        digests = set()
        if "config" in manifest_json and "digest" in manifest_json["config"]:
            digests.add(manifest_json["config"]["digest"])
        if "layers" in manifest_json:
            for layer in manifest_json["layers"]:
                if "digest" in layer:
                    digests.add(layer["digest"])
        
        # Crear tarball
        tmpdir = tempfile.mkdtemp()
        try:
            # Copiar manifest
            manifest_dest = os.path.join(tmpdir, "manifests", "registry.ollama.ai", "library", model_name)
            os.makedirs(manifest_dest, exist_ok=True)
            shutil.copy2(manifest_path, os.path.join(manifest_dest, model_size))
            
            # Copiar blobs
            blob_dir = os.path.join(tmpdir, "blobs")
            os.makedirs(blob_dir, exist_ok=True)
            
            for digest in digests:
                blob_fname = digest.replace(":", "-", 1)
                src = os.path.join(base_path, "blobs", blob_fname)
                if os.path.isfile(src):
                    shutil.copy2(src, os.path.join(blob_dir, blob_fname))
            
            # Crear tar
            with tarfile.open(output_file, "w") as tar:
                tar.add(tmpdir, arcname="")
            
        finally:
            shutil.rmtree(tmpdir)
    
    def update_export_progress(self, value: int):
        if self.export_progress_bar:
            self.export_progress_bar['value'] = value
    
    def update_export_status(self, status: str):
        if self.export_status_label:
            self.export_status_label.config(text=status)
    
    def show_export_summary(self, successful: List[str], failed: List[str], export_folder: str):
        if self.export_status_label:
            self.export_status_label.config(text="Exportación completada")
        if self.export_btn:
            self.export_btn.config(state='normal')
        
        summary = f"Exportación completada\n\n✅ Exitosos: {len(successful)}\n❌ Fallidos: {len(failed)}\n\n📁 Ubicación: {export_folder}"
        messagebox.showinfo("Resumen de Exportación", summary)
        self.load_models_list()  # Refrescar lista
    
    def start_import(self):
        """Inicia la importación de los modelos seleccionados"""
        if not self.import_selected_models:
            messagebox.showerror("Error", "Seleccione al menos un modelo para importar")
            return
        
        models_to_import = list(self.import_selected_models.values())
        
        model_list = "\n".join([f"• {m['name']}:{m['size']}" for m in models_to_import])
        if not messagebox.askyesno("Confirmar Importación", 
            f"Se importarán {len(models_to_import)} modelos:\n\n{model_list}\n\n"
            f"¿Desea continuar?"):
            return
        
        if self.import_btn:
            self.import_btn.config(state='disabled')
        if self.import_progress_bar:
            self.import_progress_bar['value'] = 0
            self.import_progress_bar['maximum'] = len(models_to_import)
        
        thread = Thread(target=self.import_multiple_models, args=(models_to_import,))
        thread.start()
    
    def import_multiple_models(self, models_to_import: List[Dict[str, Any]]):
        """Importa múltiples modelos secuencialmente"""
        successful = []
        failed = []
        
        for idx, model in enumerate(models_to_import, 1):
            self.log(f"\n{'='*60}")
            self.log(f"📥 Importando {idx}/{len(models_to_import)}: {model['name']}:{model['size']}")
            
            try:
                self.root.after(0, self.update_import_status, 
                              f"Importando {idx}/{len(models_to_import)}: {model['name']}...")
                
                self.import_single_model(model['file_path'])
                successful.append(f"{model['name']}:{model['size']}")
                self.log(f"✅ Importado exitosamente: {model['name']}:{model['size']}")
                
            except Exception as e:
                error_msg = f"❌ Error importando {model['name']}:{model['size']}: {str(e)}"
                self.log(error_msg)
                failed.append(f"{model['name']}:{model['size']} - {str(e)}")
            
            self.root.after(0, self.update_import_progress, idx)
        
        self.root.after(0, self.show_import_summary, successful, failed)
    
    def import_single_model(self, tarball_path: str):
        """Importa un solo modelo desde un archivo tar"""
        base_path = self.base_path.get()
        tmpdir = tempfile.mkdtemp()
        
        try:
            with tarfile.open(tarball_path, "r") as tar:
                tar.extractall(tmpdir)
            
            # Procesar manifiestos
            manifests_root = os.path.join(tmpdir, "manifests", "registry.ollama.ai", "library")
            if os.path.isdir(manifests_root):
                for model in os.listdir(manifests_root):
                    model_dir = os.path.join(manifests_root, model)
                    if os.path.isdir(model_dir):
                        for size_file in os.listdir(model_dir):
                            manifest_src = os.path.join(model_dir, size_file)
                            if os.path.isfile(manifest_src):
                                dest_manifest_dir = os.path.join(base_path, "manifests", "registry.ollama.ai", "library", model)
                                os.makedirs(dest_manifest_dir, exist_ok=True)
                                dest_manifest = os.path.join(dest_manifest_dir, size_file)
                                shutil.copy2(manifest_src, dest_manifest)
            
            # Procesar blobs
            blobs_src = os.path.join(tmpdir, "blobs")
            if os.path.isdir(blobs_src):
                dest_blobs = os.path.join(base_path, "blobs")
                os.makedirs(dest_blobs, exist_ok=True)
                
                for blob_file in os.listdir(blobs_src):
                    src = os.path.join(blobs_src, blob_file)
                    dest = os.path.join(dest_blobs, blob_file)
                    if not os.path.exists(dest):
                        shutil.copy2(src, dest)
            
        finally:
            shutil.rmtree(tmpdir)
    
    def update_import_progress(self, value: int):
        if self.import_progress_bar:
            self.import_progress_bar['value'] = value
    
    def update_import_status(self, status: str):
        if self.import_status_label:
            self.import_status_label.config(text=status)
    
    def show_import_summary(self, successful: List[str], failed: List[str]):
        if self.import_status_label:
            self.import_status_label.config(text="Importación completada")
        if self.import_btn:
            self.import_btn.config(state='normal')
        
        summary = f"Importación completada\n\n✅ Exitosos: {len(successful)}\n❌ Fallidos: {len(failed)}"
        messagebox.showinfo("Resumen de Importación", summary)
        self.load_models_list()  # Refrescar lista de exportación
    
    def log(self, message: str):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()

def main():
    root = tk.Tk()
    app = OllamaManagerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()