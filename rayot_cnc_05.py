import tkinter as tk
from tkinter import filedialog, messagebox
import re
import math

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ==========================================
# CONFIGURACION
# ==========================================
LIMITE_X = 280.0
LIMITE_Y = 160.0
TOLERANCIA_SELECCION = 6.0


class RayoTCNC:
    def __init__(self, root):
        self.root = root
        self.root.title("RayoT CNC - Versión 0.7")
        self.root.geometry("1280x900")
        self.root.configure(bg="#20252b")

        self.rectangulos = []
        self.circulos = []
        self.lineas = []  # Cada línea: (x1, y1, x2, y2)
        self.rapidos = []
        self.cortes = []
        self.fuera_limite = False

        self.seleccionado = None
        self.arrastrando = False
        self.posicion_inicial = None
        self.mouse_inicial = None

        self.artistas_rectangulos = []
        self.artistas_circulos = []
        self.artistas_lineas = []
        self.textos_rectangulos = []
        self.textos_circulos = []
        self.textos_lineas = []

        self.paso_var = tk.IntVar(value=10)
        self.snap_var = tk.BooleanVar(value=False)

        # Estado para dibujar una línea haciendo dos clics.
        self.modo_linea = False
        self.primer_punto_linea = None
        self.marca_primer_punto = None

        tk.Label(
            root, text="RayoT CNC", font=("Arial", 24, "bold"),
            fg="white", bg="#20252b"
        ).pack(pady=6)

        tk.Label(
            root, text="Área de trabajo: X = 280 mm | Y = 160 mm",
            font=("Arial", 12), fg="#65d6ad", bg="#20252b"
        ).pack(pady=3)

        # Barra principal
        barra = tk.Frame(root, bg="#20252b")
        barra.pack(pady=6)

        tk.Button(
            barra, text="ABRIR G-CODE", bg="#168aad", fg="white",
            command=self.abrir_archivo
        ).grid(row=0, column=0, padx=5)

        tk.Button(
            barra, text="ACTUALIZAR SELECCIONADO", bg="#168aad",
            fg="white", command=self.actualizar_figura
        ).grid(row=0, column=1, padx=5)

        tk.Button(
            barra, text="ELIMINAR SELECCIONADO", bg="#d97706",
            fg="white", command=self.eliminar_seleccionado
        ).grid(row=0, column=2, padx=5)

        tk.Button(
            barra, text="CANCELAR LÍNEA", bg="#6c757d", fg="white",
            command=self.cancelar_linea
        ).grid(row=0, column=3, padx=5)

        tk.Button(
            barra, text="LIMPIAR TODO", bg="#b23a48", fg="white",
            command=self.limpiar_todo
        ).grid(row=0, column=4, padx=5)

        # Cuadrícula
        panel_grid = tk.LabelFrame(
            root, text="Configuración de diseño", fg="white",
            bg="#20252b", padx=10, pady=6
        )
        panel_grid.pack(pady=5)

        tk.Label(
            panel_grid, text="Paso de cuadrícula:", fg="white",
            bg="#20252b"
        ).grid(row=0, column=0, padx=5)

        selector_grid = tk.OptionMenu(
            panel_grid, self.paso_var, 1, 5, 10,
            command=self.cambiar_cuadricula
        )
        selector_grid.config(bg="#168aad", fg="white", width=8)
        selector_grid.grid(row=0, column=1, padx=5)

        tk.Label(
            panel_grid, text="mm", fg="white", bg="#20252b"
        ).grid(row=0, column=2, padx=2)

        tk.Checkbutton(
            panel_grid, text="Ajustar figuras a la cuadrícula",
            variable=self.snap_var, fg="white", bg="#20252b",
            selectcolor="#303840", activebackground="#20252b",
            activeforeground="white"
        ).grid(row=0, column=3, padx=15)

        # Rectángulo
        panel_rect = tk.LabelFrame(
            root, text="Herramienta: Rectángulo", fg="white",
            bg="#20252b", padx=8, pady=6
        )
        panel_rect.pack(pady=5)

        self.pos_x = self.crear_campo(panel_rect, "Posición X:", "0", 0)
        self.pos_y = self.crear_campo(panel_rect, "Posición Y:", "0", 2)
        self.ancho_rect = self.crear_campo(panel_rect, "Ancho X:", "100", 4)
        self.alto_rect = self.crear_campo(panel_rect, "Alto Y:", "50", 6)

        tk.Button(
            panel_rect, text="AGREGAR RECTÁNGULO", bg="#168aad",
            fg="white", command=self.dibujar_rectangulo
        ).grid(row=0, column=8, padx=8)

        # Círculo
        panel_circulo = tk.LabelFrame(
            root, text="Herramienta: Círculo", fg="white",
            bg="#20252b", padx=8, pady=6
        )
        panel_circulo.pack(pady=5)

        self.centro_x = self.crear_campo(panel_circulo, "Centro X:", "140", 0)
        self.centro_y = self.crear_campo(panel_circulo, "Centro Y:", "80", 2)
        self.diametro = self.crear_campo(panel_circulo, "Diámetro:", "40", 4)

        tk.Button(
            panel_circulo, text="AGREGAR CÍRCULO", bg="#168aad",
            fg="white", command=self.dibujar_circulo
        ).grid(row=0, column=6, padx=8)

        # Línea
        panel_linea = tk.LabelFrame(
            root, text="Herramienta: Línea", fg="white",
            bg="#20252b", padx=8, pady=6
        )
        panel_linea.pack(pady=5)

        self.linea_x1 = self.crear_campo(panel_linea, "Inicio X:", "20", 0)
        self.linea_y1 = self.crear_campo(panel_linea, "Inicio Y:", "20", 2)
        self.linea_x2 = self.crear_campo(panel_linea, "Final X:", "80", 4)
        self.linea_y2 = self.crear_campo(panel_linea, "Final Y:", "60", 6)

        tk.Button(
            panel_linea, text="AGREGAR POR COORDENADAS",
            bg="#168aad", fg="white", command=self.agregar_linea_coordenadas
        ).grid(row=0, column=8, padx=5)

        tk.Button(
            panel_linea, text="DIBUJAR CON EL RATÓN",
            bg="#168aad", fg="white", command=self.activar_modo_linea
        ).grid(row=0, column=9, padx=5)

        # Gráfica
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.fig.subplots_adjust(left=0.07, right=0.98, top=0.94, bottom=0.09)

        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack(
            fill=tk.BOTH, expand=True, padx=15, pady=5
        )

        self.canvas.mpl_connect("button_press_event", self.seleccionar_figura)
        self.canvas.mpl_connect("motion_notify_event", self.mover_figura)
        self.canvas.mpl_connect("button_release_event", self.soltar_figura)

        self.info = tk.Label(
            root, text="Esperando diseño...", font=("Arial", 11, "bold"),
            fg="white", bg="#20252b"
        )
        self.info.pack(pady=4)

        self.estado = tk.Label(
            root, text="Estado: esperando diseño",
            font=("Arial", 12, "bold"), fg="#65d6ad", bg="#20252b"
        )
        self.estado.pack(pady=6)

        self.dibujar()

    # ======================================
    # UTILIDADES DE INTERFAZ
    # ======================================
    def crear_campo(self, panel, etiqueta, valor, columna):
        tk.Label(
            panel, text=etiqueta, fg="white", bg="#20252b"
        ).grid(row=0, column=columna, padx=4)
        campo = tk.Entry(panel, width=8)
        campo.insert(0, valor)
        campo.grid(row=0, column=columna + 1, padx=4)
        return campo

    def colocar_valor(self, campo, valor):
        campo.delete(0, tk.END)
        campo.insert(0, f"{valor:.3f}".rstrip("0").rstrip("."))

    def ajustar_cuadricula(self, valor):
        if not self.snap_var.get():
            return valor
        paso = self.paso_var.get()
        return round(valor / paso) * paso

    def cambiar_cuadricula(self, valor=None):
        self.dibujar()
        self.estado.config(
            text=f"CUADRÍCULA: {self.paso_var.get()} mm",
            fg="#65d6ad"
        )

    def actualizar_informacion(self):
        self.info.config(
            text=(
                f"Rectángulos: {len(self.rectangulos)} | "
                f"Círculos: {len(self.circulos)} | "
                f"Líneas: {len(self.lineas)} | "
                f"Movimientos rápidos: {len(self.rapidos)} | "
                f"Cortes: {len(self.cortes)}"
            )
        )

    def esta_fuera(self, x, y):
        return x < 0 or x > LIMITE_X or y < 0 or y > LIMITE_Y

    def validar_punto(self, x, y):
        return 0 <= x <= LIMITE_X and 0 <= y <= LIMITE_Y

    # ======================================
    # SELECCIÓN Y CARGA DE COORDENADAS
    # ======================================
    def cargar_datos_seleccion(self):
        if self.seleccionado is None:
            return

        tipo, indice = self.seleccionado

        if tipo == "rectangulo":
            x, y, ancho, alto = self.rectangulos[indice]
            for campo, valor in (
                (self.pos_x, x), (self.pos_y, y),
                (self.ancho_rect, ancho), (self.alto_rect, alto)
            ):
                self.colocar_valor(campo, valor)

        elif tipo == "circulo":
            x, y, diametro = self.circulos[indice]
            for campo, valor in (
                (self.centro_x, x), (self.centro_y, y),
                (self.diametro, diametro)
            ):
                self.colocar_valor(campo, valor)

        elif tipo == "linea":
            x1, y1, x2, y2 = self.lineas[indice]
            for campo, valor in (
                (self.linea_x1, x1), (self.linea_y1, y1),
                (self.linea_x2, x2), (self.linea_y2, y2)
            ):
                self.colocar_valor(campo, valor)

    # ======================================
    # LÍNEAS: CREAR POR COORDENADAS O RATÓN
    # ======================================
    def agregar_linea_coordenadas(self):
        try:
            x1, y1, x2, y2 = (
                float(self.linea_x1.get()),
                float(self.linea_y1.get()),
                float(self.linea_x2.get()),
                float(self.linea_y2.get())
            )
            if not all(math.isfinite(v) for v in (x1, y1, x2, y2)):
                raise ValueError("Introduce coordenadas numéricas válidas.")

            x1, y1, x2, y2 = (
                self.ajustar_cuadricula(x1),
                self.ajustar_cuadricula(y1),
                self.ajustar_cuadricula(x2),
                self.ajustar_cuadricula(y2)
            )

            if not all(self.validar_punto(x, y) for x, y in ((x1, y1), (x2, y2))):
                raise ValueError("La línea debe estar dentro del área X=280, Y=160.")

            if math.hypot(x2 - x1, y2 - y1) < 0.001:
                raise ValueError("El punto inicial y final no pueden ser iguales.")

            self.cancelar_linea(silencioso=True)
            self.lineas.append((x1, y1, x2, y2))
            self.seleccionado = ("linea", len(self.lineas) - 1)
            self.dibujar()
            self.cargar_datos_seleccion()
            self.estado.config(text="LÍNEA AGREGADA", fg="#65d6ad")

        except ValueError as error:
            messagebox.showerror("Datos incorrectos", str(error))

    def activar_modo_linea(self):
        self.cancelar_linea(silencioso=True)
        self.modo_linea = True
        self.primer_punto_linea = None
        self.seleccionado = None
        self.arrastrando = False
        self.actualizar_seleccion()
        self.estado.config(
            text="MODO LÍNEA: haz clic en el punto inicial",
            fg="#65d6ad"
        )

    def cancelar_linea(self, silencioso=False):
        self.modo_linea = False
        self.primer_punto_linea = None
        if self.marca_primer_punto is not None:
            try:
                self.marca_primer_punto.remove()
            except ValueError:
                pass
            self.marca_primer_punto = None
            self.canvas.draw_idle()
        if not silencioso:
            self.estado.config(text="Dibujo de línea cancelado", fg="#65d6ad")

    def clic_para_linea(self, event):
        if event.inaxes != self.ax or event.xdata is None or event.ydata is None:
            return

        x = self.ajustar_cuadricula(float(event.xdata))
        y = self.ajustar_cuadricula(float(event.ydata))

        if not self.validar_punto(x, y):
            self.estado.config(text="Punto fuera del área de trabajo", fg="#ff5555")
            return

        if self.primer_punto_linea is None:
            self.primer_punto_linea = (x, y)
            self.marca_primer_punto, = self.ax.plot(
                [x], [y], marker="o", color="#ff8800",
                markersize=7, linestyle="None"
            )
            self.canvas.draw_idle()
            self.estado.config(
                text=f"Inicio: X={x:g}, Y={y:g}. Ahora haz clic en el punto final",
                fg="#65d6ad"
            )
            return

        x1, y1 = self.primer_punto_linea
        if math.hypot(x - x1, y - y1) < 0.001:
            self.estado.config(text="El punto final debe ser diferente", fg="#ff5555")
            return

        self.cancelar_linea(silencioso=True)
        self.lineas.append((x1, y1, x, y))
        self.seleccionado = ("linea", len(self.lineas) - 1)
        self.dibujar()
        self.cargar_datos_seleccion()
        self.estado.config(text="LÍNEA CREADA CORRECTAMENTE", fg="#65d6ad")

    # ======================================
    # ABRIR G-CODE
    # ======================================
    def abrir_archivo(self):
        archivo = filedialog.askopenfilename(
            filetypes=[
                ("Archivos CNC", "*.nc *.gcode *.txt"),
                ("Todos los archivos", "*.*")
            ]
        )
        if not archivo:
            return

        try:
            with open(archivo, "r", encoding="utf-8", errors="ignore") as f:
                codigo = f.readlines()

            self.rectangulos = []
            self.circulos = []
            self.lineas = []
            self.seleccionado = None
            self.arrastrando = False
            self.cancelar_linea(silencioso=True)
            self.procesar_gcode(codigo)

        except Exception as error:
            messagebox.showerror("Error", str(error))

    # ======================================
    # LIMPIAR TODO
    # ======================================
    def limpiar_todo(self):
        self.rectangulos = []
        self.circulos = []
        self.lineas = []
        self.rapidos = []
        self.cortes = []
        self.fuera_limite = False
        self.seleccionado = None
        self.arrastrando = False
        self.cancelar_linea(silencioso=True)
        self.dibujar()
        self.estado.config(text="DISEÑO LIMPIADO", fg="#65d6ad")

    # ======================================
    # PROCESAR G-CODE (VISUALIZACIÓN BÁSICA)
    # ======================================
    def procesar_gcode(self, lineas):
        self.rapidos = []
        self.cortes = []
        self.fuera_limite = False

        x, y, z = 0.0, 0.0, 0.0
        movimiento = None
        absoluto = True
        escala = 1.0

        for linea in lineas:
            linea = re.sub(r"\([^)]*\)", "", linea)
            linea = linea.split(";")[0].upper()
            palabras = re.findall(r"([A-Z])\s*(-?\d+(?:\.\d+)?)", linea)
            datos = {}

            for letra, valor in palabras:
                valor = float(valor)
                if letra == "G":
                    if valor == 90:
                        absoluto = True
                    elif valor == 91:
                        absoluto = False
                    elif valor == 20:
                        escala = 25.4
                    elif valor == 21:
                        escala = 1.0
                    elif valor in (0, 1, 2, 3):
                        movimiento = int(valor)
                else:
                    datos[letra] = valor

            if movimiento is None:
                continue

            xi, yi = x, y
            if "X" in datos:
                valor = datos["X"] * escala
                x = valor if absoluto else x + valor
            if "Y" in datos:
                valor = datos["Y"] * escala
                y = valor if absoluto else y + valor
            if "Z" in datos:
                valor = datos["Z"] * escala
                z = valor if absoluto else z + valor

            if movimiento in (0, 1):
                if (xi, yi) != (x, y):
                    puntos = [(xi, yi), (x, y)]
                    fuera = any(self.esta_fuera(px, py) for px, py in puntos)
                    if fuera:
                        self.fuera_limite = True
                    if movimiento == 0:
                        self.rapidos.append((puntos, fuera))
                    else:
                        self.cortes.append((puntos, fuera))

            elif movimiento in (2, 3):
                if "I" in datos or "J" in datos:
                    cx = xi + datos.get("I", 0) * escala
                    cy = yi + datos.get("J", 0) * escala
                    radio = math.hypot(xi - cx, yi - cy)
                    inicio = math.atan2(yi - cy, xi - cx)
                    final = math.atan2(y - cy, x - cx)
                    diferencia = final - inicio

                    if movimiento == 3:
                        while diferencia <= 0:
                            diferencia += 2 * math.pi
                    else:
                        while diferencia >= 0:
                            diferencia -= 2 * math.pi

                    puntos = []
                    for i in range(81):
                        angulo = inicio + diferencia * i / 80
                        puntos.append((
                            cx + radio * math.cos(angulo),
                            cy + radio * math.sin(angulo)
                        ))
                    puntos[0] = (xi, yi)
                    puntos[-1] = (x, y)

                    fuera = any(self.esta_fuera(px, py) for px, py in puntos)
                    if fuera:
                        self.fuera_limite = True
                    self.cortes.append((puntos, fuera))
                else:
                    self.fuera_limite = True

        self.dibujar()
        if self.fuera_limite:
            self.estado.config(text="ADVERTENCIA: G-CODE FUERA DE LÍMITES", fg="#ff5555")
        else:
            self.estado.config(text="G-CODE CARGADO", fg="#65d6ad")

    # ======================================
    # AGREGAR RECTÁNGULO
    # ======================================
    def dibujar_rectangulo(self):
        try:
            x = float(self.pos_x.get())
            y = float(self.pos_y.get())
            ancho = float(self.ancho_rect.get())
            alto = float(self.alto_rect.get())

            if not all(math.isfinite(v) for v in (x, y, ancho, alto)):
                raise ValueError("Introduce números válidos.")
            if ancho <= 0 or alto <= 0:
                raise ValueError("Ancho y alto deben ser mayores que cero.")

            x = self.ajustar_cuadricula(x)
            y = self.ajustar_cuadricula(y)
            ancho = self.ajustar_cuadricula(ancho)
            alto = self.ajustar_cuadricula(alto)

            if ancho <= 0 or alto <= 0:
                raise ValueError("Las dimensiones ajustadas deben ser mayores que cero.")
            if x < 0 or y < 0:
                raise ValueError("Las posiciones no pueden ser negativas.")
            if x + ancho > LIMITE_X or y + alto > LIMITE_Y:
                messagebox.showwarning("Fuera de límites", "El rectángulo excede el área de trabajo.")
                return

            self.cancelar_linea(silencioso=True)
            self.rectangulos.append((x, y, ancho, alto))
            self.seleccionado = ("rectangulo", len(self.rectangulos) - 1)
            self.dibujar()
            self.cargar_datos_seleccion()
            self.estado.config(text="RECTÁNGULO AGREGADO", fg="#65d6ad")

        except ValueError as error:
            messagebox.showerror("Datos incorrectos", str(error))

    # ======================================
    # AGREGAR CÍRCULO
    # ======================================
    def dibujar_circulo(self):
        try:
            x = float(self.centro_x.get())
            y = float(self.centro_y.get())
            diametro = float(self.diametro.get())

            if not all(math.isfinite(v) for v in (x, y, diametro)):
                raise ValueError("Introduce números válidos.")
            if diametro <= 0:
                raise ValueError("El diámetro debe ser mayor que cero.")

            x = self.ajustar_cuadricula(x)
            y = self.ajustar_cuadricula(y)
            diametro = self.ajustar_cuadricula(diametro)

            if diametro <= 0:
                raise ValueError("El diámetro ajustado debe ser mayor que cero.")

            radio = diametro / 2
            if (
                x - radio < 0 or x + radio > LIMITE_X
                or y - radio < 0 or y + radio > LIMITE_Y
            ):
                messagebox.showwarning("Fuera de límites", "El círculo excede el área de trabajo.")
                return

            self.cancelar_linea(silencioso=True)
            self.circulos.append((x, y, diametro))
            self.seleccionado = ("circulo", len(self.circulos) - 1)
            self.dibujar()
            self.cargar_datos_seleccion()
            self.estado.config(text="CÍRCULO AGREGADO", fg="#65d6ad")

        except ValueError as error:
            messagebox.showerror("Datos incorrectos", str(error))

    # ======================================
    # ACTUALIZAR FIGURA SELECCIONADA
    # ======================================
    def actualizar_figura(self):
        if self.seleccionado is None:
            messagebox.showinfo("Editar figura", "Primero selecciona una figura.")
            return

        try:
            tipo, indice = self.seleccionado

            if tipo == "rectangulo":
                x, y, ancho, alto = (
                    float(self.pos_x.get()), float(self.pos_y.get()),
                    float(self.ancho_rect.get()), float(self.alto_rect.get())
                )
                if not all(math.isfinite(v) for v in (x, y, ancho, alto)):
                    raise ValueError("Introduce números válidos.")
                if ancho <= 0 or alto <= 0:
                    raise ValueError("Ancho y alto deben ser mayores que cero.")

                x, y = self.ajustar_cuadricula(x), self.ajustar_cuadricula(y)
                ancho, alto = self.ajustar_cuadricula(ancho), self.ajustar_cuadricula(alto)
                if ancho <= 0 or alto <= 0 or x < 0 or y < 0 or x + ancho > LIMITE_X or y + alto > LIMITE_Y:
                    raise ValueError("El rectángulo tiene dimensiones o posición fuera de límites.")
                self.rectangulos[indice] = (x, y, ancho, alto)

            elif tipo == "circulo":
                x, y, diametro = (
                    float(self.centro_x.get()), float(self.centro_y.get()),
                    float(self.diametro.get())
                )
                if not all(math.isfinite(v) for v in (x, y, diametro)):
                    raise ValueError("Introduce números válidos.")
                if diametro <= 0:
                    raise ValueError("El diámetro debe ser mayor que cero.")
                x, y = self.ajustar_cuadricula(x), self.ajustar_cuadricula(y)
                diametro = self.ajustar_cuadricula(diametro)
                radio = diametro / 2
                if diametro <= 0 or x - radio < 0 or x + radio > LIMITE_X or y - radio < 0 or y + radio > LIMITE_Y:
                    raise ValueError("El círculo excede el área de trabajo.")
                self.circulos[indice] = (x, y, diametro)

            elif tipo == "linea":
                x1, y1, x2, y2 = (
                    float(self.linea_x1.get()), float(self.linea_y1.get()),
                    float(self.linea_x2.get()), float(self.linea_y2.get())
                )
                if not all(math.isfinite(v) for v in (x1, y1, x2, y2)):
                    raise ValueError("Introduce coordenadas numéricas válidas.")
                x1, y1, x2, y2 = (
                    self.ajustar_cuadricula(x1), self.ajustar_cuadricula(y1),
                    self.ajustar_cuadricula(x2), self.ajustar_cuadricula(y2)
                )
                if not all(self.validar_punto(x, y) for x, y in ((x1, y1), (x2, y2))):
                    raise ValueError("La línea debe estar dentro del área de trabajo.")
                if math.hypot(x2 - x1, y2 - y1) < 0.001:
                    raise ValueError("Los extremos de la línea no pueden coincidir.")
                self.lineas[indice] = (x1, y1, x2, y2)

            self.dibujar()
            self.cargar_datos_seleccion()
            self.estado.config(text="FIGURA ACTUALIZADA CORRECTAMENTE", fg="#65d6ad")

        except ValueError as error:
            messagebox.showerror("No se pudo actualizar", str(error))

    # ======================================
    # ESTILO Y SELECCIÓN
    # ======================================
    def actualizar_seleccion(self):
        for i, artista in enumerate(self.artistas_rectangulos):
            seleccionado = self.seleccionado == ("rectangulo", i)
            artista.set_color("#ff00ff" if seleccionado else "cyan")
            artista.set_linewidth(3.5 if seleccionado else 2.5)

        for i, artista in enumerate(self.artistas_circulos):
            seleccionado = self.seleccionado == ("circulo", i)
            artista.set_color("#ff00ff" if seleccionado else "yellow")
            artista.set_linewidth(3.5 if seleccionado else 2.5)

        for i, artista in enumerate(self.artistas_lineas):
            seleccionado = self.seleccionado == ("linea", i)
            artista.set_color("#ff00ff" if seleccionado else "#ff8800")
            artista.set_linewidth(3.5 if seleccionado else 2.5)

        self.canvas.draw_idle()

    @staticmethod
    def distancia_punto_segmento(px, py, x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        longitud2 = dx * dx + dy * dy
        if longitud2 == 0:
            return math.hypot(px - x1, py - y1)
        t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / longitud2))
        proy_x, proy_y = x1 + t * dx, y1 + t * dy
        return math.hypot(px - proy_x, py - proy_y)

    def seleccionar_figura(self, event):
        if event.inaxes != self.ax or event.button != 1:
            return
        if event.xdata is None or event.ydata is None:
            return

        if self.modo_linea:
            self.clic_para_linea(event)
            return

        mx, my = event.xdata, event.ydata
        candidatos = []

        for i, (x, y, ancho, alto) in enumerate(self.rectangulos):
            dentro = x <= mx <= x + ancho and y <= my <= y + alto
            if dentro:
                distancia = min(
                    abs(mx - x), abs(mx - (x + ancho)),
                    abs(my - y), abs(my - (y + alto))
                )
            else:
                dx = max(x - mx, 0, mx - (x + ancho))
                dy = max(y - my, 0, my - (y + alto))
                distancia = math.hypot(dx, dy)
            if distancia <= TOLERANCIA_SELECCION:
                candidatos.append((distancia, "rectangulo", i))

        for i, (x, y, diametro) in enumerate(self.circulos):
            distancia = abs(math.hypot(mx - x, my - y) - diametro / 2)
            if distancia <= TOLERANCIA_SELECCION:
                candidatos.append((distancia, "circulo", i))

        for i, (x1, y1, x2, y2) in enumerate(self.lineas):
            distancia = self.distancia_punto_segmento(mx, my, x1, y1, x2, y2)
            if distancia <= TOLERANCIA_SELECCION:
                candidatos.append((distancia, "linea", i))

        seleccion_anterior = self.seleccionado

        if candidatos:
            candidatos.sort(key=lambda item: item[0])
            _, tipo, indice = candidatos[0]
            self.seleccionado = (tipo, indice)
            self.arrastrando = True
            self.mouse_inicial = (mx, my)

            if tipo == "rectangulo":
                self.posicion_inicial = self.rectangulos[indice]
            elif tipo == "circulo":
                self.posicion_inicial = self.circulos[indice]
            else:
                self.posicion_inicial = self.lineas[indice]

            self.cargar_datos_seleccion()
            self.estado.config(text=f"SELECCIONADO: {tipo.upper()}", fg="#ff55ff")
        else:
            self.seleccionado = None
            self.arrastrando = False
            self.posicion_inicial = None
            self.mouse_inicial = None
            self.estado.config(text="Ninguna figura seleccionada", fg="#65d6ad")

        if seleccion_anterior != self.seleccionado:
            self.actualizar_seleccion()

    # ======================================
    # MOVER FIGURAS CON EL RATÓN
    # ======================================
    def mover_figura(self, event):
        if not self.arrastrando or self.seleccionado is None:
            return
        if event.inaxes != self.ax or event.xdata is None or event.ydata is None:
            return
        if self.mouse_inicial is None:
            return

        mx, my = event.xdata, event.ydata
        dx, dy = mx - self.mouse_inicial[0], my - self.mouse_inicial[1]
        tipo, indice = self.seleccionado

        if tipo == "rectangulo":
            x0, y0, ancho, alto = self.posicion_inicial
            nuevo_x = self.ajustar_cuadricula(x0 + dx)
            nuevo_y = self.ajustar_cuadricula(y0 + dy)
            nuevo_x = max(0, min(LIMITE_X - ancho, nuevo_x))
            nuevo_y = max(0, min(LIMITE_Y - alto, nuevo_y))
            self.rectangulos[indice] = (nuevo_x, nuevo_y, ancho, alto)

            self.artistas_rectangulos[indice].set_data(
                [nuevo_x, nuevo_x + ancho, nuevo_x + ancho, nuevo_x, nuevo_x],
                [nuevo_y, nuevo_y, nuevo_y + alto, nuevo_y + alto, nuevo_y]
            )
            texto_ancho, texto_alto = self.textos_rectangulos[indice]
            texto_ancho.set_position((nuevo_x + ancho / 2, nuevo_y + alto - 4))
            texto_alto.set_position((nuevo_x + 4, nuevo_y + alto / 2))

        elif tipo == "circulo":
            x0, y0, diametro = self.posicion_inicial
            radio = diametro / 2
            nuevo_x = self.ajustar_cuadricula(x0 + dx)
            nuevo_y = self.ajustar_cuadricula(y0 + dy)
            nuevo_x = max(radio, min(LIMITE_X - radio, nuevo_x))
            nuevo_y = max(radio, min(LIMITE_Y - radio, nuevo_y))
            self.circulos[indice] = (nuevo_x, nuevo_y, diametro)

            puntos_x, puntos_y = [], []
            for j in range(101):
                angulo = 2 * math.pi * j / 100
                puntos_x.append(nuevo_x + radio * math.cos(angulo))
                puntos_y.append(nuevo_y + radio * math.sin(angulo))
            self.artistas_circulos[indice].set_data(puntos_x, puntos_y)
            self.textos_circulos[indice].set_position(
                self.posicion_texto_circulo(nuevo_x, nuevo_y, radio)
            )

        elif tipo == "linea":
            x1, y1, x2, y2 = self.posicion_inicial
            nuevo_x1 = self.ajustar_cuadricula(x1 + dx)
            nuevo_y1 = self.ajustar_cuadricula(y1 + dy)
            nuevo_x2 = self.ajustar_cuadricula(x2 + dx)
            nuevo_y2 = self.ajustar_cuadricula(y2 + dy)

            # Desplazamiento conjunto: conservar la longitud y orientación.
            despl_x = nuevo_x1 - x1
            despl_y = nuevo_y1 - y1
            minimo_x = min(x1, x2) + despl_x
            maximo_x = max(x1, x2) + despl_x
            minimo_y = min(y1, y2) + despl_y
            maximo_y = max(y1, y2) + despl_y

            if minimo_x < 0:
                despl_x -= minimo_x
            if maximo_x > LIMITE_X:
                despl_x -= maximo_x - LIMITE_X
            if minimo_y < 0:
                despl_y -= minimo_y
            if maximo_y > LIMITE_Y:
                despl_y -= maximo_y - LIMITE_Y

            nuevo_x1, nuevo_y1 = x1 + despl_x, y1 + despl_y
            nuevo_x2, nuevo_y2 = x2 + despl_x, y2 + despl_y
            self.lineas[indice] = (nuevo_x1, nuevo_y1, nuevo_x2, nuevo_y2)
            self.artistas_lineas[indice].set_data(
                [nuevo_x1, nuevo_x2], [nuevo_y1, nuevo_y2]
            )
            self.textos_lineas[indice].set_position(
                ((nuevo_x1 + nuevo_x2) / 2, (nuevo_y1 + nuevo_y2) / 2)
            )

        self.canvas.draw_idle()

    def posicion_texto_circulo(self, x, y, radio):
        if y + radio + 4 <= LIMITE_Y:
            return (x, y + radio + 4)
        return (x, y - radio - 5)

    def soltar_figura(self, event):
        self.arrastrando = False
        if self.seleccionado is not None:
            self.cargar_datos_seleccion()
            self.estado.config(text="FIGURA SELECCIONADA", fg="#ff55ff")

    # ======================================
    # ELIMINAR FIGURA
    # ======================================
    def eliminar_seleccionado(self):
        if self.seleccionado is None:
            messagebox.showinfo("Eliminar figura", "Primero selecciona una figura con el ratón.")
            return

        tipo, indice = self.seleccionado
        if tipo == "rectangulo":
            del self.rectangulos[indice]
        elif tipo == "circulo":
            del self.circulos[indice]
        elif tipo == "linea":
            del self.lineas[indice]

        self.seleccionado = None
        self.arrastrando = False
        self.dibujar()
        self.estado.config(text="FIGURA ELIMINADA", fg="#65d6ad")

    # ======================================
    # DIBUJAR GRÁFICA
    # ======================================
    def dibujar(self):
        self.ax.clear()
        self.artistas_rectangulos = []
        self.artistas_circulos = []
        self.artistas_lineas = []
        self.textos_rectangulos = []
        self.textos_circulos = []
        self.textos_lineas = []

        self.ax.set_title("RayoT CNC - Área de diseño", fontsize=14)
        self.ax.set_xlabel("Eje X (mm)")
        self.ax.set_ylabel("Eje Y (mm)")
        self.ax.set_xlim(0, LIMITE_X)
        self.ax.set_ylim(0, LIMITE_Y)

        paso = self.paso_var.get()
        self.ax.set_xticks(range(0, int(LIMITE_X) + 1, paso))
        self.ax.set_yticks(range(0, int(LIMITE_Y) + 1, paso))
        self.ax.grid(True, linestyle=":", linewidth=0.7, alpha=0.6)
        self.ax.set_aspect("equal", adjustable="box")

        # Borde del área de diseño
        self.ax.plot(
            [0, LIMITE_X, LIMITE_X, 0, 0],
            [0, 0, LIMITE_Y, LIMITE_Y, 0],
            color="green", linewidth=2
        )

        # Rectángulos y etiquetas
        for i, (x, y, ancho, alto) in enumerate(self.rectangulos):
            seleccionado = self.seleccionado == ("rectangulo", i)
            artista, = self.ax.plot(
                [x, x + ancho, x + ancho, x, x],
                [y, y, y + alto, y + alto, y],
                color="#ff00ff" if seleccionado else "cyan",
                linewidth=3.5 if seleccionado else 2.5
            )
            self.artistas_rectangulos.append(artista)

            texto_ancho = self.ax.text(
                x + ancho / 2, y + alto - 4, f"{ancho:g} mm",
                color="white", fontsize=8, ha="center", va="top",
                bbox=dict(facecolor="#20252b", alpha=0.75, edgecolor="none", pad=2)
            )
            texto_alto = self.ax.text(
                x + 4, y + alto / 2, f"{alto:g} mm",
                color="white", fontsize=8, ha="left", va="center", rotation=90,
                bbox=dict(facecolor="#20252b", alpha=0.75, edgecolor="none", pad=2)
            )
            self.textos_rectangulos.append((texto_ancho, texto_alto))

        # Círculos y etiquetas
        for i, (x, y, diametro) in enumerate(self.circulos):
            radio = diametro / 2
            seleccionado = self.seleccionado == ("circulo", i)
            puntos_x, puntos_y = [], []
            for j in range(101):
                angulo = 2 * math.pi * j / 100
                puntos_x.append(x + radio * math.cos(angulo))
                puntos_y.append(y + radio * math.sin(angulo))

            artista, = self.ax.plot(
                puntos_x, puntos_y,
                color="#ff00ff" if seleccionado else "yellow",
                linewidth=3.5 if seleccionado else 2.5
            )
            self.artistas_circulos.append(artista)

            texto = self.ax.text(
                *self.posicion_texto_circulo(x, y, radio),
                f"Ø {diametro:g} mm", color="white", fontsize=8,
                ha="center", va="center",
                bbox=dict(facecolor="#20252b", alpha=0.75, edgecolor="none", pad=2)
            )
            self.textos_circulos.append(texto)

        # Líneas y etiquetas de longitud
        for i, (x1, y1, x2, y2) in enumerate(self.lineas):
            seleccionado = self.seleccionado == ("linea", i)
            artista, = self.ax.plot(
                [x1, x2], [y1, y2],
                color="#ff00ff" if seleccionado else "#ff8800",
                linewidth=3.5 if seleccionado else 2.5,
                marker="o", markersize=3
            )
            self.artistas_lineas.append(artista)

            longitud = math.hypot(x2 - x1, y2 - y1)
            texto = self.ax.text(
                (x1 + x2) / 2, (y1 + y2) / 2,
                f"{longitud:.2f} mm", color="white", fontsize=8,
                ha="center", va="bottom",
                bbox=dict(facecolor="#20252b", alpha=0.75, edgecolor="none", pad=2)
            )
            self.textos_lineas.append(texto)

        # Movimientos rápidos y cortes importados
        for puntos, fuera in self.rapidos:
            self.ax.plot(
                [p[0] for p in puntos], [p[1] for p in puntos],
                color="red" if fuera else "gray",
                linestyle="--", linewidth=1
            )

        for puntos, fuera in self.cortes:
            self.ax.plot(
                [p[0] for p in puntos], [p[1] for p in puntos],
                color="red" if fuera else "blue", linewidth=1.6
            )

        # Leyenda
        self.ax.plot([], [], color="gray", linestyle="--", label="Movimiento rápido")
        self.ax.plot([], [], color="blue", label="Movimiento de corte")
        if self.rectangulos:
            self.ax.plot([], [], color="cyan", label="Rectángulos")
        if self.circulos:
            self.ax.plot([], [], color="yellow", label="Círculos")
        if self.lineas:
            self.ax.plot([], [], color="#ff8800", label="Líneas")
        if self.seleccionado is not None:
            self.ax.plot([], [], color="#ff00ff", linewidth=3, label="Seleccionado")

        self.ax.legend(loc="upper right", fontsize=8)
        self.actualizar_informacion()
        self.canvas.draw_idle()


# ==========================================
# INICIAR RAYOT CNC
# ==========================================
if __name__ == "__main__":
    ventana = tk.Tk()
    aplicacion = RayoTCNC(ventana)
    ventana.mainloop()
