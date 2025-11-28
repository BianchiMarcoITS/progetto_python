"""
analyzer.py
-----------
Funzioni per filtrare i dati e calcolare statistiche.
"""

import pandas as pd


def apply_filters(df: pd.DataFrame, columns: list, filters: list):
    """
    Applica una lista di filtri al DataFrame.
    filters = [(col, operatore, valore)]
    """
    filtered = df.copy()

    for col, op, value in filters:
        if op == "between":
            min_v, max_v = value
            filtered = filtered[(filtered[col] >= min_v) & (filtered[col] <= max_v)]

        elif op == "in":
            filtered = filtered[filtered[col].isin(value)]

    return filtered


def compute_statistics(df: pd.DataFrame, columns: list, operation: str):
    """
    Calcola statistiche sulla base dell'operazione scelta.
    """
    results = {}

    # Conteggio è applicabile a qualsiasi tipo di colonna (conta valori non-null)
    if operation == "Conteggio":
        for col in columns:
            results[col] = int(df[col].count())
        return results

    # Le altre operazioni sono sensate solo per colonne numeriche
    for col in columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            if operation == "Media":
                results[col] = df[col].mean()
            elif operation == "Somma":
                results[col] = df[col].sum()
            elif operation == "Massimo":
                results[col] = df[col].max()
            elif operation == "Minimo":
                results[col] = df[col].min()

    return results
