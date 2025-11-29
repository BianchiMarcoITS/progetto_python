"""
plotter.py
----------
Genera grafici usando matplotlib.
"""

import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import pandas as pd

def generate_plot(df: pd.DataFrame, columns: list, chart_type: str, top_n: int = 20, max_xticks: int = 20, force_horizontal: bool = False):
    """
    Genera un grafico matplotlib basato sui dati filtrati.
    """
    def _format_y(ax):
        try:
            ax.yaxis.set_major_formatter(ScalarFormatter())
            ax.ticklabel_format(style='plain', axis='y')
        except Exception:
            pass

    def _reduce_xticks(ax, max_ticks=20):
        try:
            ticks = ax.get_xticks()
            if len(ticks) > max_ticks:
                step = max(1, int(len(ticks) / max_ticks))
                new_ticks = ticks[::step]
                ax.set_xticks(new_ticks)
                # rotate labels for readability
                ax.tick_params(axis='x', rotation=45, labelsize=8)
            else:
                ax.tick_params(axis='x', rotation=45, labelsize=9)
        except Exception:
            pass

    if df is None or df.empty:
        return None

    numeric_cols = [c for c in columns if pd.api.types.is_numeric_dtype(df[c])]

    if not numeric_cols:
        # Trattiamo colonne non numeriche con grafici di conteggio
        # Se c'è una sola colonna, mostriamo value_counts
        if len(columns) == 1:
            col = columns[0]
            vc = df[col].value_counts(dropna=True)
            # Limit top N
            if len(vc) > top_n:
                top = vc.iloc[:top_n]
                top['Altro'] = vc.iloc[top_n:].sum()
                vc = top
            # Se richiesto, possiamo anche mostrare una torta
            # (utile per proporzioni di categorie)
            # Se chart_type == 'Torta' verrà gestito qui dal chiamante.
            # Nota: il caller passa chart_type; per compatibilità, se
            # chart_type == 'Torta' creiamo il grafico a torta.
            if chart_type == 'Torta':
                try:
                    fig, ax = plt.subplots(figsize=(8, 8))
                    vc.plot(kind='pie', ax=ax, autopct='%1.1f%%', startangle=90, counterclock=False)
                    ax.set_ylabel('')
                    ax.set_title(f'Distribuzione (Torta) per {col}')
                    ax.axis('equal')
                    plt.tight_layout()
                    return fig
                except Exception:
                    pass
            # Se molte categorie o etichette lunghe, preferiamo barre orizzontali
            long_label = any(len(str(x)) > 20 for x in vc.index.astype(str))
            many = len(vc) > 10
            use_horizontal = force_horizontal or long_label or many
            if use_horizontal:
                fig, ax = plt.subplots(figsize=(10, max(4, len(vc) * 0.25)))
                vc.sort_values().plot(kind='barh', ax=ax, color='C1')
                ax.set_xlabel('Conteggio')
                ax.set_ylabel(col)
            else:
                fig, ax = plt.subplots(figsize=(10, 5))
                vc.plot(kind='bar', ax=ax, color='C1')
                ax.set_xlabel(col)
                ax.set_ylabel('Conteggio')

            ax.set_title(f'Conteggio per {col}')
            _format_y(ax)
            _reduce_xticks(ax, max_ticks=20)
            plt.tight_layout()
            return fig

        # Se ci sono due colonne, proviamo uno stacked bar groupby
        if len(columns) == 2:
            c1, c2 = columns[0], columns[1]
            try:
                group = df.groupby([c1, c2]).size().unstack(fill_value=0)
                fig, ax = plt.subplots(figsize=(10, 6))
                group.plot(kind='bar', stacked=True, ax=ax)
                ax.set_title(f'Distribuzione: {c1} × {c2}')
                ax.set_xlabel(c1)
                ax.set_ylabel('Conteggio')
                _format_y(ax)
                _reduce_xticks(ax, max_ticks=max_xticks)
                plt.tight_layout()
                return fig
            except Exception:
                # fallback: mostra due grafici a barre separati
                fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(12, 4))
                df[c1].value_counts().iloc[:top_n].plot(kind='bar', ax=axes[0])
                axes[0].set_title(c1)
                _format_y(axes[0])
                _reduce_xticks(axes[0], max_ticks=max_xticks)
                df[c2].value_counts().iloc[:top_n].plot(kind='bar', ax=axes[1])
                axes[1].set_title(c2)
                _format_y(axes[1])
                _reduce_xticks(axes[1], max_ticks=max_xticks)
                plt.tight_layout()
                return fig

        # Più di due colonne: mostriamo i top counts per ciascuna in subplot
        n = len(columns)
        cols = columns
        max_plots = min(n, 6)
        fig, axes = plt.subplots(nrows=max_plots, ncols=1, figsize=(10, 3 * max_plots))
        if max_plots == 1:
            axes = [axes]
        for ax, col in zip(axes, cols[:max_plots]):
            vc = df[col].value_counts().iloc[:top_n]
            # prefer horizontal if labels long or forced
            if force_horizontal or any(len(str(x)) > 20 for x in vc.index.astype(str)):
                vc.sort_values().plot(kind='barh', ax=ax)
            else:
                vc.plot(kind='bar', ax=ax)
            ax.set_title(col)
            _format_y(ax)
            _reduce_xticks(ax, max_ticks=max_xticks)
        plt.tight_layout()
        return fig

    if chart_type == "Torta":
        # Per grafico a torta, sommiamo i valori numerici
        try:
            if len(numeric_cols) == 1:
                # Una sola colonna: torta dei valori sommati per indice (se categorico)
                data_sum = df[numeric_cols[0]].sum()
                fig, ax = plt.subplots(figsize=(8, 8))
                ax.pie([data_sum], labels=[numeric_cols[0]], autopct='%1.1f%%', startangle=90)
                ax.set_title(f"Torta: {numeric_cols[0]}")
                plt.tight_layout()
                return fig
            else:
                # Più colonne: somma per colonna e mostra come torta
                sums = df[numeric_cols].sum()
                # Filtra solo i valori positivi
                sums = sums[sums > 0]
                if len(sums) == 0:
                    return None
                fig, ax = plt.subplots(figsize=(8, 8))
                ax.pie(sums.values, labels=sums.index, autopct='%1.1f%%', startangle=90)
                ax.set_title("Torta: Somma per Colonna")
                plt.tight_layout()
                return fig
        except Exception:
            pass

    fig, ax = plt.subplots(figsize=(10, 5))
    plt.style.use("ggplot")

    if chart_type == "Barre":
        df[numeric_cols].plot(kind="bar", ax=ax)
        _reduce_xticks(ax, max_ticks=30)

    elif chart_type == "Linee":
        df[numeric_cols].plot(kind="line", ax=ax)

    elif chart_type == "Istogramma":
        df[numeric_cols].plot(kind="hist", bins=15, ax=ax)

    # format y axis to plain numbers
    _format_y(ax)

    ax.set_title(f"Grafico: {chart_type}")
    ax.set_xlabel("Index")
    ax.set_ylabel("Valori")

    return fig