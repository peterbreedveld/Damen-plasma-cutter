import tkinter as tk
from tkinter import ttk, messagebox
import json

class DamenPlasmaHMI:
    def __init__(self, root):
        self.root = root
        self.root.title("Damen Robot Plasmasnijder HMI")
        
        # Maak de applicatie full-screen, met de mogelijkheid om te sluiten via 'Escape'
        self.root.attributes('-fullscreen', True)
        self.root.bind("<Escape>", lambda event: self.root.attributes("-fullscreen", False))

        # --- Modulaire Definitie van Sneden en Variabelen ---
        # Hier kun je later makkelijk profielen, sneden en variabelen toevoegen of aanpassen.
        self.snij_definities = {
            "Rectangular profile": {
                "V-cut": ["orientation", "position", "left/right"],
                "Type 85": ["Y(angle)", "left/right"]
            },
            "Holland profile": {
                "Type 6": ["Angle", "Position", "left/right"],
                "Type 9": ["Angle", "Position", "left/right"]
            },
            "Angular profile": {
                "Type 11": ["X", "Y", "Angle", "Position", "left/right"],
                "Type 83": ["Thickness", "Position", "left/right"]
            }
        }

        # Interne opslag voor de gekozen sneden
        self.geplande_sneden = []

        self.bouw_interface()

    def bouw_interface(self):
        # Hoofdframe met wat padding
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- SECTIE 1: Status & Controls ---
        status_frame = tk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.status_label = tk.Label(status_frame, text="Status: Wacht op invoer...", font=("Arial", 14, "bold"), fg="blue")
        self.status_label.pack(side=tk.LEFT)

        stop_btn = tk.Button(status_frame, text="NOODSTOP", bg="red", fg="white", font=("Arial", 12, "bold"), command=self.noodstop)
        stop_btn.pack(side=tk.RIGHT, padx=5)

        start_btn = tk.Button(status_frame, text="START SYSTEEM", bg="green", fg="white", font=("Arial", 12, "bold"), command=self.start_systeem)
        start_btn.pack(side=tk.RIGHT, padx=5)

        # --- SECTIE 2: Profiel Selectie & Afmetingen ---
        profiel_frame = tk.LabelFrame(main_frame, text="1. Profiel Eigenschappen", font=("Arial", 12, "bold"), padx=10, pady=10)
        profiel_frame.pack(fill=tk.X, pady=10)

        tk.Label(profiel_frame, text="Kies Profiel:").grid(row=0, column=0, sticky="w", pady=5)
        self.profiel_var = tk.StringVar()
        self.profiel_dropdown = ttk.Combobox(profiel_frame, textvariable=self.profiel_var, values=list(self.snij_definities.keys()), state="readonly", width=30)
        self.profiel_dropdown.grid(row=0, column=1, sticky="w", pady=5)
        self.profiel_dropdown.bind("<<ComboboxSelected>>", self.update_snede_opties)

        # Variabelen voor het profiel
        self.profiel_dimensies = {}
        dimensies = ["height", "width", "length", "thickness"]
        for i, dim in enumerate(dimensies):
            tk.Label(profiel_frame, text=f"{dim.capitalize()} (mm):").grid(row=1, column=i*2, sticky="e", padx=5)
            entry = tk.Entry(profiel_frame, width=10)
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

        # Frame voor de dynamische variabelen van de gekozen snede
        self.variabelen_frame = tk.Frame(self.snede_frame)
        self.variabelen_frame.grid(row=1, column=0, columnspan=4, sticky="w", pady=10)
        self.snede_invoervelden = {}

        self.voeg_toe_btn = tk.Button(self.snede_frame, text="Voeg Snede Toe Aan Lijst", command=self.voeg_snede_toe, state=tk.DISABLED)
        self.voeg_toe_btn.grid(row=2, column=0, columnspan=2, pady=10, sticky="w")

        # --- SECTIE 4: Overzicht van Geplande Sneden ---
        lijst_frame = tk.LabelFrame(main_frame, text="3. Volgorde van Geplande Sneden", font=("Arial", 12, "bold"), padx=10, pady=10)
        lijst_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        columns = ("#1", "#2")
        self.sneden_lijst = ttk.Treeview(lijst_frame, columns=columns, show="headings", height=8)
        self.sneden_lijst.heading("#1", text="Snede Type")
        self.sneden_lijst.heading("#2", text="Parameters")
        self.sneden_lijst.column("#1", width=150)
        self.sneden_lijst.column("#2", width=600)
        self.sneden_lijst.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        scrollbar = ttk.Scrollbar(lijst_frame, orient=tk.VERTICAL, command=self.sneden_lijst.yview)
        self.sneden_lijst.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --- SECTIE 5: Bevestig & Verzend ---
        bevestig_btn = tk.Button(main_frame, text="Klaar Met Invoeren - Bekijk & Bevestig", bg="blue", fg="white", font=("Arial", 14, "bold"), command=self.toon_bevestiging_scherm)
        bevestig_btn.pack(fill=tk.X, pady=20)

    # --- LOGICA FUNCTIES ---

    def update_snede_opties(self, event=None):
        """Wordt aangeroepen als de operator een profiel kiest."""
        gekozen_profiel = self.profiel_var.get()
        beschikbare_sneden = list(self.snij_definities[gekozen_profiel].keys())
        
        # Reset de snede dropdown
        self.snede_dropdown.config(values=beschikbare_sneden)
        self.snede_var.set('')
        
        # Wis de oude invoervelden
        for widget in self.variabelen_frame.winfo_children():
            widget.destroy()
        
        self.voeg_toe_btn.config(state=tk.DISABLED)

    def maak_snede_invoervelden(self, event=None):
        """Maakt dynamisch invoervelden aan op basis van de gekozen snede."""
        # Wis huidige velden
        for widget in self.variabelen_frame.winfo_children():
            widget.destroy()
        self.snede_invoervelden.clear()

        gekozen_profiel = self.profiel_var.get()
        gekozen_snede = self.snede_var.get()
        variabelen = self.snij_definities[gekozen_profiel][gekozen_snede]

        for i, var_naam in enumerate(variabelen):
            tk.Label(self.variabelen_frame, text=f"{var_naam}:").grid(row=0, column=i*2, sticky="e", padx=5)
            
            # Maak een dropdown voor left/right, anders een tekstveld
            if var_naam.lower() == "left/right":
                entry = ttk.Combobox(self.variabelen_frame, values=["Left", "Right"], state="readonly", width=10)
            else:
                entry = tk.Entry(self.variabelen_frame, width=10)
                
            entry.grid(row=0, column=i*2+1, sticky="w", padx=5)
            self.snede_invoervelden[var_naam] = entry

        self.voeg_toe_btn.config(state=tk.NORMAL)

    def voeg_snede_toe(self):
        """Leest de variabelen uit en voegt de snede toe aan de visuele lijst."""
        gekozen_snede = self.snede_var.get()
        
        # Verzamel alle ingevulde parameters
        params = {}
        for var_naam, invoer_widget in self.snede_invoervelden.items():
            waarde = invoer_widget.get()
            if not waarde:
                messagebox.showwarning("Invoer ontbreekt", f"Vul a.u.b. de variabele '{var_naam}' in.")
                return
            params[var_naam] = waarde
        
        # Voeg toe aan interne lijst en Treeview
        self.geplande_sneden.append({
            "type": gekozen_snede,
            "parameters": params
        })
        
        param_string = ", ".join([f"{k}: {v}" for k, v in params.items()])
        self.sneden_lijst.insert("", "end", values=(gekozen_snede, param_string))
        
        self.status_label.config(text=f"Status: Snede '{gekozen_snede}' toegevoegd.", fg="green")

    def toon_bevestiging_scherm(self):
        """Verzamelt alle data en toont een overzicht aan de operator."""
        # 1. Valideer profiel afmetingen
        gekozen_profiel = self.profiel_var.get()
        if not gekozen_profiel:
            messagebox.showwarning("Fout", "Kies eerst een profieltype.")
            return

        profiel_data = {}
        for dim, widget in self.profiel_dimensies.items():
            waarde = widget.get()
            if not waarde:
                messagebox.showwarning("Fout", f"Vul a.u.b. de profiel '{dim}' in.")
                return
            profiel_data[dim] = waarde

        if not self.geplande_sneden:
            messagebox.showwarning("Fout", "Voeg minimaal één snede toe voordat je bevestigt.")
            return

        # 2. Bouw het overzichtsbericht
        overzicht = f"Gekozen Profiel: {gekozen_profiel}\n"
        overzicht += f"Afmetingen: H:{profiel_data['height']} W:{profiel_data['width']} L:{profiel_data['length']} T:{profiel_data['thickness']}\n\n"
        overzicht += "Volgorde van Sneden:\n"
        for i, snede in enumerate(self.geplande_sneden, 1):
            param_string = ", ".join([f"{k}:{v}" for k, v in snede['parameters'].items()])
            overzicht += f"{i}. {snede['type']} ({param_string})\n"

        # 3. Vraag om bevestiging
        bevestigd = messagebox.askyesno("Bevestig Invoer", overzicht + "\n\nIs deze informatie correct om door te sturen naar de machine?")
        
        if bevestigd:
            self.stuur_naar_hoofdprogramma(gekozen_profiel, profiel_data, self.geplande_sneden)

    def stuur_naar_hoofdprogramma(self, profiel_type, dimensies, sneden):
        """Functie die de definitieve data doorgeeft aan de besturingskern."""
        # Hier bouw je het uiteindelijke 'pakketje' data
        data_pakket = {
            "profiel_type": profiel_type,
            "dimensies": dimensies,
            "sneden_volgorde": sneden
        }
        
        # Voor nu printen we het in JSON formaat in de console
        print("\n--- DATA VERZONDEN NAAR HOOFDPROGRAMMA ---")
        print(json.dumps(data_pakket, indent=4))
        
        self.status_label.config(text="Status: Data succesvol verstuurd naar besturingskern.", fg="blue")
        messagebox.showinfo("Succes", "De opdracht is geregistreerd en verzonden!")

    def start_systeem(self):
        self.status_label.config(text="Status: Systeem gestart.", fg="green")
        print("Commando: START SYSTEEM")

    def noodstop(self):
        self.status_label.config(text="Status: NOODSTOP GEACTIVEERD!", fg="red")
        print("Commando: NOODSTOP")

# --- Start de Applicatie ---
if __name__ == "__main__":
    root = tk.Tk()
    app = DamenPlasmaHMI(root)
    root.mainloop()
    