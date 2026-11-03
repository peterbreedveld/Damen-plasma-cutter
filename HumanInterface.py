import math
import os
import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
from dataclasses import dataclass

# Pillow is optioneel: met Pillow worden afbeeldingen netjes geschaald en werken ook .jpg-bestanden.
# Zonder Pillow werken alleen .png en .gif (met grove schaling).
try:
    from PIL import Image, ImageTk, ImageOps
except ImportError:
    Image = ImageTk = ImageOps = None


# ---------------------------------------------------------------------------
# Uiterlijk
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Thema's: "modern" (licht, blauw) en "retro" (green phosphor terminal)
#
# Kiezen kan op twee manieren:
#   - DamenPlasmaHMI(root, thema="retro")
#   - of STANDAARD_THEMA hieronder aanpassen
# Alle kleuren en lettertypes van een thema staan in THEMAS; de rest van de code
# gebruikt alleen K[...] en FONT, dus je kunt hier ook een eigen thema bij zetten.
# ---------------------------------------------------------------------------

STANDAARD_THEMA = "modern"

THEMAS = {
    "modern": {
        "fonts": ["Segoe UI"],
        "bg": "#eef1f5", "kaart": "#ffffff", "rand": "#d9dee6", "rand_dikte": 1,
        "tekst": "#1f2937", "subtiel": "#6b7280",
        "header": "#0f172a", "header_tekst": "white", "header_sub": "#94a3b8",
        "accent": "#2563eb", "accent_hover": "#1d4ed8",
        "succes": "#16a34a", "succes_hover": "#15803d",
        "gevaar": "#dc2626", "gevaar_hover": "#b91c1c",
        "uit": "#cbd5e1", "uit_rand": "#94a3b8", "snijden": "#ea580c",
        "knop_tekst": "white", "knop_uit_tekst": "#f8fafc",
        "veld": "white", "veld_uit": "#f1f5f9", "veld_uit_tekst": "#9ca3af",
        "secundair": "#e2e8f0", "secundair_hover": "#cbd5e1", "secundair_uit": "#f1f5f9",
        "selectie": "#dbeafe", "beeld_bg": "#f8fafc",
        "tag_bezig": "#fff3b0", "tag_klaar": "#c8f7c5", "tag_onderbroken": "#fecaca",
        "scroll": "#cbd5e1", "scroll_trog": "#f1f5f9",
        # Statuskleuren staan in de header (donker), dus iets lichtere varianten
        "status": {"blue": "#60a5fa", "green": "#4ade80", "red": "#f87171", "orange": "#fbbf24"},
        "status_voorvoegsel": "Status: ", "titel_voorvoegsel": "", "hoofdletters": False,
        "cursor": False, "beeld_groen": False,
    },
    "retro": {
        # Eerste beschikbare monospace-font wordt gebruikt
        "fonts": ["Consolas", "DejaVu Sans Mono", "Liberation Mono", "Courier New", "Courier"],
        "bg": "#000000", "kaart": "#020d04", "rand": "#1c7a36", "rand_dikte": 2,
        "tekst": "#33ff66", "subtiel": "#1fa84a",
        "header": "#000000", "header_tekst": "#33ff66", "header_sub": "#1fa84a",
        "accent": "#22cc55", "accent_hover": "#33ff66",
        "succes": "#33ff66", "succes_hover": "#7dffa0",
        "gevaar": "#ff3b30", "gevaar_hover": "#ff6b60",   # noodstop blijft duidelijk rood
        "uit": "#0d3d1a", "uit_rand": "#1c7a36", "snijden": "#ffb000",
        "knop_tekst": "#000000", "knop_uit_tekst": "#1a6b2f",
        "veld": "#000000", "veld_uit": "#061a0a", "veld_uit_tekst": "#1a6b2f",
        "secundair": "#0d3d1a", "secundair_hover": "#176b2f", "secundair_uit": "#061a0a",
        "selectie": "#0f5a24", "beeld_bg": "#000000",
        "tag_bezig": "#4a3d00", "tag_klaar": "#0a3d17", "tag_onderbroken": "#4a0f0f",
        "scroll": "#1c7a36", "scroll_trog": "#020d04",
        "status": {"blue": "#33ff66", "green": "#33ff66", "red": "#ff5a4d", "orange": "#ffb000"},
        "status_voorvoegsel": "> STATUS: ", "titel_voorvoegsel": "> ", "hoofdletters": True,
        "cursor": True,
        # True = uitleg-afbeeldingen groen/zwart maken (alleen met Pillow). Staat uit omdat
        # kleuren in de afbeelding soms juist de variabelen duidelijk maken.
        "beeld_groen": False,
    },
}

K = {}                  # actieve kleuren/instellingen; wordt gevuld door activeer_thema()
FONT = "Segoe UI"       # actief lettertype; wordt gezet door activeer_thema()


def activeer_thema(root, naam):
    """Zet het gekozen thema actief. Moet aangeroepen worden voordat widgets gemaakt worden."""
    global FONT
    if naam not in THEMAS:
        raise ValueError(f"Onbekend thema '{naam}'. Kies uit: {', '.join(THEMAS)}")
    K.clear()
    K.update(THEMAS[naam])
    K["naam"] = naam
    beschikbaar = set(tkfont.families(root))
    kandidaten = K["fonts"]
    FONT = next((f for f in kandidaten if f in beschikbaar), kandidaten[-1])


# Map met afbeeldingen naast dit bestand. Bestandsnaam = cuttype + extensie,
# bijv. afbeeldingen/type6.png, afbeeldingen/v_cut.png
AFBEELDINGEN_MAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "afbeeldingen")
BEELD_MAX = (520, 350)   # maximale afmeting (breedte, hoogte) van de afbeelding in pixels


def laad_afbeelding(naam):
    """Zoekt afbeeldingen/<naam>.(png|jpg|jpeg|gif) en geeft een PhotoImage terug, of None."""
    for ext in (".png", ".jpg", ".jpeg", ".gif"):
        pad = os.path.join(AFBEELDINGEN_MAP, naam + ext)
        if not os.path.isfile(pad):
            continue
        try:
            if ImageTk is not None:
                img = Image.open(pad)
                img.thumbnail(BEELD_MAX, Image.LANCZOS)
                if K.get("beeld_groen"):
                    img = ImageOps.colorize(ImageOps.grayscale(img), black="#000000", white=K["tekst"])
                return ImageTk.PhotoImage(img)
            foto = tk.PhotoImage(file=pad)
            factor = max(math.ceil(foto.width() / BEELD_MAX[0]),
                         math.ceil(foto.height() / BEELD_MAX[1]), 1)
            return foto.subsample(factor) if factor > 1 else foto
        except Exception as fout:
            print(f"Kon afbeelding '{pad}' niet laden: {fout}")
    return None


class KnopModern(tk.Button):
    """Platte knop met hover-effect en een andere kleur als hij uitgeschakeld is."""

    def __init__(self, parent, tekst, kleur, hover, command, state=tk.NORMAL, **kw):
        self._kleur = kleur
        self._hover = hover
        super().__init__(
            parent, text=tekst, command=command, bg=kleur, fg=K["knop_tekst"],
            activebackground=hover, activeforeground=K["knop_tekst"],
            disabledforeground=K["knop_uit_tekst"], relief="flat", bd=0, cursor="hand2",
            font=(FONT, 12, "bold"), padx=22, pady=10, state=state, **kw,
        )
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", lambda e: self._pas_kleur())
        self._pas_kleur()

    def _actief(self):
        return str(self.cget("state")) != "disabled"

    def _enter(self, _event):
        if self._actief():
            tk.Button.configure(self, bg=self._hover)

    def _pas_kleur(self):
        tk.Button.configure(self, bg=self._kleur if self._actief() else K["uit"])

    def configure(self, cnf=None, **kw):
        resultaat = super().configure(cnf, **kw)
        if "state" in kw:
            self._pas_kleur()
        return resultaat

    config = configure


# ---------------------------------------------------------------------------
# Definitie van parameters, sneden en profielen
# Alles wat je wilt aanpassen/uitbreiden staat hier; de GUI past zich vanzelf aan.
#
# Optioneel per snede: "afbeelding": "bestandsnaam_zonder_extensie"
# Standaard wordt de afbeelding gezocht op basis van "cuttype".
# ---------------------------------------------------------------------------

@dataclass
class Param:
    label: str            # wat de operator ziet
    key: str              # naam in de data die naar de besturingskern gaat
    kind: str = "mm"      # "mm" (invoer in mm -> opslag in meter), "float" (ongewijzigd), "keuze"
    keuzes: dict = None   # alleen bij kind="keuze": {label voor operator: opgeslagen waarde}

    def parse(self, ruw):
        """Zet de invoer van de operator direct om naar de uiteindelijke waarde."""
        ruw = ruw.strip()
        if self.kind == "keuze":
            return self.keuzes[ruw]
        waarde = float(ruw.replace(",", "."))   # ValueError als het geen getal is
        return waarde / 1000 if self.kind == "mm" else waarde


# Veelgebruikte parameters
# Operator ziet "zijde" met rear/front; naar de besturingskern gaat nog steeds "left"/"right"
ZIJDE = Param("zijde", "side", "keuze", {"rear": "left", "front": "right"})
POSITIE = Param("position", "position", "mm")
ORIENTATIE = Param(
    "orientation", "lengthwise", "keuze",
    {"lengthwise": True, "widthwise": False},
)

PROFIELEN = {
    "Rectangular profile": {
        "code": "Rect",
        "sneden": {
            "V-cut": {
                "cuttype": "v_cut",
                "params": [ORIENTATIE, POSITIE, ZIJDE],
            },
            "Type 85": {
                "cuttype": "type85",
                "params": [ORIENTATIE, Param("Y(angle)", "A", "float"), ZIJDE],
            },
        },
    },
    "Holland profile": {
        "code": "HP",
        "sneden": {
            "Type 6": {
                "cuttype": "type6",
                "params": [Param("Angle", "Y", "float"), POSITIE, ZIJDE],
            },
            "Type 9": {
                "cuttype": "type9",
                "params": [Param("Angle", "Y", "float"), POSITIE, ZIJDE],
            },
        },
    },
    "Angular profile": {
        "code": "Angle",
        "sneden": {
            "Type 11": {
                "cuttype": "type11",
                "params": [
                    Param("X", "X", "mm"),
                    Param("Y", "Y", "mm"),
                    Param("Angle", "Angle", "float"),
                    POSITIE,
                    ZIJDE,
                ],
            },
            "Type 83": {
                "cuttype": "type83",
                "params": [POSITIE, ZIJDE],
            },
        },
    },
}

DIMENSIES = ["height", "width", "length", "thickness"]   # allemaal in mm


class DamenPlasmaHMI:
    def __init__(self, root, on_job_submitted=None, on_start=None, on_noodstop=None, on_reset=None, thema=None):
        self.root = root
        activeer_thema(root, thema or STANDAARD_THEMA)   # eerst thema, dan pas widgets
        self.on_job_submitted = on_job_submitted
        self.on_start = on_start
        self.on_noodstop = on_noodstop
        self.on_reset = on_reset      # moet False teruggeven als resetten nu niet mag
        self.root.title("Damen Robot Plasmasnijder HMI")
        self.root.configure(bg=K["bg"])

        # Maak de applicatie full-screen, met de mogelijkheid om te sluiten via 'Escape'
        self.root.attributes('-fullscreen', True)
        self.root.bind("<Escape>", lambda event: self.root.attributes("-fullscreen", False))
        self.root.protocol("WM_DELETE_WINDOW", self.sluiten)

        # Elke geplande snede:
        # {"naam": ..., "weergave": ..., "args": {...kant-en-klaar...}, "status": "Wachtend", "afbeelding": ...}
        self.geplande_sneden = []
        self.bevestigd = False   # True zodra de operator de opdracht heeft bevestigd
        self.bezig = False       # True zodra het systeem is gestart en aan het snijden is

        self.indicatoren = {}    # sleutel -> widgets van een statuslampje
        self._foto_cache = {}    # afbeeldingen (ook nodig om ze in het geheugen te houden)

        self.stel_stijl_in()
        self.bouw_interface()

    # ------------------------------------------------------------------
    # Stijl
    # ------------------------------------------------------------------

    def stel_stijl_in(self):
        stijl = ttk.Style()
        stijl.theme_use("clam")

        self.root.option_add("*TCombobox*Listbox.font", (FONT, 11))
        self.root.option_add("*TCombobox*Listbox.background", K["kaart"])
        self.root.option_add("*TCombobox*Listbox.foreground", K["tekst"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", K["accent"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", K["knop_tekst"])

        invoer = dict(
            padding=7, fieldbackground=K["veld"], foreground=K["tekst"],
            bordercolor=K["rand"], lightcolor=K["veld"], darkcolor=K["veld"],
            insertcolor=K["tekst"], selectbackground=K["selectie"], selectforeground=K["tekst"],
        )
        stijl.configure("TEntry", **invoer)
        stijl.configure("TCombobox", arrowsize=16, arrowcolor=K["tekst"], background=K["secundair"], **invoer)
        stijl.map(
            "TCombobox",
            fieldbackground=[("readonly", K["veld"]), ("disabled", K["veld_uit"])],
            selectbackground=[("readonly", K["veld"])],
            selectforeground=[("readonly", K["tekst"])],
            foreground=[("disabled", K["veld_uit_tekst"])],
            bordercolor=[("focus", K["accent"])],
        )
        stijl.map(
            "TEntry",
            fieldbackground=[("disabled", K["veld_uit"])],
            foreground=[("disabled", K["veld_uit_tekst"])],
            bordercolor=[("focus", K["accent"])],
        )

        stijl.configure("Treeview", rowheight=32, font=(FONT, 10), background=K["kaart"],
                        fieldbackground=K["kaart"], foreground=K["tekst"], borderwidth=0)
        stijl.configure("Treeview.Heading", font=(FONT, 10, "bold"), background=K["secundair"],
                        foreground=K["tekst"], relief="flat", padding=6)
        stijl.map("Treeview", background=[("selected", K["selectie"])],
                  foreground=[("selected", K["tekst"])])
        stijl.map("Treeview.Heading", background=[("active", K["secundair_hover"])])

        stijl.configure("Horizontal.TProgressbar", troughcolor=K["secundair"], background=K["accent"],
                        bordercolor=K["secundair"], lightcolor=K["accent"], darkcolor=K["accent"],
                        thickness=14)

        stijl.configure("Accent.TButton", font=(FONT, 10, "bold"), padding=(14, 8),
                        background=K["accent"], foreground=K["knop_tekst"], borderwidth=0,
                        bordercolor=K["accent"], lightcolor=K["accent"], darkcolor=K["accent"],
                        focuscolor=K["accent"])
        stijl.map("Accent.TButton",
                  background=[("disabled", K["uit"]), ("active", K["accent_hover"])],
                  foreground=[("disabled", K["knop_uit_tekst"])])

        stijl.configure("Secundair.TButton", font=(FONT, 10), padding=(14, 8),
                        background=K["secundair"], foreground=K["tekst"], borderwidth=0,
                        bordercolor=K["secundair"], lightcolor=K["secundair"], darkcolor=K["secundair"],
                        focuscolor=K["secundair"])
        stijl.map("Secundair.TButton",
                  background=[("disabled", K["secundair_uit"]), ("active", K["secundair_hover"])],
                  foreground=[("disabled", K["veld_uit_tekst"])])

        stijl.configure("Vertical.TScrollbar", background=K["scroll"], troughcolor=K["scroll_trog"],
                        bordercolor=K["scroll_trog"], arrowcolor=K["subtiel"])

    def maak_kaart(self, parent, titel):
        """Kaart met titel. Geeft (buitenframe om te packen, binnenframe om in te bouwen)."""
        if K["hoofdletters"]:
            titel = titel.upper()
        titel = K["titel_voorvoegsel"] + titel
        buiten = tk.Frame(parent, bg=K["kaart"], highlightbackground=K["rand"],
                          highlightthickness=K["rand_dikte"])
        tk.Label(buiten, text=titel, font=(FONT, 12, "bold"), bg=K["kaart"],
                 fg=K["tekst"]).pack(anchor="w", padx=16, pady=(12, 6))
        binnen = tk.Frame(buiten, bg=K["kaart"])
        binnen.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 14))
        return buiten, binnen

    def maak_label(self, parent, tekst, **kw):
        opties = dict(bg=K["kaart"], fg=K["tekst"], font=(FONT, 10))
        opties.update(kw)
        return tk.Label(parent, text=tekst, **opties)

    # ------------------------------------------------------------------
    # Opbouw van de interface
    # ------------------------------------------------------------------

    def bouw_interface(self):
        # --- HEADER: titel, status en hoofdknoppen ---
        header = tk.Frame(self.root, bg=K["header"])
        header.pack(fill=tk.X)
        header_inner = tk.Frame(header, bg=K["header"], padx=24, pady=14)
        header_inner.pack(fill=tk.X)
        if K["naam"] == "retro":
            tk.Frame(self.root, bg=K["rand"], height=2).pack(fill=tk.X)   # streep onder de header

        tk.Label(header_inner, text="DAMEN", font=(FONT, 16, "bold"), bg=K["header"],
                 fg=K["header_tekst"]).pack(side=tk.LEFT)
        tk.Label(header_inner, text="Plasmasnijder HMI", font=(FONT, 12), bg=K["header"],
                 fg=K["header_sub"]).pack(side=tk.LEFT, padx=(10, 30))

        self.status_label = tk.Label(header_inner, font=(FONT, 13, "bold"), bg=K["header"])
        self.status_label.pack(side=tk.LEFT)
        self._toon_status("Wacht op invoer...", "blue")

        # Knipperende cursor achter de status (alleen in het retro-thema)
        self._cursor_aan = True
        self.cursor_label = tk.Label(header_inner, text="\u2588", font=(FONT, 13, "bold"),
                                     bg=K["header"], fg=K["tekst"])
        if K["cursor"]:
            self.cursor_label.pack(side=tk.LEFT, padx=(6, 0))
            self._knipper_cursor()

        stop_btn = KnopModern(header_inner, "NOODSTOP", K["gevaar"], K["gevaar_hover"], self.noodstop)
        stop_btn.pack(side=tk.RIGHT, padx=(10, 0))

        # Start is pas beschikbaar na bevestiging van de opdracht
        self.start_btn = KnopModern(header_inner, "START SYSTEEM", K["succes"], K["succes_hover"],
                                    self.start_systeem, state=tk.DISABLED)
        self.start_btn.pack(side=tk.RIGHT)

        # --- BODY: twee kolommen ---
        body = tk.Frame(self.root, bg=K["bg"], padx=20, pady=16)
        body.pack(fill=tk.BOTH, expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=0, minsize=340)
        body.rowconfigure(0, weight=1)

        links = tk.Frame(body, bg=K["bg"])
        links.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        rechts = tk.Frame(body, bg=K["bg"])
        rechts.grid(row=0, column=1, sticky="nsew")

        self.bouw_linkerkolom(links)
        self.bouw_rechterkolom(rechts)

        # Alles wat tijdens het snijden vergrendeld moet worden
        self.bewerk_widgets = [
            self.profiel_dropdown, self.snede_dropdown, self.voeg_toe_btn,
            self.verwijder_btn, self.wis_btn, self.bevestig_btn, self.reset_btn,
            *self.profiel_dimensies.values(),
        ]

        self.toon_afbeelding(None)

    def bouw_linkerkolom(self, parent):
        # --- Kaart 1: Profiel & afmetingen ---
        kaart, profiel_frame = self.maak_kaart(parent, "1.  Profiel eigenschappen")
        kaart.pack(fill=tk.X, pady=(0, 12))

        self.maak_label(profiel_frame, "Kies profiel:").grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.profiel_var = tk.StringVar()
        self.profiel_dropdown = ttk.Combobox(profiel_frame, textvariable=self.profiel_var,
                                             values=list(PROFIELEN.keys()), state="readonly",
                                             width=28, font=(FONT, 11))
        self.profiel_dropdown.grid(row=0, column=1, columnspan=3, sticky="w", pady=(0, 8), padx=(8, 0))
        self.profiel_dropdown.bind("<<ComboboxSelected>>", self.update_snede_opties)

        self.profiel_dimensies = {}
        for i, dim in enumerate(DIMENSIES):
            self.maak_label(profiel_frame, f"{dim.capitalize()} (mm)",
                            fg=K["subtiel"]).grid(row=1, column=i, sticky="w", padx=(0, 12))
            var = tk.StringVar()
            # Als een afmeting verandert nadat er bevestigd is, moet opnieuw bevestigd worden
            var.trace_add("write", lambda *args: self.invalideer_bevestiging())
            entry = ttk.Entry(profiel_frame, width=12, textvariable=var, font=(FONT, 11))
            entry.grid(row=2, column=i, sticky="w", padx=(0, 12))
            self.profiel_dimensies[dim] = entry

        # --- Kaart 2: Snede kiezen (links invoer, rechts afbeelding) ---
        kaart, self.snede_frame = self.maak_kaart(parent, "2.  Voeg sneden toe")
        kaart.pack(fill=tk.X, pady=(0, 12))

        bovenrij = tk.Frame(self.snede_frame, bg=K["kaart"])
        bovenrij.pack(fill=tk.X, pady=(0, 10))
        self.maak_label(bovenrij, "Kies snede:").pack(side=tk.LEFT)
        self.snede_var = tk.StringVar()
        self.snede_dropdown = ttk.Combobox(bovenrij, textvariable=self.snede_var, state="readonly",
                                           width=28, font=(FONT, 11))
        self.snede_dropdown.pack(side=tk.LEFT, padx=(8, 0))
        self.snede_dropdown.bind("<<ComboboxSelected>>", self.maak_snede_invoervelden)

        onderrij = tk.Frame(self.snede_frame, bg=K["kaart"])
        onderrij.pack(fill=tk.X)

        invoer_kolom = tk.Frame(onderrij, bg=K["kaart"])
        invoer_kolom.pack(side=tk.LEFT, fill=tk.Y, anchor="n")

        self.variabelen_frame = tk.Frame(invoer_kolom, bg=K["kaart"])
        self.variabelen_frame.pack(anchor="w")
        self.snede_invoervelden = {}

        self.voeg_toe_btn = ttk.Button(invoer_kolom, text="+  Voeg snede toe aan lijst",
                                       style="Accent.TButton", command=self.voeg_snede_toe,
                                       state=tk.DISABLED)
        self.voeg_toe_btn.pack(anchor="w", pady=(14, 0))

        # Afbeelding met uitleg van de variabelen
        beeld_kolom = tk.Frame(onderrij, bg=K["kaart"])
        beeld_kolom.pack(side=tk.RIGHT, padx=(20, 0))
        tk.Label(beeld_kolom, text="Bovenaanzicht snede", font=(FONT, 10, "bold"),
                 bg=K["kaart"], fg=K["tekst"]).pack(anchor="w", pady=(0, 6))
        beeld_kader = tk.Frame(beeld_kolom, bg=K["beeld_bg"], highlightbackground=K["rand"],
                               highlightthickness=1, width=BEELD_MAX[0] + 20, height=BEELD_MAX[1] + 20)
        beeld_kader.pack()
        beeld_kader.pack_propagate(False)
        self.beeld_label = tk.Label(beeld_kader, bg=K["beeld_bg"], fg=K["subtiel"], font=(FONT, 10),
                                    justify="center", wraplength=BEELD_MAX[0] - 20)
        self.beeld_label.pack(expand=True)

        # --- Kaart 3: Overzicht van geplande sneden ---
        kaart, lijst_frame = self.maak_kaart(parent, "3.  Volgorde van geplande sneden")
        kaart.pack(fill=tk.BOTH, expand=True)

        tabel_frame = tk.Frame(lijst_frame, bg=K["kaart"])
        tabel_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("nr", "type", "params", "status")
        self.sneden_lijst = ttk.Treeview(tabel_frame, columns=columns, show="headings", height=4)
        self.sneden_lijst.heading("nr", text="#")
        self.sneden_lijst.heading("type", text="Snede type")
        self.sneden_lijst.heading("params", text="Parameters")
        self.sneden_lijst.heading("status", text="Status")
        self.sneden_lijst.column("nr", width=40, anchor="center", stretch=False)
        self.sneden_lijst.column("type", width=150, stretch=False)
        self.sneden_lijst.column("params", width=500)
        self.sneden_lijst.column("status", width=110, anchor="center", stretch=False)
        self.sneden_lijst.tag_configure("bezig", background=K["tag_bezig"])
        self.sneden_lijst.tag_configure("klaar", background=K["tag_klaar"])
        self.sneden_lijst.tag_configure("onderbroken", background=K["tag_onderbroken"])
        self.sneden_lijst.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        scrollbar = ttk.Scrollbar(tabel_frame, orient=tk.VERTICAL, command=self.sneden_lijst.yview)
        self.sneden_lijst.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        knoppen_frame = tk.Frame(lijst_frame, bg=K["kaart"])
        knoppen_frame.pack(fill=tk.X, pady=(10, 0))
        self.verwijder_btn = ttk.Button(knoppen_frame, text="Verwijder geselecteerde snede",
                                        style="Secundair.TButton", command=self.verwijder_snede)
        self.verwijder_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.wis_btn = ttk.Button(knoppen_frame, text="Wis alle sneden",
                                  style="Secundair.TButton", command=self.wis_alle_sneden)
        self.wis_btn.pack(side=tk.LEFT)

    def bouw_rechterkolom(self, parent):
        # Reset en afsluiten helemaal onderaan (ver weg van START/NOODSTOP)
        onderknoppen = tk.Frame(parent, bg=K["bg"])
        onderknoppen.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        onderknoppen.columnconfigure(0, weight=1, uniform="onder")
        onderknoppen.columnconfigure(1, weight=1, uniform="onder")
        self.reset_btn = ttk.Button(onderknoppen, text="Reset / nieuw profiel",
                                    style="Secundair.TButton", command=self.reset_interface)
        self.reset_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ttk.Button(onderknoppen, text="Afsluiten", style="Secundair.TButton",
                   command=self.sluiten).grid(row=0, column=1, sticky="ew", padx=(5, 0))

        # Bevestigknop (eerst packen zodat hij altijd zichtbaar blijft)
        self.bevestig_btn = KnopModern(parent, "Klaar met invoeren\nBekijk & bevestig", K["accent"],
                                       K["accent_hover"], self.toon_bevestiging_scherm)
        self.bevestig_btn.pack(side=tk.BOTTOM, fill=tk.X, pady=(12, 0))

        # --- Machinestatus ---
        kaart, status_frame = self.maak_kaart(parent, "Machinestatus")
        kaart.pack(fill=tk.X, pady=(0, 12))

        self.maak_indicator(status_frame, "robot", "Robotarm", "BEWEEGT", "STIL", begin=False)
        self.maak_indicator(status_frame, "plasma", "Plasmasnijder", "AAN", "UIT",
                            begin=False, kleur_aan=K["snijden"])
        tk.Frame(status_frame, bg=K["rand"], height=1).pack(fill=tk.X, pady=8)
        self.maak_indicator(status_frame, "pneumatiek", "Pneumatiek", "AAN", "UIT", begin=False)
        self.maak_indicator(status_frame, "conveyor", "Transportband", "LOOPT", "STIL", begin=False)
        tk.Frame(status_frame, bg=K["rand"], height=1).pack(fill=tk.X, pady=8)
        for n in (1, 2):
            self.maak_indicator(status_frame, f"clamp{n}", f"Clamp {n}", "DICHT", "OPEN", begin=None)
        self.maak_indicator(status_frame, f"clamp3", f"Extra support", "AAN", "UIT", begin=None)

        # --- Voortgang ---
        kaart, voortgang_frame = self.maak_kaart(parent, "Voortgang")
        kaart.pack(fill=tk.X)

        self.actief_label = tk.Label(voortgang_frame, text="Nu bezig: -", font=(FONT, 10),
                                     bg=K["kaart"], fg=K["tekst"], wraplength=300,
                                     justify="left", anchor="w")
        self.actief_label.pack(fill=tk.X)
        self.voortgang = ttk.Progressbar(voortgang_frame, orient=tk.HORIZONTAL, mode="determinate",
                                         maximum=1, value=0)
        self.voortgang.pack(fill=tk.X, pady=(10, 0))

    def maak_indicator(self, parent, sleutel, naam, tekst_aan, tekst_uit, begin=None, kleur_aan=None):
        """Maakt een rij met een gekleurd lampje, een naam en een statustekst."""
        rij = tk.Frame(parent, bg=K["kaart"])
        rij.pack(fill=tk.X, pady=4)

        canvas = tk.Canvas(rij, width=22, height=22, bg=K["kaart"], highlightthickness=0)
        ovaal = canvas.create_oval(3, 3, 19, 19, outline=K["uit_rand"], width=2, fill="")
        canvas.pack(side=tk.LEFT)

        tk.Label(rij, text=naam, font=(FONT, 11), bg=K["kaart"], fg=K["tekst"]).pack(side=tk.LEFT, padx=(8, 0))
        toestand = tk.Label(rij, text="", font=(FONT, 10, "bold"), bg=K["kaart"])
        toestand.pack(side=tk.RIGHT)

        self.indicatoren[sleutel] = {
            "canvas": canvas, "ovaal": ovaal, "label": toestand,
            "aan": tekst_aan, "uit": tekst_uit,
            "kleur": kleur_aan or K["succes"],
        }
        self._zet_indicator(sleutel, begin)

    def _zet_indicator(self, sleutel, toestand):
        """toestand: True = aan/dicht/loopt, False = uit/open/stil, None = onbekend."""
        ind = self.indicatoren[sleutel]
        if toestand is None:
            ind["canvas"].itemconfig(ind["ovaal"], fill="", outline=K["uit_rand"])
            ind["label"].config(text="ONBEKEND", fg=K["subtiel"])
        elif toestand:
            ind["canvas"].itemconfig(ind["ovaal"], fill=ind["kleur"], outline=ind["kleur"])
            ind["label"].config(text=ind["aan"], fg=ind["kleur"])
        else:
            ind["canvas"].itemconfig(ind["ovaal"], fill=K["uit"], outline=K["uit_rand"])
            ind["label"].config(text=ind["uit"], fg=K["subtiel"])

    # ------------------------------------------------------------------
    # Afbeelding bij de gekozen snede
    # ------------------------------------------------------------------

    def toon_afbeelding(self, snede):
        """Toont de uitleg-afbeelding van de gekozen snede (of een placeholder)."""
        if snede is None:
            self.beeld_label.config(image="", text="Kies een snede om de uitleg\nvan de variabelen te zien.")
            return

        naam = snede.get("afbeelding", snede["cuttype"])
        if naam not in self._foto_cache:
            foto = laad_afbeelding(naam)
            if foto is not None:
                self._foto_cache[naam] = foto
        foto = self._foto_cache.get(naam)

        if foto is not None:
            self.beeld_label.config(image=foto, text="")
        else:
            self.beeld_label.config(
                image="",
                text=f"Geen afbeelding gevonden.\n\nPlaats '{naam}.png' in de map\n'afbeeldingen'.",
            )

    # ------------------------------------------------------------------
    # Status / indicatoren
    # ------------------------------------------------------------------

    def _toon_status(self, tekst, kleur="blue"):
        self.status_label.config(text=f"{K['status_voorvoegsel']}{tekst}",
                                 fg=K["status"].get(kleur, kleur))

    def _knipper_cursor(self):
        """Laat de cursor achter de statustekst knipperen (retro-thema)."""
        self._cursor_aan = not self._cursor_aan
        self.cursor_label.config(fg=K["tekst"] if self._cursor_aan else K["header"])
        self.root.after(530, self._knipper_cursor)

    # --- LOGICA FUNCTIES ---

    def zet_bewerken(self, toestaan):
        """Schakelt de invoer aan/uit (uit zolang het systeem aan het snijden is)."""
        for widget in [*self.bewerk_widgets, *self.snede_invoervelden.values()]:
            if isinstance(widget, ttk.Combobox):
                widget.config(state="readonly" if toestaan else "disabled")
            else:
                widget.config(state=tk.NORMAL if toestaan else tk.DISABLED)
        # 'Voeg toe' mag alleen als er een snede gekozen is
        if toestaan and not self.snede_var.get():
            self.voeg_toe_btn.config(state=tk.DISABLED)

    def invalideer_bevestiging(self):
        """Wordt aangeroepen bij elke wijziging; de opdracht moet dan opnieuw bevestigd worden."""
        if self.bevestigd:
            self.bevestigd = False
            self.start_btn.config(state=tk.DISABLED)
            self._toon_status("Opdracht gewijzigd - bevestig opnieuw om te starten.", "orange")

    def ververs_lijst(self):
        """Bouwt de Treeview opnieuw op uit self.geplande_sneden."""
        self.sneden_lijst.delete(*self.sneden_lijst.get_children())
        tags_per_status = {"Bezig": "bezig", "Klaar": "klaar", "Onderbroken": "onderbroken"}
        for i, snede in enumerate(self.geplande_sneden):
            tag = tags_per_status.get(snede["status"])
            self.sneden_lijst.insert(
                "", "end", iid=str(i),
                values=(i + 1, snede["naam"], snede["weergave"], snede["status"]),
                tags=(tag,) if tag else (),
            )

    def update_snede_opties(self, event=None):
        """Wordt aangeroepen als de operator een profiel kiest."""
        sneden = PROFIELEN[self.profiel_var.get()]["sneden"]
        self.snede_dropdown.config(values=list(sneden.keys()))
        self.snede_var.set('')

        for widget in self.variabelen_frame.winfo_children():
            widget.destroy()
        self.snede_invoervelden.clear()
        self.voeg_toe_btn.config(state=tk.DISABLED)
        self.toon_afbeelding(None)
        self.invalideer_bevestiging()

    def maak_snede_invoervelden(self, event=None):
        """Maakt dynamisch invoervelden aan op basis van de gekozen snede en toont de uitleg-afbeelding."""
        for widget in self.variabelen_frame.winfo_children():
            widget.destroy()
        self.snede_invoervelden.clear()

        snede = PROFIELEN[self.profiel_var.get()]["sneden"][self.snede_var.get()]

        for i, param in enumerate(snede["params"]):
            suffix = " (mm)" if param.kind == "mm" else ""
            self.maak_label(self.variabelen_frame, f"{param.label}{suffix}:").grid(
                row=i, column=0, sticky="e", padx=(0, 10), pady=4)

            if param.kind == "keuze":
                entry = ttk.Combobox(self.variabelen_frame, values=list(param.keuzes.keys()),
                                     state="readonly", width=14, font=(FONT, 11))
            else:
                entry = ttk.Entry(self.variabelen_frame, width=16, font=(FONT, 11))

            entry.grid(row=i, column=1, sticky="w", pady=4)
            self.snede_invoervelden[param.label] = entry

        self.voeg_toe_btn.config(state=tk.NORMAL)
        self.zet_standaard_zijde()
        self.toon_afbeelding(snede)

    def zet_standaard_zijde(self):
        """Eerste snede standaard 'front', tweede 'rear', derde 'front', enzovoort."""
        veld = self.snede_invoervelden.get(ZIJDE.label)
        if isinstance(veld, ttk.Combobox):
            veld.set("front" if len(self.geplande_sneden) % 2 == 0 else "rear")

    def voeg_snede_toe(self):
        """Leest de invoer, zet die direct om naar het eindformaat en voegt de snede toe."""
        naam = self.snede_var.get()
        snede = PROFIELEN[self.profiel_var.get()]["sneden"][naam]

        args = {"cuttype": snede["cuttype"]}
        weergave = []
        for param in snede["params"]:
            ruw = self.snede_invoervelden[param.label].get()
            if not ruw.strip():
                messagebox.showwarning("Invoer ontbreekt", f"Vul a.u.b. de variabele '{param.label}' in.")
                return
            try:
                args[param.key] = param.parse(ruw)
            except ValueError:
                messagebox.showwarning("Ongeldige invoer", f"'{param.label}' moet een getal zijn (kreeg: '{ruw}').")
                return
            weergave.append(f"{param.label}: {ruw}")

        self.geplande_sneden.append({
            "naam": naam,
            "weergave": ", ".join(weergave),
            "args": args,
            "status": "Wachtend",
        })
        self.ververs_lijst()

        self.zet_standaard_zijde()   # volgende snede krijgt de andere zijde
        self._toon_status(f"Snede '{naam}' toegevoegd.", "green")
        self.invalideer_bevestiging()

    def verwijder_snede(self):
        """Verwijdert de geselecteerde sneden uit de lijst."""
        selectie = self.sneden_lijst.selection()
        if not selectie:
            messagebox.showwarning("Geen selectie", "Selecteer eerst een snede in de lijst.")
            return

        # Van achter naar voren verwijderen zodat de indexen kloppen
        for index in sorted((int(iid) for iid in selectie), reverse=True):
            del self.geplande_sneden[index]
        self.ververs_lijst()

        self.zet_standaard_zijde()
        self._toon_status("Snede(n) verwijderd.", "green")
        self.invalideer_bevestiging()

    def wis_alle_sneden(self):
        if not self.geplande_sneden:
            return
        if messagebox.askyesno("Wis alles", "Alle geplande sneden verwijderen?"):
            self.geplande_sneden.clear()
            self.ververs_lijst()
            self.zet_standaard_zijde()
            self._toon_status("Alle sneden gewist.", "green")
            self.invalideer_bevestiging()

    def bouw_opdracht(self):
        """Geeft (profiel_naam, opdracht-dict) terug, of None bij ontbrekende/ongeldige invoer."""
        profiel_naam = self.profiel_var.get()
        if not profiel_naam:
            messagebox.showwarning("Fout", "Kies eerst een profieltype.")
            return None

        profiel_args = {"profiel": PROFIELEN[profiel_naam]["code"]}
        for dim, widget in self.profiel_dimensies.items():
            ruw = widget.get().strip()
            if not ruw:
                messagebox.showwarning("Fout", f"Vul a.u.b. de profiel '{dim}' in.")
                return None
            try:
                profiel_args[dim] = float(ruw.replace(",", ".")) / 1000   # mm -> m
            except ValueError:
                messagebox.showwarning("Fout", f"Profiel '{dim}' moet een getal zijn (kreeg: '{ruw}').")
                return None

        if not self.geplande_sneden:
            messagebox.showwarning("Fout", "Voeg minimaal één snede toe voordat je bevestigt.")
            return None

        return profiel_naam, {
            "profiel_args": profiel_args,
            "cut_args": [s["args"] for s in self.geplande_sneden],
        }

    def toon_bevestiging_scherm(self):
        """Toont een overzicht aan de operator en verstuurt na bevestiging."""
        resultaat = self.bouw_opdracht()
        if resultaat is None:
            return
        profiel_naam, data_pakket = resultaat

        dims = {d: w.get() for d, w in self.profiel_dimensies.items()}
        overzicht = f"Gekozen Profiel: {profiel_naam}\n"
        overzicht += f"Afmetingen: H:{dims['height']} W:{dims['width']} L:{dims['length']} T:{dims['thickness']}\n\n"
        overzicht += "Volgorde van Sneden:\n"
        for i, snede in enumerate(self.geplande_sneden, 1):
            overzicht += f"{i}. {snede['naam']} ({snede['weergave']})\n"

        if messagebox.askyesno("Bevestig Invoer", overzicht + "\n\nIs deze informatie correct om door te sturen naar de machine?"):
            self.stuur_naar_hoofdprogramma(data_pakket)

    def stuur_naar_hoofdprogramma(self, data_pakket):
        """Geeft de definitieve data door aan de besturingskern en geeft Start vrij."""
        self.bevestigd = True
        self.start_btn.config(state=tk.NORMAL)

        # Nieuwe opdracht: alle sneden weer op 'Wachtend'
        for snede in self.geplande_sneden:
            snede["status"] = "Wachtend"
        self.ververs_lijst()
        self.actief_label.config(text="Nu bezig: -")
        self.voortgang.config(maximum=len(self.geplande_sneden), value=0)

        self._toon_status("Opdracht bevestigd - klaar om te starten.", "blue")
        messagebox.showinfo("Succes", "De opdracht is geregistreerd. Je kunt het systeem nu starten.")
        if self.on_job_submitted is not None:
            self.on_job_submitted(data_pakket)

    def start_systeem(self):
        if not self.bevestigd:
            messagebox.showwarning("Niet bevestigd", "Bevestig eerst de opdracht voordat je het systeem start.")
            return

        self.bezig = True
        self.start_btn.config(state=tk.DISABLED)
        self.zet_bewerken(False)
        self.actief_label.config(text="Nu bezig: wacht op eerste snede...")
        self._toon_status("Systeem gestart.", "green")
        print("Commando: START SYSTEEM")
        if self.on_start is not None:
            self.on_start()

    def noodstop(self):
        if self.on_noodstop is not None:
            self.on_noodstop()  # Meld de noodstop aan de besturingskern
        self.bezig = False
        self.bevestigd = False                      # na een noodstop opnieuw bevestigen
        self.start_btn.config(state=tk.DISABLED)
        self.zet_bewerken(True)
        for snede in self.geplande_sneden:
            if snede["status"] == "Bezig":
                snede["status"] = "Onderbroken"
        self.ververs_lijst()

        # Hardware is gestopt: band staat stil, pneumatiek uit, clamp-stand is niet meer zeker
        self._zet_indicator("plasma", False)
        self._zet_indicator("robot", False)
        self._zet_indicator("conveyor", False)
        self._zet_indicator("pneumatiek", False)
        for n in (1, 2, 3):
            self._zet_indicator(f"clamp{n}", None)

        self.actief_label.config(text="Nu bezig: gestopt door noodstop")
        self._toon_status("NOODSTOP GEACTIVEERD!", "red")
        print("Commando: NOODSTOP")

    def reset_interface(self):
        """Wist alle invoer en zet de HMI terug naar de beginstand, klaar voor een nieuw profiel."""
        if self.bezig:
            messagebox.showwarning("Systeem bezig", "Het systeem is nog aan het snijden. "
                                   "Gebruik eerst de noodstop als je wilt stoppen.")
            return
        if not messagebox.askyesno("Reset", "Alle invoer wissen en een nieuw profiel starten?"):
            return
        # De besturingskern mag weigeren (bijv. als de robotthread nog niet klaar is)
        if self.on_reset is not None and self.on_reset() is False:
            messagebox.showwarning("Robot nog bezig", "De robot is nog niet helemaal gestopt. "
                                   "Wacht even en probeer het opnieuw.")
            return

        self.bevestigd = False
        self.start_btn.config(state=tk.DISABLED)

        self.geplande_sneden.clear()
        self.ververs_lijst()

        self.profiel_var.set("")
        for entry in self.profiel_dimensies.values():
            entry.delete(0, tk.END)

        self.snede_var.set("")
        self.snede_dropdown.config(values=[])
        for widget in self.variabelen_frame.winfo_children():
            widget.destroy()
        self.snede_invoervelden.clear()
        self.voeg_toe_btn.config(state=tk.DISABLED)
        self.toon_afbeelding(None)

        self.actief_label.config(text="Nu bezig: -")
        self.voortgang.config(maximum=1, value=0)
        self._toon_status("Reset - klaar voor een nieuw profiel.", "blue")

    def sluiten(self):
        """Sluit het programma af (na bevestiging, en niet tijdens het snijden)."""
        if self.bezig:
            messagebox.showwarning("Systeem bezig", "Het systeem is nog aan het snijden. "
                                   "Gebruik eerst de noodstop voordat je afsluit.")
            return
        if messagebox.askyesno("Afsluiten", "Programma afsluiten?"):
            self.root.destroy()

    # --- PUBLIEKE FUNCTIES VOOR DE BESTURINGSKERN (thread-safe via root.after) ---

    def set_actieve_snede(self, index):
        """Meld dat snede `index` (0-based, volgorde van cut_args) nu wordt gesneden."""
        self.root.after(0, self._set_actieve_snede, index)

    def snijden_klaar(self):
        """Meld dat alle sneden klaar zijn."""
        self.root.after(0, self._snijden_klaar)

    def set_status(self, tekst, kleur="blue"):
        """Toon een vrije statustekst bovenin."""
        self.root.after(0, lambda: self._toon_status(tekst, kleur))

    def set_clamp(self, nummer, dicht):
        """Meld de stand van clamp `nummer` (1-3): True = dicht, False = open, None = onbekend."""
        self.root.after(0, self._zet_indicator, f"clamp{nummer}", dicht)

    def set_conveyor(self, draait):
        """Meld of de transportband beweegt (True) of stilstaat (False)."""
        self.root.after(0, self._zet_indicator, "conveyor", bool(draait))

    def set_robot_beweegt(self, beweegt):
        """Meld of de robotarm beweegt (True) of stilstaat (False)."""
        self.root.after(0, self._zet_indicator, "robot", bool(beweegt))

    def set_plasma(self, aan):
        """Meld of de plasmasnijder aan staat (True) of uit (False)."""
        self.root.after(0, self._zet_indicator, "plasma", bool(aan))

    def set_snijden(self, bezig):
        """Oude naam, blijft bestaan zodat oudere code niet breekt. Gebruik set_plasma()."""
        self.set_plasma(bezig)

    def set_pneumatiek(self, aan):
        """Meld of het pneumatische systeem aan (True) of uit (False) staat."""
        self.root.after(0, self._zet_indicator, "pneumatiek", bool(aan))

    def _set_actieve_snede(self, index):
        totaal = len(self.geplande_sneden)
        if not 0 <= index < totaal:
            return
        for i, snede in enumerate(self.geplande_sneden):
            snede["status"] = "Klaar" if i < index else "Bezig" if i == index else "Wachtend"
        self.ververs_lijst()
        self.sneden_lijst.see(str(index))

        actief = self.geplande_sneden[index]
        self.actief_label.config(text=f"Nu bezig: snede {index + 1} van {totaal}\n{actief['naam']} ({actief['weergave']})")
        self.voortgang.config(maximum=totaal, value=index)

    def _snijden_klaar(self):
        self._zet_indicator("plasma", False)
        self._zet_indicator("robot", False)
        for snede in self.geplande_sneden:
            snede["status"] = "Klaar"
        self.ververs_lijst()
        self.voortgang.config(maximum=max(len(self.geplande_sneden), 1), value=len(self.geplande_sneden))
        self.actief_label.config(text="Nu bezig: alle sneden voltooid")
        self._toon_status("Opdracht voltooid.", "green")

        # Klaar: invoer weer vrijgeven; voor een nieuwe run opnieuw bevestigen
        self.bezig = False
        self.bevestigd = False
        self.start_btn.config(state=tk.DISABLED)
        self.zet_bewerken(True)


# --- Start de Applicatie ---
if __name__ == "__main__":
    root = tk.Tk()

    def simuleer_snijden():
        """Alleen om de UI te testen: loopt elke 2 seconden naar de volgende snede."""
        totaal = len(app.geplande_sneden)

        # Laat ook de indicatoren zien
        app.set_pneumatiek(True)
        app.set_clamp(1, False)
        app.set_clamp(2, False)
        app.set_clamp(3, True)

        def stap(i=0):
            if not app.bezig:          # gestopt via noodstop
                return
            if i < totaal:
                app.set_actieve_snede(i)
                app.set_conveyor(True)
                root.after(800, lambda: app.set_conveyor(False))
                app.set_robot_beweegt(True)
                root.after(1000, lambda: app.set_plasma(True))
                root.after(1600, lambda: app.set_plasma(False))
                root.after(1900, lambda: app.set_robot_beweegt(False))
                root.after(2000, stap, i + 1)
            else:
                app.snijden_klaar()

        stap()

    import sys
    thema = sys.argv[1] if len(sys.argv) > 1 else None   # bijv. 'python HumanInterface.py retro'
    app = DamenPlasmaHMI(root, on_start=simuleer_snijden, thema=thema)
    root.mainloop()