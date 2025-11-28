import streamlit as st
import pandas as pd

import streamlit as st
import pandas as pd

from modules.data_loader import load_csv
from modules.analyzer import apply_filters, compute_statistics
from modules.plotter import generate_plot

from database import init_db, save_dataset, list_datasets, load_dataset, save_history


# ======================================================
# INIZIALIZZA DATABASE
# ======================================================
init_db()

st.set_page_config(page_title="CSV Analyzer", layout="wide")
st.title("CSV Analyzer")

df = None  # DataFrame attuale


# ======================================================
# 1) UPLOAD CSV
# ======================================================
st.header("Carica un file CSV")
upload_file = st.file_uploader("Seleziona un CSV", type="csv")

if upload_file is not None:

    df, err = load_csv(upload_file)

    if err:
        st.error(err)
    else:
        st.success("File caricato correttamente!")
        st.dataframe(df.head())

        # Salvataggio nel DB (evita duplicati per nome)
        try:
            dataset_id, created = save_dataset(upload_file.name, df)
            if dataset_id is None:
                st.error("Errore nel salvataggio del dataset (vedi console).")
            elif not created:
                st.info("Dataset già presente: caricamento del dataset esistente.")
                # Carichiamo quello esistente nel DataFrame
                df = load_dataset(dataset_id)
                st.dataframe(df.head())
            else:
                st.success("✓ Dataset salvato nel database.")
        except Exception as e:
            st.error(f"Errore nel salvataggio: {e}")
        


# ======================================================
# 2) CARICAMENTO DA DATABASE
# ======================================================
st.subheader("Dataset salvati")

datasets = list_datasets()

if datasets:
    dataset_names = ["-- Seleziona --"] + [
        f"{d[0]} - {d[1]} ({d[2]})" for d in datasets
    ]

    selected_dataset = st.selectbox("Carica dataset salvato", dataset_names)

    if selected_dataset != "-- Seleziona --":
        dataset_id = int(selected_dataset.split(" - ")[0])
        df = load_dataset(dataset_id)
        st.success("Dataset caricato dal database.")
        st.dataframe(df.head())


# ======================================================
# 3) SELEZIONE COLONNE E FILTRI
# ======================================================
if df is not None:

    st.header("Seleziona colonne e applica filtri")

    columns = df.columns.tolist()
    selected_cols = st.multiselect("Colonne da analizzare", columns)

    if selected_cols:

        # --- Filtri dinamici ---
        filters = []
        st.subheader("Filtri")

        for col in selected_cols:

            if pd.api.types.is_numeric_dtype(df[col]):
                min_val = float(df[col].min())
                max_val = float(df[col].max())

                sel_min, sel_max = st.slider(
                    f"Filtro numerico per {col}",
                    min_val, max_val, (min_val, max_val)
                )

                filters.append((col, 'between', (sel_min, sel_max)))

            else:
                values = df[col].dropna().unique().tolist()
                sel_vals = st.multiselect(
                    f"Filtro valori per {col}",
                    values,
                    default=values
                )

                filters.append((col, 'in', sel_vals))

        # --- Applica i filtri ---
        filtered_df = apply_filters(df, selected_cols, filters)
        st.write("### Risultato filtrato:")
        st.dataframe(filtered_df)

        # --- Export dei dati filtrati ---
        csv_bytes = None
        try:
            csv_bytes = filtered_df.to_csv(index=False).encode('utf-8')
        except Exception:
            csv_bytes = None

        # Determina base per il nome file (upload, oppure dataset selezionato, altrimenti 'dataset')
        filename_base = 'dataset'
        try:
            if upload_file is not None and hasattr(upload_file, 'name'):
                filename_base = upload_file.name
            elif 'selected_dataset' in locals() and selected_dataset and selected_dataset != "-- Seleziona --":
                # selected_dataset ha formato: "{id} - {name} ({date})"
                try:
                    name_part = selected_dataset.split(' - ', 1)[1]
                    # rimuovi la parte tra parentesi finale
                    name_only = name_part.rsplit(' (', 1)[0]
                    filename_base = name_only
                except Exception:
                    filename_base = selected_dataset
        except Exception:
            filename_base = 'dataset'

        if csv_bytes is not None and not filtered_df.empty:
            st.download_button(
                label="Download CSV (filtrato)",
                data=csv_bytes,
                file_name=f"{filename_base}_filtered.csv",
                mime="text/csv"
            )
        else:
            st.button("Download CSV (filtrato)", disabled=True)


        # ======================================================
        # 4) ANALISI STATISTICHE
        # ======================================================
        st.header("Analisi statistiche")

        operation = st.selectbox(
            "Tipo di analisi:",
            ["Media", "Somma", "Conteggio", "Massimo", "Minimo"]
        )

        stats = compute_statistics(filtered_df, selected_cols, operation)

        if stats:
            st.write("### Risultati:")
            st.table(stats)
        else:
            st.info("Seleziona almeno una colonna numerica.")


        # ======================================================
        # 5) GENERAZIONE GRAFICI
        # ======================================================
        st.header("Genera grafico")

        chart_type = st.selectbox(
            "Tipo di grafico:",
            ["Barre", "Linee", "Istogramma"]
        )

        fig = generate_plot(filtered_df, selected_cols, chart_type)

        if fig:
            st.pyplot(fig)
            # --- Export grafico ---
            try:
                from io import BytesIO
                buf = BytesIO()
                fig.savefig(buf, format='png', bbox_inches='tight')
                buf.seek(0)
                st.download_button(
                    label='Download grafico PNG',
                    data=buf.getvalue(),
                    file_name=f"{filename_base}_{chart_type}.png",
                    mime='image/png'
                )
            except Exception:
                st.info('Impossibile esportare il grafico come PNG.')
        else:
            st.warning("Impossibile generare un grafico con i dati selezionati.")