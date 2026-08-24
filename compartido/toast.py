# Archivo: toast.py
# Ruta: compartido/toast.py
# Uso: from compartido.toast import Toast
import tkinter as tk


class Toast:
    """Sistema centralizado de notificaciones toast para AutomaPro"""

    COLOR_INFO        = "#1a73e8"
    COLOR_EXITO       = "#28a745"
    COLOR_ADVERTENCIA = "#e65100"
    COLOR_ERROR       = "#dc3545"

    ICONO_INFO        = "ℹ️"
    ICONO_EXITO       = "☑"
    ICONO_ADVERTENCIA = "⚠"
    ICONO_ERROR       = "✕"

    @staticmethod
    def info(root, mensaje, duracion=4000):
        Toast._mostrar(root, mensaje, duracion, Toast.COLOR_INFO, Toast.ICONO_INFO)

    @staticmethod
    def exito(root, mensaje, duracion=4000):
        Toast._mostrar(root, mensaje, duracion, Toast.COLOR_EXITO, Toast.ICONO_EXITO)

    @staticmethod
    def advertencia(root, mensaje, duracion=5000):
        Toast._mostrar(root, mensaje, duracion, Toast.COLOR_ADVERTENCIA, Toast.ICONO_ADVERTENCIA)

    @staticmethod
    def error(root, mensaje, duracion=5000):
        Toast._mostrar(root, mensaje, duracion, Toast.COLOR_ERROR, Toast.ICONO_ERROR)

    @staticmethod
    def _mostrar(root, mensaje, duracion, color, icono):
        try:
            # Separar título y subtítulo si el mensaje tiene salto de línea
            partes = mensaje.split('\n', 1)
            titulo = partes[0].strip()
            subtitulo = partes[1].strip() if len(partes) > 1 else None

            toast = tk.Toplevel(root)
            toast.overrideredirect(True)
            toast.attributes('-topmost', True)

            ancho = 420
            alto = 90 if not subtitulo else 110

            frame = tk.Frame(toast, bg=color, padx=20, pady=12)
            frame.pack(fill='both', expand=True)

            # Línea superior: icono + título
            frame_titulo = tk.Frame(frame, bg=color)
            frame_titulo.pack()

            tk.Label(
                frame_titulo,
                text=icono,
                font=("Segoe UI", 13),
                bg=color,
                fg="white"
            ).pack(side='left', padx=(0, 6))

            tk.Label(
                frame_titulo,
                text=titulo,
                font=("Segoe UI", 11, "bold"),
                bg=color,
                fg="white"
            ).pack(side='left')

            # Subtítulo si existe
            if subtitulo:
                tk.Label(
                    frame,
                    text=subtitulo,
                    font=("Segoe UI", 9),
                    bg=color,
                    fg="#e0ffe0" if color == Toast.COLOR_EXITO else "white",
                    wraplength=ancho - 40,
                    justify='center'
                ).pack(pady=(4, 0))

            toast.update_idletasks()
            x = root.winfo_screenwidth() - ancho - 20
            y = root.winfo_screenheight() - alto - 60
            toast.geometry(f'{ancho}x{alto}+{x}+{y}')

            toast.after(duracion, toast.destroy)
            frame.bind('<Button-1>', lambda e: toast.destroy())

        except Exception:
            pass