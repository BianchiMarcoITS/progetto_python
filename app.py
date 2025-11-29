import streamlit as st
import pandas as pd
from io import BytesIO

from modules.data_loader import load_csv
from modules.analyzer import apply_filters, compute_statistics
from modules.plotter import generate_plot

from database import init_db, save_dataset, list_datasets, load_dataset, save_history


# ======================================================
# FUNZIONI DI EXPORT
# ======================================================
def export_to_pdf_chart(fig, filename):
    """Esporta un grafico Matplotlib in formato PDF.

    Args:
        fig (matplotlib.figure.Figure): Figura Matplotlib da esportare.
        filename (str): Nome file suggerito (usato solo per metadata/nomi di download).

    Returns:
        bytes | None: Contenuto PDF in byte se l'operazione ha successo, altrimenti ``None``.
    """
    try:
        buf = BytesIO()
        fig.savefig(buf, format='pdf', bbox_inches='tight')
        buf.seek(0)
        return buf.getvalue()
    except Exception as e:
        st.error(f"Errore nell'export PDF: {e}")
        return None


def export_to_excel(df, filename):
    """Esporta un ``pandas.DataFrame`` in un file Excel (.xlsx).

    Effettua una formattazione di base (larghezza colonne) usando ``openpyxl``.

    Args:
        df (pandas.DataFrame): DataFrame da esportare.
        filename (str): Nome file suggerito (usato solo per metadata/nomi di download).

    Returns:
        bytes | None: Conteuto del file .xlsx in memoria se ha successo, altrimenti ``None``.
    """
    try:
        from openpyxl.utils import get_column_letter
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Data', index=False)
            # Formattazione basilare: autowidth delle colonne
            worksheet = writer.sheets['Data']
            for idx, col in enumerate(df.columns, 1):
                max_length = max(df[col].astype(str).apply(len).max(), len(col)) + 2
                col_letter = get_column_letter(idx)
                worksheet.column_dimensions[col_letter].width = min(max_length, 50)
        buf.seek(0)
        return buf.getvalue()
    except Exception as e:
        st.error(f"Errore nell'export Excel: {e}")
        return None


def export_pdf_report(df, fig, title, filename):
    """Crea ed esporta un report PDF con tabella dati e grafico.

    Usa ``reportlab`` per assemblare un PDF in landscape contenente una
    tabella (preview limitata delle righe) e il grafico fornito come immagine.

    Args:
        df (pandas.DataFrame): DataFrame di cui includere la tabella.
        fig (matplotlib.figure.Figure): Figura Matplotlib da includere nel report.
        title (str): Titolo del report.
        filename (str): Nome file suggerito (usato solo per metadata/nomi di download).

    Returns:
        bytes | None: Contenuto PDF se l'operazione ha successo, altrimenti ``None``.
    """
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
        from reportlab.lib import colors
        from datetime import datetime
        
        # Salva il grafico in PNG per includerlo nel PDF
        img_buf = BytesIO()
        fig.savefig(img_buf, format='png', bbox_inches='tight', dpi=100)
        img_buf.seek(0)
        
        # Crea PDF su landscape per grafici larghi
        pdf_buf = BytesIO()
        doc = SimpleDocTemplate(pdf_buf, pagesize=landscape(A4), topMargin=0.4*inch, bottomMargin=0.4*inch, leftMargin=0.4*inch, rightMargin=0.4*inch)
        
        # Stili
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=8,
            alignment=1  # centrato
        )
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=8,
            spaceAfter=4
        )
        
        # Contenuto del report
        story = []
        
        # Titolo e timestamp
        story.append(Paragraph(title, title_style))
        story.append(Paragraph(f"<b>Generato il:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", normal_style))
        story.append(Spacer(1, 0.15*inch))
        
        # Tabella dati (con scroll orizzontale se molte colonne)
        story.append(Paragraph("<b>Dati</b>", styles['Heading2']))
        
        # Converti DataFrame in lista per la tabella
        data = [list(df.columns)] + df.values.tolist()
        
        # Limita il numero di righe per leggibilità (max 15 + header su landscape)
        if len(data) > 16:
            data_display = data[:16]
            story.append(Paragraph(f"<i>(Visualizzati 15 record su {len(df)} totali)</i>", normal_style))
        else:
            data_display = data
        
        # Crea tabella con colonne ridimensionate dinamicamente
        n_cols = len(df.columns)
        # Massima larghezza disponibile su landscape A4: ~10 inches
        max_width = 10 * inch
        col_widths = [max_width / max(1, n_cols)] * n_cols
        
        table = Table(data_display, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('TOPPADDING', (0, 1), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 2),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.2*inch))
        
        # Grafico
        story.append(Paragraph("<b>Grafico</b>", styles['Heading2']))
        
        # Ridimensiona l'immagine per adattarla bene al landscape
        # Larghezza: quasi tutta la pagina, altezza proporzionale
        img_width = 9.5 * inch
        img_height = 4.5 * inch
        img = Image(img_buf, width=img_width, height=img_height)
        story.append(img)
        
        # Build PDF
        doc.build(story)
        pdf_buf.seek(0)
        return pdf_buf.getvalue()
    
    except Exception as e:
        st.error(f"Errore nell'export PDF report: {e}")
        import traceback
        traceback.print_exc()
        return None


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

        # --- Aggregazione rapida (opzionale) ---
        # Se tra le colonne selezionate ci sono categoriche, offriamo
        # una semplice UI per raggruppare il risultato filtrato.
        cat_selected = [c for c in selected_cols if not pd.api.types.is_numeric_dtype(df[c])]
        num_all = [c for c in df.columns.tolist() if pd.api.types.is_numeric_dtype(df[c])]
        if cat_selected:
            st.subheader("Aggregazione rapida (opzionale)")
            # chiave unica per evitare StreamlitDuplicateElementId
            cat_key = "_".join([c.replace(' ', '_') for c in cat_selected])[:200]
            group_col = st.selectbox("Raggruppa per (colonna categorica)", ["-- Nessuna --"] + cat_selected, key=f"group_col_{cat_key}")
            if group_col and group_col != "-- Nessuna --":
                # Permetti di scegliere colonne numeriche da aggregare (dalla tabella completa)
                value_cols = st.multiselect("Colonne numeriche da aggregare", num_all, default=(num_all[:1] if num_all else []), key=f"vals_{cat_key}")
                agg_op = st.selectbox("Operazione di aggregazione", ["sum", "mean", "count", "max", "min"], key=f"aggop_{cat_key}") 

                if value_cols:
                        try:
                            if agg_op == "count":
                                agg_df = filtered_df.groupby(group_col)[value_cols].count().reset_index()
                            else:
                                agg_df = filtered_df.groupby(group_col)[value_cols].agg(agg_op).reset_index()

                            # Ordina per la prima colonna di valore (discendente)
                            sort_by = value_cols[0]
                            agg_df = agg_df.sort_values(by=sort_by, ascending=False)

                            st.write("### Tabella aggregata")
                            st.dataframe(agg_df)

                            # Export CSV
                            try:
                                csv_bytes = agg_df.to_csv(index=False).encode('utf-8')
                                filename_base = 'aggregated'
                                if upload_file is not None and hasattr(upload_file, 'name'):
                                    filename_base = upload_file.name.replace('.csv', '')
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.download_button(label="Download CSV (aggregato)", data=csv_bytes, file_name=f"{filename_base}_aggregated.csv", mime="text/csv")
                                with col2:
                                    excel_data = export_to_excel(agg_df, f"{filename_base}_aggregated.xlsx")
                                    if excel_data:
                                        st.download_button(label="Download Excel (aggregato)", data=excel_data, file_name=f"{filename_base}_aggregated.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                            except Exception:
                                pass

                            # Grafico della tabella aggregata
                            st.subheader("Grafico aggregato")
                            chart_type = st.selectbox("Tipo di grafico:", ["Barre", "Linee", "Torta"], key=f"agg_chart_{group_col}")
                            fig = generate_plot(agg_df, [group_col] + value_cols, chart_type)
                            if fig:
                                st.pyplot(fig)
                                # Export grafico aggregato
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    try:
                                        buf = BytesIO()
                                        fig.savefig(buf, format='png', bbox_inches='tight')
                                        buf.seek(0)
                                        st.download_button(label='Download grafico PNG (aggregato)', data=buf.getvalue(), file_name=f"{filename_base}_aggregated_{chart_type}.png", mime='image/png')
                                    except Exception:
                                        pass
                                with col2:
                                    try:
                                        pdf_data = export_to_pdf_chart(fig, f"{filename_base}_aggregated_{chart_type}.pdf")
                                        if pdf_data:
                                            st.download_button(label='Download grafico PDF (aggregato)', data=pdf_data, file_name=f"{filename_base}_aggregated_{chart_type}.pdf", mime='application/pdf')
                                    except Exception:
                                        pass
                                with col3:
                                    try:
                                        report_data = export_pdf_report(agg_df, fig, f"Report Aggregato: {chart_type}", f"{filename_base}_report_aggregated_{chart_type}.pdf")
                                        if report_data:
                                            st.download_button(label='Download Report PDF (aggregato)', data=report_data, file_name=f"{filename_base}_report_aggregated_{chart_type}.pdf", mime='application/pdf')
                                    except Exception:
                                        pass
                        except Exception as e:
                            st.error(f"Errore durante l'aggregazione rapida: {e}")

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
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="Download CSV (filtrato)",
                    data=csv_bytes,
                    file_name=f"{filename_base}_filtered.csv",
                    mime="text/csv"
                )
            with col2:
                try:
                    excel_data = export_to_excel(filtered_df, f"{filename_base}_filtered.xlsx")
                    if excel_data:
                        st.download_button(
                            label="Download Excel (filtrato)",
                            data=excel_data,
                            file_name=f"{filename_base}_filtered.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                except Exception:
                    st.info('Impossibile esportare come Excel.')
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
            ["Barre", "Linee", "Istogramma", "Torta"]
        )

        fig = generate_plot(filtered_df, selected_cols, chart_type)

        if fig:
            st.pyplot(fig)
            # --- Export grafico ---
            col1, col2, col3 = st.columns(3)
            with col1:
                try:
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
            
            with col2:
                try:
                    pdf_data = export_to_pdf_chart(fig, f"{filename_base}_{chart_type}.pdf")
                    if pdf_data:
                        st.download_button(
                            label='Download grafico PDF',
                            data=pdf_data,
                            file_name=f"{filename_base}_{chart_type}.pdf",
                            mime='application/pdf'
                        )
                except Exception:
                    st.info('Impossibile esportare il grafico come PDF.')
            
            with col3:
                try:
                    report_data = export_pdf_report(filtered_df, fig, f"Report: {chart_type}", f"{filename_base}_report_{chart_type}.pdf")
                    if report_data:
                        st.download_button(
                            label='Download Report PDF',
                            data=report_data,
                            file_name=f"{filename_base}_report_{chart_type}.pdf",
                            mime='application/pdf'
                        )
                except Exception:
                    st.info('Impossibile esportare il report PDF.')
        else:
            st.warning("Impossibile generare un grafico con i dati selezionati.")