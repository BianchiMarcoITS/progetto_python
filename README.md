# CSV Analyzer

Applicazione Python per analizzare file CSV, filtrare dati, calcolare statistiche, generare grafici e esportare risultati tramite Streamlit.

## 🎯 Funzionalità principali
- ✅ **Caricamento CSV** e anteprima dati con supporto a molteplici encoding
- ✅ **Filtri dinamici** per colonne numeriche (slider range) e categoriche (multiselect)
- ✅ **Analisi statistiche**: Media, Somma, Conteggio, Massimo, Minimo (con supporto colonne non-numeriche)
- ✅ **Generazione grafici** via Matplotlib: Barre, Linee, Istogramma, Torta
- ✅ **Aggregazione rapida**: raggruppa per colonna categorica, aggrega colonne numeriche con operazioni (sum, mean, count, max, min)
## Funzionalità principali
- Caricamento CSV e anteprima
- Filtri dinamici per colonne selezionate
- Analisi statistiche: Media, Somma, Conteggio, Massimo, Minimo
- Generazione grafici via Matplotlib (Barre, Linee, Istogramma, Torta)
- ✅ **Aggregazione rapida**: raggruppa per colonna categorica, aggrega colonne numeriche con operazioni (sum, mean, count, max, min)
- ✅ **Salvataggio dataset** nel DB SQLite (BLOB storage) con deduplicazione automatica (nome + contenuto normalizzato)
- ✅ **Storico operazioni** nella tabella `history`
- ✅ **Esportazione multiformato**:
  - CSV (dati filtrati/aggregati)
  - PNG (grafici)
  - PDF (grafici)
  - Excel (dati filtrati/aggregati con formattazione basilare)

## 📋 Requisiti
- Python 3.10+ 
- Dipendenze (vedi `requirements.txt`):
  - `streamlit` (GUI)
  - `pandas` (data handling)
  - `matplotlib` (plotting)
  - `openpyxl` (Excel export)
  - `reportlab` (PDF generation)
  - E altre (pillow, altair, numpy, etc.)

## 🚀 Installazione e avvio

### 1. Clone o Scarica il progetto
```powershell
cd C:\Users\Bianc\Desktop\progetto_python
```

### 2. Installa dipendenze
```powershell
python -m pip install -r requirements.txt
```

### 3. Avvia l'app
```powershell
streamlit run app.py
```

L'app si aprirà automaticamente in un browser a `http://localhost:8501/`.

## 📖 Come usare l'applicazione

### Step 1: Carica un CSV
1. Clicca su "Seleziona un CSV" e scegli un file
2. L'app carica il file e lo salva automaticamente nel database SQLite
3. Se il file è già stato caricato (stesso nome + contenuto), l'app lo riconosce come duplicato

### Step 2: Scegli colonne
1. Usa il multiselect "Colonne da analizzare" per scegliere le colonne interessanti
2. I filtri si aggiorneranno dinamicamente basati sulle colonne selezionate

### Step 3: Applica filtri
1. **Colonne numeriche**: usa lo slider per selezionare un range di valori
2. **Colonne categoriche**: usa il multiselect per scegliere i valori desiderati
3. La tabella "Risultato filtrato" si aggiorna in tempo reale

### Step 4: Analisi statistiche
1. Seleziona un'operazione dal menu "Tipo di analisi" (Media, Somma, Conteggio, Massimo, Minimo)
2. I risultati si mostrano in una tabella

### Step 5: Genera grafici
1. Scegli il tipo di grafico: **Barre**, **Linee**, **Istogramma**
2. Il grafico si mostra e puoi esportarlo in:
   - **PNG** (formato raster)
   - **PDF** (vettoriale, più compatto)

### Step 6: Aggregazione rapida (opzionale)
1. Se ci sono colonne categoriche, puoi creare un'aggregazione:
   - Scegli la colonna su cui raggruppare
   - Seleziona le colonne numeriche da aggregare
   - Scegli l'operazione (sum, mean, count, max, min)
2. I risultati aggregati si mostrano in una tabella con grafico e opzioni di export

### Step 7: Esporta risultati
- **Dati filtrati**: CSV o Excel
- **Grafici**: PNG o PDF
- **Dati aggregati**: CSV, Excel, con grafici (PNG/PDF)

---

## 🗄️ Database

### Struttura
L'app usa SQLite con file `csv_analyzer.db` (creato automaticamente nella root del progetto).

**Tabella `datasets`:**
```
id (INTEGER PRIMARY KEY)
name (TEXT)
upload_date (TIMESTAMP)
data (BLOB)  <- Pickle di DataFrame
```

**Tabella `history`:**
```
id (INTEGER PRIMARY KEY)
dataset_id (INTEGER FK)
operation (TEXT)
filters (TEXT)
timestamp (TIMESTAMP)
```

### Deduplicazione
L'app evita di creare duplicati confrontando:
- Nome del file (normalizzato: minuscolo, spazi trimmed)
- Contenuto (hash del pickle del DataFrame)

Se carica due CSV con lo stesso nome e lo stesso contenuto, viene usato il dataset esistente.

---

## 📤 Export

### CSV Export
- Esporta i dati filtrati o aggregati in formato CSV
- Facilmente apribile in Excel, Google Sheets, o altri tool di analisi

### PNG Export
- Esporta grafici in formato raster (PNG)
- Buono per email e condivisione veloce
- Dimensione file: più grande di PDF

### PDF Export
- Esporta grafici in formato vettoriale (PDF)
- Migliore qualità di stampa
- Dimensione file: più compatta
- Usa `reportlab` e `matplotlib` per la generazione

### Excel Export
- Esporta dati in `.xlsx` (formato Excel moderno)
- Include formattazione basilare (autowidth delle colonne)
- Consente ulteriori elaborazioni in Excel
- Usa `openpyxl` per la generazione

---

## 🔧 Troubleshooting

### Il database non si crea
- Assicurati di avere i permessi di scrittura nella cartella del progetto
- Controlla il file `db_init.log` per diagnostica

### L'export in Excel non funziona
- Verifica che `openpyxl` sia installato: `python -c "import openpyxl; print(openpyxl.__version__)"`
- Se non è presente: `pip install openpyxl`

### L'export in PDF non funziona
- Verifica che `reportlab` sia installato: `python -c "import reportlab; print(reportlab.Version)"`
- Se non è presente: `pip install reportlab`

### Errore "StreamlitDuplicateElementId"
- Ricarica l'app (F5 nel browser)
- Se persiste, pulisci la cache: cancella la cartella `.streamlit` in `~/.streamlit/`

### L'app è lenta con dataset molto grandi
- Usa il preview per testare con un campione dei dati
- Aggiungi un filtro per ridurre le righe
- Aumenta la RAM disponibile al processo Python

---

## 📚 File del progetto

```
progetto_python/
├── app.py                      # Applicazione principale (Streamlit)
├── database.py                 # Funzioni DB (init, save, load, list)
├── modules/
│   ├── analyzer.py            # Logica filtri e statistiche
│   ├── data_loader.py         # Caricamento CSV con encoding detection
│   └── plotter.py             # Generazione grafici
├── requirements.txt            # Dipendenze Python
├── README.md                   # Questo file
├── .gitignore                  # Esclusioni Git
├── csv_analyzer.db            # Database SQLite (generato)
├── db_init.log                # Log diagnostica DB
└── __pycache__/               # Cache Python
```

---

## 🧪 Verifica del codice

Per verificare la sintassi di tutti i file Python:
```powershell
python -m py_compile app.py database.py modules/analyzer.py modules/data_loader.py modules/plotter.py
```

Se non ci sono errori, l'output sarà silenzioso.

---

## 📦 Dipendenze in dettaglio

| Pacchetto | Versione | Uso |
|-----------|----------|-----|
| streamlit | 1.51.0 | Framework GUI |
| pandas | 2.3.3 | Data manipulation |
| matplotlib | 3.10.7 | Plotting |
| openpyxl | 3.1.2 | Excel export |
| reportlab | 4.1.3 | PDF generation |
| numpy | 2.3.5 | Numerical computing |
| pillow | 12.0.0 | Image handling |
| altair | 5.5.0 | (optional) Alternative plotting |

---

## 🔄 Workflow tipico

1. **Upload CSV** → File salvato nel DB
2. **Seleziona colonne** → Filtri creati dinamicamente
3. **Applica filtri** → Tabella si aggiorna
4. **Vedi statistiche** → Media, somma, conteggio, min, max
5. **Genera grafico** → Barre, linee, istogramma, torta
6. **Aggrega (opzionale)** → Groupby + operazione di aggregazione
7. **Esporta risultati** → CSV, Excel, PNG, PDF

---

## 🚀 Prossimi miglioramenti (futuri)

- [ ] Support per file Excel e Parquet
- [ ] Visualizzazione tabelle interattive (plotly)
- [ ] Report PDF con layout avanzato (tabella + grafici combinati)
- [ ] Autenticazione e permessi per l'accesso ai dataset
- [ ] API REST per integrazione con altri sistemi
- [ ] Test automatici e CI/CD su GitHub Actions
- [ ] Support per dataset molto grandi (chunking, sampling)

---

## 📧 Contatti e Supporto

Se hai domande, problemi o suggerimenti:
- Controlla i log (`db_init.log`)
- Testa la sintassi con `py_compile`
- Verifica che tutte le dipendenze siano installate

---

## 📝 Note sulla deduplicazione

L'app usa una strategia di deduplicazione basata su:
1. **Nome normalizzato**: minuscolo + trim dei whitespace
2. **Hash del contenuto**: hash del pickle del DataFrame

Questo significa che se carichi due file con:
- ✅ Stesso nome, stesso contenuto → Duplicato (usa il vecchio)
- ✅ Stesso nome, contenuto diverso → Nuovo dataset (override del vecchio)
- ✅ Nome diverso, stesso contenuto → Nuovo dataset (non è duplicato)

---
