import tkinter as tk
from tkinter import ttk, messagebox
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Definitie van parameters, sneden en profielen
# Alles wat je wilt aanpassen/uitbreiden staat hier; de GUI past zich vanzelf aan.
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
ZIJDE = Param("left/right", "side", "keuze", {"left": "left", "right": "right"})
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
                "params": [Param("Y(angle)", "A", "float"), ZIJDE],
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
    def __init__(self, root, on_job_submitted=None, on_start=None, on_noodstop=None):
        self.root = root
        self.on_job_submitted = on_job_submitted
        self.on_start = on_start
        self.on_noodstop = on_noodstop
        self.root.title("Damen Robot Plasmasnijder HMI")

        # Maak de applicatie full-screen, met de mogelijkheid om te sluiten via 'Escape'
        self.root.attributes('-fullscreen', True)
        self.root.bind("<Escape>", lambda event: self.root.attributes("-fullscreen", False))

        # Elke geplande snede:
        # {"naam": ..., "weergave": ..., "args": {...kant-en-klaar...}, "status": "Wachtend"}
        self.geplande_sneden = []
        self.bevestigd = False   # True zodra de operator de opdracht heeft bevestigd
        self.bezig = False       # True zodra het systeem is gestart en aan het snijden is

        self.bouw_interface()

    def bouw_interface(self):
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- SECTIE 1: Status & Controls ---
        status_frame = tk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        self.status_label = tk.Label(status_frame, text="Status: Wacht op invoer...", font=("Arial", 14, "bold"), fg="blue")
        self.status_label.pack(side=tk.LEFT)

        stop_btn = tk.Button(status_frame, text="NOODSTOP", bg="red", fg="white", font=("Arial", 12, "bold"), command=self.noodstop)
        stop_btn.pack(side=tk.RIGHT, padx=5)

        # Start is pas beschikbaar na bevestiging van de opdracht
        self.start_btn = tk.Button(status_frame, text="START SYSTEEM", bg="green", fg="white", font=("Arial", 12, "bold"), command=self.start_systeem, state=tk.DISABLED)
        self.start_btn.pack(side=tk.RIGHT, padx=5)

        # --- Voortgang: welke snede is actief ---
        voortgang_frame = tk.Frame(main_frame)
        voortgang_frame.pack(fill=tk.X, pady=(0, 10))

        self.actief_label = tk.Label(voortgang_frame, text="Nu bezig: -", font=("Arial", 12))
        self.actief_label.pack(anchor="w")
        self.voortgang = ttk.Progressbar(voortgang_frame, orient=tk.HORIZONTAL, mode="determinate", maximum=1, value=0)
        self.voortgang.pack(fill=tk.X, pady=(5, 0))

        # --- SECTIE 2: Profiel Selectie & Afmetingen ---
        profiel_frame = tk.LabelFrame(main_frame, text="1. Profiel Eigenschappen", font=("Arial", 12, "bold"), padx=10, pady=10)
        profiel_frame.pack(fill=tk.X, pady=10)

        tk.Label(profiel_frame, text="Kies Profiel:").grid(row=0, column=0, sticky="w", pady=5)
        self.profiel_var = tk.StringVar()
        self.profiel_dropdown = ttk.Combobox(profiel_frame, textvariable=self.profiel_var, values=list(PROFIELEN.keys()), state="readonly", width=30)
        self.profiel_dropdown.grid(row=0, column=1, sticky="w", pady=5)
        self.profiel_dropdown.bind("<<ComboboxSelected>>", self.update_snede_opties)

        self.profiel_dimensies = {}
        for i, dim in enumerate(DIMENSIES):
            tk.Label(profiel_frame, text=f"{dim.capitalize()} (mm):").grid(row=1, column=i*2, sticky="e", padx=5)
            var = tk.StringVar()
            # Als een afmeting verandert nadat er bevestigd is, moet opnieuw bevestigd worden
            var.trace_add("write", lambda *args: self.invalideer_bevestiging())
            entry = tk.Entry(profiel_frame, width=10, textvariable=var)
            entry.grid(row=1, column=i*2+1, sticky="w", padx=5)
            self.profiel_dimensies[dim] = entry

        # --- SECTIE 3: Snede Selectie (Dynamisch) ---
        self.snede_frame = tk.LabelFrame(main_frame, text="2. Voeg Sneden Toe", font=("Arial", 12, "bold"), padx=10, pady=10)
        self.snede_frame.pack(fill=tk.X, pady=10)

        tk.Label(self.snede_frame, text="Kies Snede:").grid(row=0, column=0, sticky="w", pady=5)
        self.snede_var = tk.StringVar()
        self.snede_dropdown = ttk.Combobox(self.snede_frame, textvariable=self.snede_var, state="readonly", width=30)
        self.snede_dropdown.grid(row=0, column=1, sticky="w", pady=5)
        self.snede_dropdown.bind("<<ComboboxSelected>>", self.maak_snede_invoervelden)

        self.variabelen_frame = tk.Frame(self.snede_frame)
        self.variabelen_frame.grid(row=1, column=0, columnspan=4, sticky="w", pady=10)
        self.snede_invoervelden = {}

        self.voeg_toe_btn = tk.Button(self.snede_frame, text="Voeg Snede Toe Aan Lijst", command=self.voeg_snede_toe, state=tk.DISABLED)
        self.voeg_toe_btn.grid(row=2, column=0, columnspan=2, pady=10, sticky="w")

        # --- SECTIE 4: Overzicht van Geplande Sneden ---
        lijst_frame = tk.LabelFrame(main_frame, text="3. Volgorde van Geplande Sneden", font=("Arial", 12, "bold"), padx=10, pady=10)
        lijst_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        tabel_frame = tk.Frame(lijst_frame)
        tabel_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("nr", "type", "params", "status")
        self.sneden_lijst = ttk.Treeview(tabel_frame, columns=columns, show="headings", height=8)
        self.sneden_lijst.heading("nr", text="#")
        self.sneden_lijst.heading("type", text="Snede Type")
        self.sneden_lijst.heading("params", text="Parameters")
        self.sneden_lijst.heading("status", text="Status")
        self.sneden_lijst.column("nr", width=40, anchor="center", stretch=False)
        self.sneden_lijst.column("type", width=150, stretch=False)
        self.sneden_lijst.column("params", width=500)
        self.sneden_lijst.column("status", width=110, anchor="center", stretch=False)
        self.sneden_lijst.tag_configure("bezig", background="#fff3b0")
        self.sneden_lijst.tag_configure("klaar", background="#c8f7c5")
        self.sneden_lijst.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        scrollbar = ttk.Scrollbar(tabel_frame, orient=tk.VERTICAL, command=self.sneden_lijst.yview)
        self.sneden_lijst.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        knoppen_frame = tk.Frame(lijst_frame)
        knoppen_frame.pack(fill=tk.X, pady=(10, 0))
        self.verwijder_btn = tk.Button(knoppen_frame, text="Verwijder Geselecteerde Snede", command=self.verwijder_snede)
        self.verwijder_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.wis_btn = tk.Button(knoppen_frame, text="Wis Alle Sneden", command=self.wis_alle_sneden)
        self.wis_btn.pack(side=tk.LEFT)

        # --- SECTIE 5: Bevestig & Verzend ---
        self.bevestig_btn = tk.Button(main_frame, text="Klaar Met Invoeren - Bekijk & Bevestig", bg="blue", fg="white", font=("Arial", 14, "bold"), command=self.toon_bevestiging_scherm)
        self.bevestig_btn.pack(fill=tk.X, pady=20)

        # Alles wat tijdens het snijden vergrendeld moet worden
        self.bewerk_widgets = [
            self.profiel_dropdown, self.snede_dropdown, self.voeg_toe_btn,
            self.verwijder_btn, self.wis_btn, self.bevestig_btn,
            *self.profiel_dimensies.values(),
        ]

    # --- LOGICA FUNCTIES ---

    def zet_bewerken(self, toestaan):
        """Schakelt de invoer aan/uit (uit zolang het systeem aan het snijden is)."""
        for widget in self.bewerk_widgets:
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
            self.status_label.config(text="Status: Opdracht gewijzigd - bevestig opnieuw om te starten.", fg="orange")

    def ververs_lijst(self):
        """Bouwt de Treeview opnieuw op uit self.geplande_sneden."""
        self.sneden_lijst.delete(*self.sneden_lijst.get_children())
        tags_per_status = {"Bezig": "bezig", "Klaar": "klaar"}
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
        self.invalideer_bevestiging()

    def maak_snede_invoervelden(self, event=None):
        """Maakt dynamisch invoervelden aan op basis van de gekozen snede."""
        for widget in self.variabelen_frame.winfo_children():
            widget.destroy()
        self.snede_invoervelden.clear()

        snede = PROFIELEN[self.profiel_var.get()]["sneden"][self.snede_var.get()]

        for i, param in enumerate(snede["params"]):
            tk.Label(self.variabelen_frame, text=f"{param.label}:").grid(row=0, column=i*2, sticky="e", padx=5)

            if param.kind == "keuze":
                entry = ttk.Combobox(self.variabelen_frame, values=list(param.keuzes.keys()), state="readonly", width=12)
            else:
                entry = tk.Entry(self.variabelen_frame, width=10)

            entry.grid(row=0, column=i*2+1, sticky="w", padx=5)
            self.snede_invoervelden[param.label] = entry

        self.voeg_toe_btn.config(state=tk.NORMAL)

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

        self.status_label.config(text=f"Status: Snede '{naam}' toegevoegd.", fg="green")
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

        self.status_label.config(text="Status: Snede(n) verwijderd.", fg="green")
        self.invalideer_bevestiging()

    def wis_alle_sneden(self):
        if not self.geplande_sneden:
            return
        if messagebox.askyesno("Wis alles", "Alle geplande sneden verwijderen?"):
            self.geplande_sneden.clear()
            self.ververs_lijst()
            self.status_label.config(text="Status: Alle sneden gewist.", fg="green")
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

        self.status_label.config(text="Status: Opdracht bevestigd - klaar om te starten.", fg="blue")
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
        self.status_label.config(text="Status: Systeem gestart.", fg="green")
        print("Commando: START SYSTEEM")
        if self.on_start is not None:
            self.on_start()

    def noodstop(self):
        self.on_noodstop()  # Meld de noodstop aan de besturingskern
        self.bezig = False
        self.bevestigd = False                      # na een noodstop opnieuw bevestigen
        self.start_btn.config(state=tk.DISABLED)
        self.zet_bewerken(True)
        for snede in self.geplande_sneden:
            if snede["status"] == "Bezig":
                snede["status"] = "Onderbroken"
        self.ververs_lijst()
        self.actief_label.config(text="Nu bezig: gestopt door noodstop")
        self.status_label.config(text="Status: NOODSTOP GEACTIVEERD!", fg="red")
        print("Commando: NOODSTOP")

    # --- PUBLIEKE FUNCTIES VOOR DE BESTURINGSKERN (thread-safe via root.after) ---

    def set_actieve_snede(self, index):
        """Meld dat snede `index` (0-based, volgorde van cut_args) nu wordt gesneden."""
        self.root.after(0, self._set_actieve_snede, index)

    def snijden_klaar(self):
        """Meld dat alle sneden klaar zijn."""
        self.root.after(0, self._snijden_klaar)

    def set_status(self, tekst, kleur="blue"):
        """Toon een vrije statustekst bovenin."""
        self.root.after(0, lambda: self.status_label.config(text=f"Status: {tekst}", fg=kleur))

    def _set_actieve_snede(self, index):
        totaal = len(self.geplande_sneden)
        if not 0 <= index < totaal:
            return
        for i, snede in enumerate(self.geplande_sneden):
            snede["status"] = "Klaar" if i < index else "Bezig" if i == index else "Wachtend"
        self.ververs_lijst()
        self.sneden_lijst.see(str(index))

        actief = self.geplande_sneden[index]
        self.actief_label.config(text=f"Nu bezig: snede {index + 1} van {totaal} - {actief['naam']} ({actief['weergave']})")
        self.voortgang.config(maximum=totaal, value=index)

    def _snijden_klaar(self):
        for snede in self.geplande_sneden:
            snede["status"] = "Klaar"
        self.ververs_lijst()
        self.voortgang.config(maximum=max(len(self.geplande_sneden), 1), value=len(self.geplande_sneden))
        self.actief_label.config(text="Nu bezig: alle sneden voltooid")
        self.status_label.config(text="Status: Opdracht voltooid.", fg="green")

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

        def stap(i=0):
            if not app.bezig:          # gestopt via noodstop
                return
            if i < totaal:
                app.set_actieve_snede(i)
                root.after(2000, stap, i + 1)
            else:
                app.snijden_klaar()

        stap()

    app = DamenPlasmaHMI(root, on_start=simuleer_snijden)
    root.mainloop()