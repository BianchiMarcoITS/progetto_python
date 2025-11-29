import sqlite3
import pandas as pd
import pickle
from datetime import datetime
import os

# Path assoluto alla cartella che contiene questo file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "csv_analyzer.db")


def init_db():
    """Crea le tabelle del database se non esistono.

    Questo metodo inizializza il file SQLite nella cartella del progetto
    creando le tabelle `datasets` e `history` se non presenti. Scrive
    anche un log semplice in `db_init.log` per tracciare le invocazioni.

    Returns:
        None
    """
    print(f"[DB] Inizializzo database in: {DB_PATH}")
    print(f"[DB] BASE_DIR: {BASE_DIR}")
    print(f"[DB] File esiste? {os.path.exists(DB_PATH)}")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                upload_date TEXT NOT NULL,
                data BLOB NOT NULL
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER,
                columns TEXT,
                operation TEXT,
                timestamp TEXT,
                FOREIGN KEY(dataset_id) REFERENCES datasets(id)
            )
        """)

        conn.commit()
        conn.close()
        
        # Verifica che il file sia stato effettivamente creato
        if os.path.exists(DB_PATH):
            print(f"[DB] Database inizializzato correttamente")
            print(f"[DB] Dimensione file: {os.path.getsize(DB_PATH)} bytes")
        else:
            print(f"[DB] ERRORE: File non creato!")
            
    except Exception as e:
        print(f"[DB] ERRORE durante init_db: {e}")
        import traceback
        traceback.print_exc()

    # Scriviamo anche un log persistente in BASE_DIR per verificare l'invocazione
    try:
        log_path = os.path.join(BASE_DIR, 'db_init.log')
        with open(log_path, 'a', encoding='utf-8') as lf:
            from datetime import datetime as _dt
            lf.write(f"{_dt.now().isoformat(timespec='seconds')} - init_db called. DB_PATH={DB_PATH} exists={os.path.exists(DB_PATH)}\n")
    except Exception:
        # non interrompiamo l'esecuzione se il log fallisce
        pass


def save_dataset(name: str, df: pd.DataFrame):
    """
    Salva il DataFrame nel DB.

    Comportamento (Opzione 1 - nome + contenuto semplificato):
    - Se esistono record con lo stesso `name`, confronta il contenuto normalizzato.
      Se trovi un dataset identico, non crea un duplicato e ritorna (existing_id, False).
    - Altrimenti inserisce un nuovo record e ritorna (new_id, True).
    """
    print(f"[DB] Tentativo di salvataggio in: {DB_PATH}")

    def _normalize(df_in: pd.DataFrame) -> pd.DataFrame:
        # Normalizzazione semplice: ordina le colonne, reset indice, arrotonda float, fillna
        d = df_in.copy()
        # Ordina colonne per avere confronto indipendente dall'ordine
        d = d.reindex(sorted(d.columns), axis=1)
        d = d.reset_index(drop=True)
        # Arrotonda float a 6 decimali per evitare differenze minime
        float_cols = d.select_dtypes(include=['float', 'float64', 'float32']).columns
        for c in float_cols:
            d[c] = d[c].round(6)
        # Sostituisci NaN con stringa vuota per confronto coerente
        d = d.fillna('')
        return d

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Cerca record con lo stesso nome
        c.execute("SELECT id, data FROM datasets WHERE name = ?", (name,))
        rows = c.fetchall()

        new_norm = _normalize(df)

        for rid, blob in rows:
            try:
                existing_df = pickle.loads(blob)
                exist_norm = _normalize(existing_df)
                # Confronto diretto
                if exist_norm.equals(new_norm):
                    conn.close()
                    print(f"[DB] Trovato dataset identico per nome '{name}' (id={rid}), non creo duplicato")
                    return rid, False
            except Exception as e:
                print(f"[DB] Impossibile confrontare blob esistente id={rid}: {e}")
                continue

        # Nessun duplicato trovato: inseriamo
        blob = pickle.dumps(df)
        now = datetime.now().isoformat(timespec='seconds')
        c.execute("""
            INSERT INTO datasets (name, upload_date, data)
            VALUES (?, ?, ?)
        """, (name, now, blob))

        conn.commit()
        new_id = c.lastrowid
        conn.close()

        # Verifica: conteggio
        conn_check = sqlite3.connect(DB_PATH)
        c_check = conn_check.cursor()
        c_check.execute("SELECT COUNT(*) FROM datasets")
        count = c_check.fetchone()[0]
        conn_check.close()
        print(f"[DB] Dataset '{name}' salvato nel DB con successo (id={new_id}, totale={count})")
        return new_id, True

    except Exception as e:
        print(f"[DB] ERRORE nel salvataggio di '{name}': {e}")
        import traceback
        traceback.print_exc()
        return None, False


def load_dataset(dataset_id: int):
    """Carica e deserializza un dataset memorizzato nel DB.

    Args:
        dataset_id (int): ID del dataset da caricare.

    Returns:
        pandas.DataFrame | None: DataFrame deserializzato se trovato,
            altrimenti ``None`` se l'ID non esiste.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT data FROM datasets WHERE id = ?", (dataset_id,))
    row = c.fetchone()

    conn.close()

    return pickle.loads(row[0]) if row else None


def list_datasets():
    """Restituisce la lista dei dataset salvati.

    Returns:
        list[tuple]: Lista di tuple ``(id, name, upload_date)`` per i dataset
            presenti nel DB.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT id, name, upload_date FROM datasets")
    rows = c.fetchall()

    conn.close()
    return rows


def save_history(dataset_id: int, columns: list, operation: str):
    """Registra un'operazione eseguita su un dataset nella tabella `history`.

    Args:
        dataset_id (int): ID del dataset coinvolto.
        columns (list): Lista di colonne coinvolte nell'operazione.
        operation (str): Descrizione breve dell'operazione (es. 'filter', 'aggregate').

    Returns:
        None
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    now = datetime.now().isoformat(timespec='seconds')

    c.execute("""
        INSERT INTO history (dataset_id, columns, operation, timestamp)
        VALUES (?, ?, ?, ?)
    """, (dataset_id, ",".join(columns), operation, now))

    conn.commit()
    conn.close()


def load_history():
    """Recupera la cronologia delle operazioni eseguite su dataset.

    Returns:
        list[tuple]: Lista di righe con (history.id, dataset.name, columns, operation, timestamp),
            ordinate per timestamp decrescente.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        SELECT h.id, d.name, h.columns, h.operation, h.timestamp
        FROM history h
        LEFT JOIN datasets d ON h.dataset_id = d.id
        ORDER BY h.timestamp DESC
    """)

    rows = c.fetchall()
    conn.close()

    return rows

# devo fare un check del csv, così da non crearne di duplicati