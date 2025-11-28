"""
data_loader.py
--------------
Gestisce il caricamento sicuro e robusto dei file CSV.
"""

import pandas as pd
from typing import Tuple, Optional


def load_csv(file) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Carica un CSV provando diversi encoding e gestendo errori comuni.
    Ritorna (df, errore)
    """

    encodings = ["utf-8", "latin1", "cp1252"]
    last_error = None

    for enc in encodings:
        try:
            file.seek(0)
            df = pd.read_csv(file, sep=None, engine="python", encoding=enc)
            return df, None
        except Exception as e:
            last_error = str(e)

    return None, f"Errore nel caricamento CSV: {last_error}"
