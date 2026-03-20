"""
ClasificadorV2 — Clasificador de Archivos
v2 — Paleta oscura, previsualización, simulación, estadísticas
"""

import os
import shutil
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from collections import defaultdict

COLOR = {
    "fondo":        "#1E2235",
    "fondo2":       "#252A3D",
    "panel":        "#2C3150",
    "panel2":       "#323759",
    "borde":        "#3D4369",
    "acento":       "#3A5F8A",
    "acento_hover": "#4A7AAD",
    "acento_claro": "#5B8DB8",
    "rojo":         "#9E3A3A",
    "rojo_hover":   "#B84A4A",
    "rojo_claro":   "#C26060",
    "texto":        "#D6DCF0",
    "texto_suave":  "#7A849E",
    "exito":        "#4A8C6A",
    "error":        "#9E3A3A",
    "advertencia":  "#8C6B2A",
    "progreso_bg":  "#1E2235",
}

PALABRAS_CAPTURA = [
    "screenshot", "captura", "pantallazo", "screen shot",
    "captura de pantalla", "fullscreen", "full screen", "screen_shot",
]

SUBCARPETAS_DOC = {
    "PDF":              {".pdf"},
    "Word":             {".doc", ".docx", ".odt"},
    "Excel":            {".xls", ".xlsx", ".ods", ".csv"},
    "PowerPoint":       {".ppt", ".pptx", ".odp"},
    "Texto":            {".txt", ".rtf", ".md"},
    "Otros documentos": set(),
}

EXTENSIONES_CONOCIDAS = {
    "Imagenes":    {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff", ".heic"},
    "Videos":      {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"},
    "Audio":       {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"},
    "Documentos":  {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
                    ".odt", ".ods", ".odp", ".txt", ".rtf", ".md", ".csv"},
    "Codigo":      {".py", ".js", ".ts", ".html", ".css", ".java", ".c", ".cpp",
                    ".cs", ".php", ".rb", ".go", ".rs", ".sh", ".bat"},
    "Comprimidos": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"},
    "Ejecutables": {".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm"},
}

COLORES_CAT = {
    "Imagenes":             "#5B8DB8",
    "Videos":               "#9E3A3A",
    "Audio":                "#4A8C6A",
    "Documentos":           "#7A5BAD",
    "Codigo":               "#3A7A8C",
    "Comprimidos":          "#8C6B2A",
    "Ejecutables":          "#8C3A6B",
    "Capturas de pantalla": "#5A7A4A",
    "Otros":                "#4A4A6A",
}


def boton(padre, texto, comando, color_fondo=None, color_texto=None, ancho=None, estado="normal"):
    cf = color_fondo or COLOR["acento"]
    ct = color_texto or COLOR["texto"]
    kw = dict(text=texto, command=comando, bg=cf, fg=ct,
              font=("Segoe UI", 10, "bold"), relief="flat",
              cursor="hand2", padx=14, pady=7, borderwidth=0, state=estado)
    if ancho:
        kw["width"] = ancho
    btn = tk.Button(padre, **kw)
    hover = COLOR["acento_hover"] if cf == COLOR["acento"] else (
            COLOR["rojo_hover"] if cf == COLOR["rojo"] else cf)
    btn.bind("<Enter>", lambda e: btn.config(bg=hover) if str(btn["state"]) == "normal" else None)
    btn.bind("<Leave>", lambda e: btn.config(bg=cf))
    return btn

def separador(padre, color=None):
    return tk.Frame(padre, height=1, bg=color or COLOR["borde"])

def lbl(padre, texto, size=10, bold=False, color=None, bg=None):
    return tk.Label(padre, text=texto,
                    font=("Segoe UI", size, "bold" if bold else "normal"),
                    bg=bg or COLOR["panel"], fg=color or COLOR["texto"])

def panel_card(padre, acento_color=None, **pack_kw):
    outer = tk.Frame(padre, bg=acento_color or COLOR["acento"])
    outer.pack(**pack_kw)
    tk.Frame(outer, bg=acento_color or COLOR["acento"], width=4).pack(side="left", fill="y")
    inner = tk.Frame(outer, bg=COLOR["panel"], padx=16, pady=12)
    inner.pack(fill="both", expand=True)
    return inner


class VentanaPreview:
    def __init__(self, padre, plan, callback_confirmar):
        self.win = tk.Toplevel(padre)
        self.win.title("Previsualizacion — Archivos a mover")
        self.win.geometry("720x500")
        self.win.configure(bg=COLOR["fondo"])
        self.win.grab_set()

        tk.Label(self.win, text="Previsualizacion de la clasificacion",
                 font=("Segoe UI", 13, "bold"),
                 bg=COLOR["fondo"], fg=COLOR["texto"]).pack(pady=(16, 2))
        tk.Label(self.win,
                 text=f"{len(plan)} archivos seran organizados. Revisa antes de continuar.",
                 font=("Segoe UI", 9), bg=COLOR["fondo"], fg=COLOR["texto_suave"]).pack(pady=(0, 10))

        marco = tk.Frame(self.win, bg=COLOR["panel"],
                         highlightthickness=1, highlightbackground=COLOR["borde"])
        marco.pack(fill="both", expand=True, padx=20)

        cols = ("archivo", "categoria", "subcarpeta")
        tree = ttk.Treeview(marco, columns=cols, show="headings", height=16)

        estilo = ttk.Style()
        estilo.theme_use("default")
        estilo.configure("Preview.Treeview",
                         background=COLOR["panel"], foreground=COLOR["texto"],
                         fieldbackground=COLOR["panel"], rowheight=24,
                         font=("Segoe UI", 9))
        estilo.configure("Preview.Treeview.Heading",
                         background=COLOR["panel2"], foreground=COLOR["acento_claro"],
                         font=("Segoe UI", 9, "bold"), relief="flat")
        estilo.map("Preview.Treeview", background=[("selected", COLOR["acento"])])
        tree.configure(style="Preview.Treeview")

        tree.heading("archivo",    text="Archivo")
        tree.heading("categoria",  text="Categoria")
        tree.heading("subcarpeta", text="Subcarpeta")
        tree.column("archivo",    width=320, anchor="w")
        tree.column("categoria",  width=160, anchor="center")
        tree.column("subcarpeta", width=160, anchor="center")

        sc = ttk.Scrollbar(marco, command=tree.yview)
        tree.configure(yscrollcommand=sc.set)
        sc.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)

        for nombre, cat, sub in plan:
            tree.insert("", "end", values=(nombre, cat, sub or "—"))

        f = tk.Frame(self.win, bg=COLOR["fondo"])
        f.pack(fill="x", padx=20, pady=12)

        def confirmar():
            self.win.destroy()
            callback_confirmar()

        boton(f, "Confirmar y clasificar", confirmar).pack(side="right", padx=(6, 0))
        boton(f, "Cancelar", self.win.destroy, color_fondo=COLOR["rojo"]).pack(side="right")


class VentanaEstadisticas:
    def __init__(self, padre, stats, total, simulado=False):
        self.win = tk.Toplevel(padre)
        titulo = "Estadisticas — Simulacion" if simulado else "Estadisticas — Clasificacion completada"
        self.win.title(titulo)
        self.win.geometry("600x500")
        self.win.configure(bg=COLOR["fondo"])
        self.win.grab_set()

        tk.Label(self.win, text="Resumen de clasificacion",
                 font=("Segoe UI", 14, "bold"),
                 bg=COLOR["fondo"], fg=COLOR["texto"]).pack(pady=(16, 2))
        modo  = "SIMULACION — sin archivos movidos" if simulado else "Clasificacion completada"
        color_modo = COLOR["advertencia"] if simulado else COLOR["exito"]
        tk.Label(self.win, text=modo, font=("Segoe UI", 10, "bold"),
                 bg=COLOR["fondo"], fg=color_modo).pack(pady=(0, 10))

        canvas_w, canvas_h = 560, 220
        c = tk.Canvas(self.win, width=canvas_w, height=canvas_h,
                      bg=COLOR["fondo2"], highlightthickness=0)
        c.pack(padx=20)

        if stats and total > 0:
            cats    = list(stats.keys())
            valores = [stats[k] for k in cats]
            max_v   = max(valores) if valores else 1
            n       = len(cats)
            bar_w   = min(60, (canvas_w - 60) // n)
            gap     = max(4, (canvas_w - 40 - bar_w * n) // (n + 1))
            base_y  = canvas_h - 45

            for i, (cat, val) in enumerate(zip(cats, valores)):
                x0 = 20 + gap + i * (bar_w + gap)
                h  = max(4, int((val / max_v) * (canvas_h - 70)))
                x1 = x0 + bar_w
                y0 = base_y - h
                color_bar = COLORES_CAT.get(cat, COLOR["acento_claro"])
                c.create_rectangle(x0, y0, x1, base_y, fill=color_bar, outline="")
                c.create_text(x0 + bar_w // 2, y0 - 8, text=str(val),
                              fill=COLOR["texto"], font=("Segoe UI", 8, "bold"))
                etq = cat if len(cat) <= 10 else cat[:9] + "."
                c.create_text(x0 + bar_w // 2, base_y + 16, text=etq,
                              fill=COLOR["texto_suave"], font=("Segoe UI", 7))

            c.create_line(20, base_y, canvas_w - 20, base_y, fill=COLOR["borde"], width=1)

        marco = tk.Frame(self.win, bg=COLOR["panel"],
                         highlightthickness=1, highlightbackground=COLOR["borde"])
        marco.pack(fill="both", expand=True, padx=20, pady=10)

        cols = ("categoria", "archivos", "porcentaje")
        tree = ttk.Treeview(marco, columns=cols, show="headings", height=8)
        estilo = ttk.Style()
        estilo.configure("Stats.Treeview",
                         background=COLOR["panel"], foreground=COLOR["texto"],
                         fieldbackground=COLOR["panel"], rowheight=22,
                         font=("Segoe UI", 9))
        estilo.configure("Stats.Treeview.Heading",
                         background=COLOR["panel2"], foreground=COLOR["acento_claro"],
                         font=("Segoe UI", 9, "bold"), relief="flat")
        estilo.map("Stats.Treeview", background=[("selected", COLOR["acento"])])
        tree.configure(style="Stats.Treeview")

        tree.heading("categoria",  text="Categoria")
        tree.heading("archivos",   text="Archivos")
        tree.heading("porcentaje", text="Porcentaje")
        tree.column("categoria",  width=260, anchor="w")
        tree.column("archivos",   width=100, anchor="center")
        tree.column("porcentaje", width=120, anchor="center")

        for cat, n in sorted(stats.items(), key=lambda x: -x[1]):
            pct = f"{(n/total*100):.1f}%" if total else "0%"
            tree.insert("", "end", values=(cat, n, pct))

        sc2 = ttk.Scrollbar(marco, command=tree.yview)
        tree.configure(yscrollcommand=sc2.set)
        sc2.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)

        boton(self.win, "Cerrar", self.win.destroy,
              color_fondo=COLOR["rojo"]).pack(pady=(0, 14))


class ClasificadorV2:

    def __init__(self, ventana):
        self.ventana = ventana
        self.carpeta_origen  = tk.StringVar()
        self.carpeta_destino = tk.StringVar()
        self.en_proceso      = False
        self.pausado         = False
        self.detener_flag    = False
        self.modo_sim        = tk.BooleanVar(value=False)
        self.extensiones_sel      = set()
        self.modo_filtro          = "todas"
        self.extensiones_halladas = set()
        self._init_ventana()
        self._init_ui()

    def _init_ventana(self):
        self.ventana.title("Clasificador")
        self.ventana.geometry("820x740")
        self.ventana.configure(bg=COLOR["fondo"])
        self.ventana.minsize(720, 620)

    def _init_ui(self):
        self._init_cabecera()

        contenido = tk.Frame(self.ventana, bg=COLOR["fondo"], padx=24, pady=16)
        contenido.pack(fill="both", expand=True)

        self._panel_rutas(contenido)
        self._panel_filtros(contenido)
        self._panel_opciones(contenido)
        self._panel_acciones(contenido)
        self._panel_progreso(contenido)
        self._panel_consola(contenido)

    def _init_cabecera(self):
        """Nombre simple centrado, gris ligeramente más claro que el fondo."""
        cab = tk.Frame(self.ventana, bg=COLOR["fondo"], pady=18)
        cab.pack(fill="x")
        tk.Label(cab, text="CLASIFICADOR",
                 font=("Segoe UI", 32, "bold"),
                 bg=COLOR["fondo"], fg="#3A4060").pack()

        contenido = tk.Frame(self.ventana, bg=COLOR["fondo"], padx=24, pady=16)
        contenido.pack(fill="both", expand=True)

        self._panel_rutas(contenido)
        self._panel_filtros(contenido)
        self._panel_opciones(contenido)
        self._panel_acciones(contenido)
        self._panel_progreso(contenido)
        self._panel_consola(contenido)

    def _panel_rutas(self, p):
        inner = panel_card(p, fill="x", pady=(0, 10))
        lbl(inner, "Carpetas", 11, bold=True).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
        def fila(row, texto, var):
            lbl(inner, texto, 9, color=COLOR["texto_suave"]).grid(row=row, column=0, sticky="w", pady=3)
            tk.Entry(inner, textvariable=var, font=("Segoe UI", 10),
                     bg=COLOR["panel2"], fg=COLOR["texto"],
                     insertbackground=COLOR["texto"], relief="flat",
                     highlightthickness=1, highlightbackground=COLOR["borde"],
                     width=52).grid(row=row, column=1, padx=(8, 8), pady=3, sticky="ew")
            boton(inner, "Examinar",
                  lambda v=var: v.set(filedialog.askdirectory() or v.get())
                  ).grid(row=row, column=2, pady=3)
        inner.columnconfigure(1, weight=1)
        fila(1, "Origen:", self.carpeta_origen)
        fila(2, "Destino:", self.carpeta_destino)

    def _panel_filtros(self, p):
        inner = panel_card(p, acento_color=COLOR["rojo"], fill="x", pady=(0, 10))
        ft = tk.Frame(inner, bg=COLOR["panel"])
        ft.pack(fill="x")
        lbl(ft, "Filtro de extensiones", 11, bold=True).pack(side="left")
        self.lbl_modo_filtro = tk.Label(ft, text="● Todas",
            font=("Segoe UI", 9), bg=COLOR["panel"], fg=COLOR["exito"])
        self.lbl_modo_filtro.pack(side="right")
        separador(inner).pack(fill="x", pady=6)
        f = tk.Frame(inner, bg=COLOR["panel"])
        f.pack(fill="x")
        boton(f, "Escanear y configurar extensiones",
              self._abrir_config_extensiones, color_fondo=COLOR["rojo"]).pack(side="left")
        self.lbl_ext_resumen = tk.Label(f, text="Escanea primero la carpeta origen",
            font=("Segoe UI", 9), bg=COLOR["panel"], fg=COLOR["texto_suave"])
        self.lbl_ext_resumen.pack(side="left", padx=12)

    def _panel_opciones(self, p):
        inner = panel_card(p, acento_color=COLOR["advertencia"], fill="x", pady=(0, 10))
        lbl(inner, "Opciones", 11, bold=True).pack(anchor="w", pady=(0, 6))
        tk.Checkbutton(inner,
                       text="Modo simulacion  (no mueve archivos, solo muestra que haria)",
                       variable=self.modo_sim,
                       bg=COLOR["panel"], fg=COLOR["texto"],
                       selectcolor=COLOR["panel2"],
                       activebackground=COLOR["panel"],
                       activeforeground=COLOR["texto"],
                       font=("Segoe UI", 10)).pack(anchor="w")

    def _panel_acciones(self, p):
        f = tk.Frame(p, bg=COLOR["fondo"])
        f.pack(fill="x", pady=(0, 10))
        self.btn_preview  = boton(f, "Previsualizar", self._previsualizar,
                                  color_fondo=COLOR["acento_claro"])
        self.btn_preview.pack(side="left", padx=(0, 8))
        self.btn_iniciar  = boton(f, "Iniciar clasificacion", self._lanzar_proceso)
        self.btn_iniciar.pack(side="left", padx=(0, 8))
        self.btn_pausar   = boton(f, "Pausar", self.pausar_proceso,
                                  color_fondo=COLOR["panel2"], estado="disabled")
        self.btn_pausar.pack(side="left", padx=(0, 8))
        self.btn_reanudar = boton(f, "Reanudar", self.reanudar_proceso,
                                  color_fondo=COLOR["panel2"], estado="disabled")
        self.btn_reanudar.pack(side="left", padx=(0, 8))
        boton(f, "Limpiar consola", self.limpiar_consola,
              color_fondo=COLOR["fondo"], color_texto=COLOR["texto_suave"]).pack(side="right")

    def _panel_progreso(self, p):
        inner = panel_card(p, acento_color=COLOR["panel2"], fill="x", pady=(0, 10))
        fila = tk.Frame(inner, bg=COLOR["panel"])
        fila.pack(fill="x")
        self.lbl_progreso   = lbl(fila, "En espera", 10, bold=True)
        self.lbl_progreso.pack(side="left")
        self.lbl_tiempo     = lbl(fila, "", 9, color=COLOR["texto_suave"])
        self.lbl_tiempo.pack(side="right", padx=10)
        self.lbl_porcentaje = lbl(fila, "0%", 10, bold=True, color=COLOR["acento_claro"])
        self.lbl_porcentaje.pack(side="right")
        estilo = ttk.Style()
        estilo.theme_use("default")
        estilo.configure("V2.Horizontal.TProgressbar",
                         background=COLOR["acento_claro"],
                         troughcolor=COLOR["progreso_bg"],
                         bordercolor=COLOR["panel"], thickness=10)
        self.barra = ttk.Progressbar(inner, style="V2.Horizontal.TProgressbar",
                                     orient="horizontal", mode="determinate")
        self.barra.pack(fill="x", pady=(8, 0))

    def _panel_consola(self, p):
        outer = tk.Frame(p, bg=COLOR["borde"])
        outer.pack(fill="both", expand=True)
        tk.Label(outer, text="Registro de actividad",
                 font=("Segoe UI", 9, "bold"),
                 bg=COLOR["panel2"], fg=COLOR["texto_suave"],
                 anchor="w", padx=12, pady=6).pack(fill="x")
        self.consola = tk.Text(outer, bg=COLOR["fondo2"], fg=COLOR["texto"],
                               font=("Consolas", 9), relief="flat",
                               state="disabled", wrap="word", padx=10, pady=8)
        sc = ttk.Scrollbar(outer, command=self.consola.yview)
        self.consola.configure(yscrollcommand=sc.set)
        sc.pack(side="right", fill="y")
        self.consola.pack(fill="both", expand=True)
        self.consola.tag_configure("ok",   foreground=COLOR["exito"])
        self.consola.tag_configure("err",  foreground=COLOR["rojo_claro"])
        self.consola.tag_configure("info", foreground=COLOR["acento_claro"])
        self.consola.tag_configure("warn", foreground="#B8862A")
        self.consola.tag_configure("sim",  foreground="#7A5BAD")

    def log(self, msg, tipo="normal"):
        self.consola.config(state="normal")
        hora = time.strftime("%H:%M:%S")
        self.consola.insert("end", f"[{hora}] {msg}\n", tipo)
        self.consola.see("end")
        self.consola.config(state="disabled")

    def limpiar_consola(self):
        self.consola.config(state="normal")
        self.consola.delete("1.0", "end")
        self.consola.config(state="disabled")

    def _subcarpeta_doc(self, ext):
        for nombre, exts in SUBCARPETAS_DOC.items():
            if ext in exts:
                return nombre
        return "Otros documentos"

    def _categoria(self, ext):
        for cat, exts in EXTENSIONES_CONOCIDAS.items():
            if ext in exts:
                return cat
        return ext.lstrip(".").upper() if ext else "Sin extension"

    def _es_captura(self, nombre):
        return any(p in nombre.lower() for p in PALABRAS_CAPTURA)

    def _procesar_ext(self, ext):
        if self.modo_filtro == "todas":
            return True
        return (ext.lower() if ext else "__sin__") in self.extensiones_sel

    def _construir_plan(self):
        origen = self.carpeta_origen.get()
        plan   = []
        for raiz, _, fnames in os.walk(origen):
            for nombre in fnames:
                ext = os.path.splitext(nombre)[1].lower()
                if not self._procesar_ext(ext):
                    continue
                ruta = os.path.join(raiz, nombre)
                if self._es_captura(nombre):
                    cat, sub = "Capturas de pantalla", None
                else:
                    cat = self._categoria(ext)
                    sub = self._subcarpeta_doc(ext) if cat == "Documentos" else None
                plan.append((nombre, cat, sub, ruta))
        return plan

    def _previsualizar(self):
        if not self.carpeta_origen.get():
            messagebox.showwarning("Aviso", "Selecciona la carpeta de origen.")
            return
        plan = self._construir_plan()
        if not plan:
            messagebox.showinfo("Sin archivos", "No se encontraron archivos con los filtros actuales.")
            return
        self.log(f"Previsualizacion: {len(plan)} archivos encontrados.", "info")
        VentanaPreview(self.ventana, [(n, c, s) for n, c, s, _ in plan], self._lanzar_proceso)

    def _lanzar_proceso(self):
        if not self.carpeta_origen.get() or not self.carpeta_destino.get():
            messagebox.showwarning("Aviso", "Selecciona las carpetas de origen y destino.")
            return
        if self.en_proceso:
            return
        self.en_proceso   = True
        self.detener_flag = False
        self.pausado      = False
        self.btn_iniciar.config(state="disabled")
        self.btn_preview.config(state="disabled")
        self.btn_pausar.config(state="normal")
        threading.Thread(target=self._clasificar, daemon=True).start()

    def _clasificar(self):
        simulado = self.modo_sim.get()
        self.log("MODO SIMULACION — no se movera ningun archivo" if simulado
                 else "Iniciando clasificacion...", "sim" if simulado else "info")

        plan  = self._construir_plan()
        total = len(plan)
        self.log(f"Archivos a procesar: {total}", "info")
        self.barra["maximum"] = max(total, 1)
        self.barra["value"]   = 0

        if total == 0:
            self.log("No se encontraron archivos.", "warn")
            self._fin_proceso()
            return

        stats  = defaultdict(int)
        inicio = time.time()
        movidos = 0

        for i, (nombre, cat, sub, ruta_origen) in enumerate(plan):
            while self.pausado and not self.detener_flag:
                time.sleep(0.1)
            if self.detener_flag:
                self.log("Proceso cancelado.", "warn")
                break

            destino_base = self.carpeta_destino.get()
            if cat == "Capturas de pantalla":
                carpeta_final = os.path.join(destino_base, "Capturas de pantalla")
            elif cat == "Documentos" and sub:
                carpeta_final = os.path.join(destino_base, "Documentos", sub)
            else:
                carpeta_final = os.path.join(destino_base, cat)

            base, ext2 = os.path.splitext(nombre)
            nombre_final = nombre
            c = 1
            while os.path.exists(os.path.join(carpeta_final, nombre_final)):
                nombre_final = f"{base}_{c}{ext2}"
                c += 1

            if simulado:
                dest_rel = os.path.join(cat, sub or "", nombre_final)
                self.log(f"[SIM] {nombre}  ->  {dest_rel}", "sim")
                stats[cat] += 1
                movidos += 1
            else:
                try:
                    os.makedirs(carpeta_final, exist_ok=True)
                    shutil.move(ruta_origen, os.path.join(carpeta_final, nombre_final))
                    self.log(f"OK {nombre_final}  [{cat}{' / ' + sub if sub else ''}]", "ok")
                    stats[cat] += 1
                    movidos += 1
                except PermissionError:
                    self.log(f"Sin permisos: {nombre}", "err")
                except Exception:
                    try:
                        os.makedirs(carpeta_final, exist_ok=True)
                        shutil.copy2(ruta_origen, os.path.join(carpeta_final, nombre_final))
                        os.remove(ruta_origen)
                        self.log(f"OK (copia) {nombre_final}", "ok")
                        stats[cat] += 1
                        movidos += 1
                    except Exception as e2:
                        self.log(f"Error: {nombre} — {e2}", "err")

            pct = int(((i + 1) / total) * 100)
            self.barra["value"]   = i + 1
            self.lbl_porcentaje.config(text=f"{pct}%")
            self.lbl_progreso.config(text=f"{'[SIM] ' if simulado else ''}Procesando {i+1}/{total}")
            if i > 0:
                transcurrido = time.time() - inicio
                restante = int((total - i) * (transcurrido / i))
                m, s = divmod(restante, 60)
                self.lbl_tiempo.config(text=f"~{m:02d}:{s:02d} restantes")
            self.ventana.update_idletasks()

        self.log("—" * 42, "info")
        accion = "procesados (simulacion)" if simulado else "movidos"
        self.log(f"Completado: {movidos} archivos {accion}.", "info")
        self.lbl_progreso.config(text=f"{'Simulacion' if simulado else 'Clasificacion'} completada — {movidos} archivos")
        self.lbl_tiempo.config(text="")
        self._fin_proceso()
        VentanaEstadisticas(self.ventana, dict(stats), movidos, simulado=simulado)

    def _fin_proceso(self):
        self.en_proceso = False
        self.pausado    = False
        self.btn_iniciar.config(state="normal")
        self.btn_preview.config(state="normal")
        self.btn_pausar.config(state="disabled")
        self.btn_reanudar.config(state="disabled")

    def pausar_proceso(self):
        if self.en_proceso and not self.pausado:
            self.pausado = True
            self.log("Proceso pausado.", "warn")
            self.btn_pausar.config(state="disabled")
            self.btn_reanudar.config(state="normal")
            self.lbl_progreso.config(text="Pausado")

    def reanudar_proceso(self):
        if self.pausado:
            self.pausado = False
            self.log("Proceso reanudado.", "info")
            self.btn_pausar.config(state="normal")
            self.btn_reanudar.config(state="disabled")

    def _abrir_config_extensiones(self):
        if not self.carpeta_origen.get():
            messagebox.showwarning("Aviso", "Selecciona primero la carpeta de origen.")
            return
        self.extensiones_halladas.clear()
        try:
            for raiz, _, archs in os.walk(self.carpeta_origen.get()):
                for f in archs:
                    ext = os.path.splitext(f)[1].lower()
                    self.extensiones_halladas.add(ext if ext else "__sin__")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        if not self.extensiones_halladas:
            messagebox.showinfo("Sin extensiones", "No se encontraron archivos.")
            return

        win = tk.Toplevel(self.ventana)
        win.title("Configurar extensiones")
        win.geometry("460x480")
        win.configure(bg=COLOR["fondo"])
        win.grab_set()

        tk.Label(win, text="Extensiones encontradas",
                 font=("Segoe UI", 13, "bold"),
                 bg=COLOR["fondo"], fg=COLOR["texto"]).pack(pady=(16, 4))

        f_modo = tk.Frame(win, bg=COLOR["fondo"])
        f_modo.pack(fill="x", padx=20)
        modo_var = tk.StringVar(value=self.modo_filtro)
        for val, txt in [("todas", "Todas las extensiones"), ("seleccionadas", "Solo seleccionadas")]:
            tk.Radiobutton(f_modo, text=txt, variable=modo_var, value=val,
                           bg=COLOR["fondo"], fg=COLOR["texto"],
                           selectcolor=COLOR["panel"],
                           activebackground=COLOR["fondo"],
                           font=("Segoe UI", 10)).pack(side="left", padx=(0, 16))

        separador(win, COLOR["borde"]).pack(fill="x", padx=20, pady=8)

        contenedor = tk.Frame(win, bg=COLOR["panel"],
                              highlightthickness=1, highlightbackground=COLOR["borde"])
        contenedor.pack(fill="both", expand=True, padx=20)
        canvas = tk.Canvas(contenedor, bg=COLOR["panel"], highlightthickness=0)
        sc = ttk.Scrollbar(contenedor, command=canvas.yview)
        canvas.configure(yscrollcommand=sc.set)
        sc.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        frame_ext = tk.Frame(canvas, bg=COLOR["panel"])
        canvas.create_window((0, 0), window=frame_ext, anchor="nw")
        frame_ext.bind("<Configure>",
                       lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        vars_ext = {}
        for ext in sorted(self.extensiones_halladas):
            var  = tk.BooleanVar(value=ext in self.extensiones_sel)
            vars_ext[ext] = var
            nombre = ext.lstrip(".").upper() if ext != "__sin__" else "Sin extension"
            tk.Checkbutton(frame_ext, text=nombre, variable=var,
                           bg=COLOR["panel"], fg=COLOR["texto"],
                           selectcolor=COLOR["panel2"],
                           activebackground=COLOR["panel"],
                           font=("Segoe UI", 10)).pack(anchor="w", padx=16, pady=2)

        f_acc = tk.Frame(win, bg=COLOR["fondo"])
        f_acc.pack(fill="x", padx=20, pady=10)
        boton(f_acc, "Todas",   lambda: [v.set(True)  for v in vars_ext.values()],
              color_fondo=COLOR["panel2"]).pack(side="left", padx=(0, 6))
        boton(f_acc, "Ninguna", lambda: [v.set(False) for v in vars_ext.values()],
              color_fondo=COLOR["panel2"]).pack(side="left")

        def aplicar():
            self.extensiones_sel = {e for e, v in vars_ext.items() if v.get()}
            self.modo_filtro     = modo_var.get()
            if self.modo_filtro == "todas":
                self.lbl_modo_filtro.config(text="Todas", fg=COLOR["exito"])
                self.lbl_ext_resumen.config(text="Clasificando todas las extensiones")
            else:
                n = len(self.extensiones_sel)
                self.lbl_modo_filtro.config(text=f"{n} sel.", fg=COLOR["acento_claro"])
                self.lbl_ext_resumen.config(text=f"{n} extension(es) activa(s)")
            self.log(f"Filtro: {self.modo_filtro} — {len(self.extensiones_sel)} ext.", "info")
            win.destroy()

        boton(f_acc, "Aplicar", aplicar).pack(side="right")


if __name__ == "__main__":
    ventana = tk.Tk()
    ClasificadorV2(ventana)
    ventana.mainloop()
