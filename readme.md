# Ollama Model Manager

Una herramienta gráfica para exportar e importar modelos de Ollama de forma sencilla.

## 📌 ¿Qué hace este proyecto?

`ollama_model_manager_gui.py` es una aplicación de escritorio en Python que permite:

- Exportar modelos de Ollama a archivos `*.tar`
- Importar modelos desde archivos `*.tar` a la instalación local de Ollama
- Seleccionar varios modelos a la vez
- Guardar la ruta de la carpeta de modelos de Ollama
- Trabajar con la estructura `manifests` y `blobs` de Ollama

## 📁 Estructura del proyecto

- `ollama_model_manager_gui.py` - aplicación principal
- `requirements.txt` - dependencias del proyecto
- `readme.md` - documentación del proyecto
- `versions/1.1/` y `versions/1.2/` - versiones históricas del código

## 🚀 Requisitos previos

1. Python 3.8 o superior
2. Ollama instalado y configurado en tu sistema
3. Modelos descargados en Ollama (por ejemplo `ollama pull llama2`)
4. Terminal de Windows (`PowerShell` o `cmd`) o consola compatible

> En Windows, la ruta predeterminada de modelos suele ser:
> `C:\Users\TuUsuario\.ollama\models`
>
> En Linux/macOS suele ser:
> `~/.ollama/models`

## 🛠 Instalación desde cero

Sigue estos pasos desde la terminal:

1. Abre una terminal en `d:\htdocs\exportimportollama\exportimportollama`.

2. (Opcional, recomendado) Crea y activa un entorno virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Instala las dependencias del proyecto:

```powershell
pip install -r requirements.txt
```

4. Ejecuta la aplicación desde el código fuente:

```powershell
python ollama_model_manager_gui.py
```

5. Al iniciar la aplicación, el programa pedirá la ruta base donde Ollama guarda sus modelos.
   - Si es necesario, selecciona la carpeta correcta usando el explorador.
   - Si la ruta es válida, la aplicación mostrará los modelos disponibles para exportar/importar.

## ▶️ Uso básico

1. En la pestaña **Exportar Modelos**:
   - Selecciona los modelos que deseas exportar.
   - Elige la carpeta de destino.
   - Ajusta el formato del nombre si quieres.
   - Haz clic en **Exportar**.

2. En la pestaña **Importar Modelos**:
   - Selecciona la carpeta donde están los archivos `*.tar` de modelos.
   - Haz clic en **Escanear Modelos**.
   - Selecciona los modelos que deseas importar.
   - Haz clic en **Importar**.

3. En la pestaña **Configuración**:
   - Cambia la ruta base de Ollama.
   - Guarda la configuración.
   - Refresca la lista de modelos.

## 📦 Compilar a ejecutable con PyInstaller

Si quieres generar un `.exe` para Windows, usa PyInstaller.

### 1. Instalar PyInstaller

```powershell
pip install pyinstaller>=6.0.0
```

> Si ya tienes un entorno virtual, asegúrate de que esté activado.

### 2. Compilar el ejecutable

Ejecuta este comando desde la carpeta del proyecto:

```powershell
pyinstaller --onefile --windowed ollama_model_manager_gui.py
```

#### Qué se genera

- `dist\ollama_model_manager_gui.exe` — ejecutable final
- `build\` — archivos temporales de compilación
- `ollama_model_manager_gui.spec` — archivo de configuración de PyInstaller

### 3. Ejecutar el exe generado

```powershell
cd dist
.	ollama_model_manager_gui.exe
```

### 4. Ajustes opcionales

- Si quieres un icono, añade `--icon=tu_icono.ico` al comando de PyInstaller:

```powershell
pyinstaller --onefile --windowed --icon=tu_icono.ico ollama_model_manager_gui.py
```

- Si quieres incluir datos adicionales o cambiar opciones de compilación, edita `ollama_model_manager_gui.spec`.

## ✅ Comandos rápidos

Instalar dependencias:

```powershell
pip install -r requirements.txt
```

Ejecutar en desarrollo:

```powershell
python ollama_model_manager_gui.py
```

Compilar exe:

```powershell
pyinstaller --onefile --windowed ollama_model_manager_gui.py
```

## ⚠️ Consejos y solución de problemas

- Si no aparecen modelos, revisa que la carpeta de Ollama tenga `manifests\registry.ollama.ai\library` y `blobs`.
- Si el instalador no encuentra `python`, asegúrate de que Python esté en la variable `PATH`.
- Si PyInstaller falla, activa el entorno virtual y vuelve a instalar `pyinstaller`.
- Si la app no inicia, usa la terminal para ver errores completos.

## 📚 Notas finales

- El proyecto está pensado para funcionar sobre la instalación local de Ollama.
- Los modelos exportados se guardan como archivos `.tar` con manifiestos y blobs.
- La importación copia manifiestos y blobs dentro de la ruta de Ollama.

¡Listo! Ahora tienes el flujo completo para instalar, usar y compilar este proyecto desde cero.
