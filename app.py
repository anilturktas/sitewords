import streamlit as st
import pandas as pd
import pydeck as pdk
import io
import re
import math
from pyproj import Transformer, CRS
from fpdf import FPDF
from datetime import datetime

# --- Arayüz Dil Sözlüğü (İngilizce, Almanca, Fransızca, Romence, İtalyanca) ---
UI_TEXT = {
    'en': {
        'upload_header': '📋 Data Upload',
        'upload_info': 'To begin, select your Region and Language, then upload both TaskLog and Record files.',
        'region_mode': 'Region Mode',
        'language_mode': 'Language',
        'upload_files': 'Upload Log Files',
        'parsing_spinner': 'Parsing and joining logs...',
        'tasklog_missing': 'No TaskLog mapped. Showing Records only.',
        'parse_error': 'Error parsing records. Ensure valid TaskLog and Record files.',
        'dash_header': '📋 Dashboard',
        'clear_files': '🗑️ Clear Loaded Files',
        'field_data_sel': '🗃️ Field Data Selection',
        'sel_caption': 'Select rows to include in the report. If none are selected, all rows will be exported.',
        'report_all': '📄 Report All Data',
        'report_all_help': 'No rows selected. Clicking this will use ALL data.',
        'report_sel_base': '📄 Report Selection',
        'report_sel_help': 'Create report from selected rows.',
        'map_header': '📍 Site Map Overview',
        'map_caption': 'Interactive map view of the measurement points.',
        'map_style_label': 'Map Style',
        'style_light': 'Light (Default)',
        'style_dark': 'Dark Mode',
        'style_road': 'Road Map',
        'map_pt_name': 'Point Name',
        'map_no_coord': 'No valid geographic coordinates found to display on map.',
        'rep_header': '📄 Report Generator',
        'back_dash': '← Back to Dashboard',
        'proj_details': 'Project Details',
        'proj_name': 'Project Name',
        'work_order': 'Work Order',
        'client_name': 'Client Name',
        'rep_meta': 'Report Metadata',
        'company_name': 'Company Name',
        'rep_date': 'Report Date',
        'rep_time': 'Report Time',
        'col_sel_expander': '⚙️ Data Columns Selection (Click to Open/Close)',
        'col_sel_caption': 'Select columns to include in the exported report.',
        'col_warning': 'No columns selected. Export will contain default columns.',
        'rep_preview': 'Report Preview',
        'rows': 'rows',
        'export_opts': 'Export Options',
        'dl_pdf': 'Download PDF',
        'dl_excel': 'Download Excel',
        'dl_csv': 'Download CSV',
        'dl_html': 'Download HTML',
        'pdf_project': 'Project:',
        'pdf_wo': 'Work Order:',
        'pdf_client': 'Client:',
        'pdf_company': 'Company:',
        'pdf_datetime': 'Date/Time:',
        'pdf_date': 'Date:',
        'pdf_time': 'Time:',
        'pdf_page': 'Page',
        'pdf_title': 'SiteWords Report',
        # Sütun Çevirileri
        'col_Record_Type': 'Record Type',
        'col_Sub_Type': 'Sub Type',
        'col_Point_Name': 'Point Name',
        'col_Line_Name': 'Line Name',
        'col_Point_Code': 'Point Code',
        'col_Measured_E': 'Measured Easting',
        'col_Measured_N': 'Measured Northing',
        'col_Measured_Elv': 'Measured Elevation',
        'col_Design_N': 'Design N',
        'col_Design_E': 'Design E',
        'col_Design_Elv': 'Design Elv',
        'col_Cut_Fill': 'Cut/Fill (+/-)',
        'col_Horz_Deviation': 'Horz Deviation',
        'col_Design_Station': 'Design Station',
        'col_Design_Offset': 'Design Offset',
        'col_Measured_Station': 'Measured Station',
        'col_Measured_Offset': 'Measured Offset',
        'col_Precision_H': 'Precision H',
        'col_Precision_V': 'Precision V'
    },
    'de': {
        'upload_header': '📋 Daten-Upload',
        'upload_info': 'Wählen Sie Ihre Region und Sprache und laden Sie dann TaskLog- und Record-Dateien hoch.',
        'region_mode': 'Region Modus',
        'language_mode': 'Sprache',
        'upload_files': 'Log-Dateien hochladen',
        'parsing_spinner': 'Logs werden analysiert und verknüpft...',
        'tasklog_missing': 'Kein TaskLog zugeordnet. Es werden nur Records angezeigt.',
        'parse_error': 'Fehler beim Lesen der Dateien. Stellen Sie sicher, dass TaskLog und Record gültig sind.',
        'dash_header': '📋 Dashboard',
        'clear_files': '🗑️ Geladene Dateien löschen',
        'field_data_sel': '🗃️ Felddaten-Auswahl',
        'sel_caption': 'Wählen Sie die Zeilen für den Bericht aus. Ohne Auswahl werden alle Zeilen exportiert.',
        'report_all': '📄 Alle Daten berichten',
        'report_all_help': 'Keine Zeilen gewählt. ALLE Daten werden verwendet.',
        'report_sel_base': '📄 Auswahl berichten',
        'report_sel_help': 'Bericht aus ausgewählten Zeilen erstellen.',
        'map_header': '📍 Standortkarte Übersicht',
        'map_caption': 'Interaktive Kartenansicht der Messpunkte.',
        'map_style_label': 'Kartenstil',
        'style_light': 'Hell (Standard)',
        'style_dark': 'Dunkelmodus',
        'style_road': 'Straßenkarte',
        'map_pt_name': 'Punktname',
        'map_no_coord': 'Keine gültigen geografischen Koordinaten für die Karte gefunden.',
        'rep_header': '📄 Berichtsgenerator',
        'back_dash': '← Zurück zum Dashboard',
        'proj_details': 'Projektdetails',
        'proj_name': 'Projektname',
        'work_order': 'Arbeitsauftrag',
        'client_name': 'Kundenname',
        'rep_meta': 'Berichts-Metadaten',
        'company_name': 'Firmenname',
        'rep_date': 'Berichtsdatum',
        'rep_time': 'Berichtszeit',
        'col_sel_expander': '⚙️ Datenspalten-Auswahl (Klicken zum Öffnen/Schließen)',
        'col_sel_caption': 'Wählen Sie die Spalten für den exportierten Bericht.',
        'col_warning': 'Keine Spalten gewählt. Standardspalten werden exportiert.',
        'rep_preview': 'Berichtsvorschau',
        'rows': 'Zeilen',
        'export_opts': 'Exportoptionen',
        'dl_pdf': 'PDF herunterladen',
        'dl_excel': 'Excel herunterladen',
        'dl_csv': 'CSV herunterladen',
        'dl_html': 'HTML herunterladen',
        'pdf_project': 'Projekt:',
        'pdf_wo': 'Arbeitsauftrag:',
        'pdf_client': 'Kunde:',
        'pdf_company': 'Firma:',
        'pdf_datetime': 'Datum/Zeit:',
        'pdf_date': 'Datum:',
        'pdf_time': 'Zeit:',
        'pdf_page': 'Seite',
        'pdf_title': 'SiteWords Bericht',
        # Sütun Çevirileri
        'col_Record_Type': 'Datensatztyp',
        'col_Sub_Type': 'Untertyp',
        'col_Point_Name': 'Punktname',
        'col_Line_Name': 'Linienname',
        'col_Point_Code': 'Punktcode',
        'col_Measured_E': 'Gemess. Rechtswert',
        'col_Measured_N': 'Gemess. Hochwert',
        'col_Measured_Elv': 'Gemess. Höhe',
        'col_Design_N': 'Soll Hochw.',
        'col_Design_E': 'Soll Rechtsw.',
        'col_Design_Elv': 'Sollhöhe',
        'col_Cut_Fill': 'Abtr./Auftr. (+/-)',
        'col_Horz_Deviation': 'Lageabw.',
        'col_Design_Station': 'Sollstation',
        'col_Design_Offset': 'Sollabstand',
        'col_Measured_Station': 'Gemess. Station',
        'col_Measured_Offset': 'Gemess. Abstand',
        'col_Precision_H': 'Lagegenauigkeit',
        'col_Precision_V': 'Höhengenauigkeit'
    },
    'fr': {
        'upload_header': '📋 Téléchargement de Données',
        'upload_info': 'Pour commencer, sélectionnez votre région et votre langue, puis téléchargez les fichiers TaskLog et Record.',
        'region_mode': 'Mode Région',
        'language_mode': 'Langue',
        'upload_files': 'Télécharger les fichiers journaux',
        'parsing_spinner': 'Analyse et fusion des journaux en cours...',
        'tasklog_missing': 'Aucun TaskLog mappé. Affichage des Records uniquement.',
        'parse_error': 'Erreur lors de l\'analyse. Assurez-vous que les fichiers sont valides.',
        'dash_header': '📋 Tableau de Bord',
        'clear_files': '🗑️ Effacer les fichiers chargés',
        'field_data_sel': '🗃️ Sélection des Données de Terrain',
        'sel_caption': 'Sélectionnez les lignes à inclure dans le rapport. Si aucune n\'est sélectionnée, toutes les lignes seront exportées.',
        'report_all': '📄 Rapporter Toutes les Données',
        'report_all_help': 'Aucune ligne sélectionnée. Cliquer ici utilisera TOUTES les données.',
        'report_sel_base': '📄 Sélection du Rapport',
        'report_sel_help': 'Créer un rapport à partir des lignes sélectionnées.',
        'map_header': '📍 Aperçu de la Carte du Site',
        'map_caption': 'Vue cartographique interactive des points de mesure.',
        'map_style_label': 'Style de Carte',
        'style_light': 'Clair (Défaut)',
        'style_dark': 'Mode Sombre',
        'style_road': 'Carte Routière',
        'map_pt_name': 'Nom du Point',
        'map_no_coord': 'Aucune coordonnée géographique valide trouvée pour l\'affichage sur la carte.',
        'rep_header': '📄 Générateur de Rapports',
        'back_dash': '← Retour au Tableau de Bord',
        'proj_details': 'Détails du Projet',
        'proj_name': 'Nom du Projet',
        'work_order': 'Bon de Travail',
        'client_name': 'Nom du Client',
        'rep_meta': 'Métadonnées du Rapport',
        'company_name': 'Nom de l\'Entreprise',
        'rep_date': 'Date du Rapport',
        'rep_time': 'Heure du Rapport',
        'col_sel_expander': '⚙️ Sélection des Colonnes de Données (Cliquez pour Ouvrir/Fermer)',
        'col_sel_caption': 'Sélectionnez les colonnes à inclure dans le rapport exporté.',
        'col_warning': 'Aucune colonne sélectionnée. L\'export contiendra les colonnes par défaut.',
        'rep_preview': 'Aperçu du Rapport',
        'rows': 'lignes',
        'export_opts': 'Options d\'Exportation',
        'dl_pdf': 'Télécharger le PDF',
        'dl_excel': 'Télécharger Excel',
        'dl_csv': 'Télécharger le CSV',
        'dl_html': 'Télécharger le HTML',
        'pdf_project': 'Projet :',
        'pdf_wo': 'Bon de Travail :',
        'pdf_client': 'Client :',
        'pdf_company': 'Entreprise :',
        'pdf_datetime': 'Date/Heure :',
        'pdf_date': 'Date :',
        'pdf_time': 'Heure :',
        'pdf_page': 'Page',
        'pdf_title': 'Rapport SiteWords',
        # Sütun Çevirileri
        'col_Record_Type': 'Type d\'enregistrement',
        'col_Sub_Type': 'Sous-type',
        'col_Point_Name': 'Nom du Point',
        'col_Line_Name': 'Nom de la Ligne',
        'col_Point_Code': 'Code du Point',
        'col_Measured_E': 'Est Mesuré',
        'col_Measured_N': 'Nord Mesuré',
        'col_Measured_Elv': 'Élévation Mesurée',
        'col_Design_N': 'Nord Projet',
        'col_Design_E': 'Est Projet',
        'col_Design_Elv': 'Élévation Projet',
        'col_Cut_Fill': 'Déblai/Remblai (+/-)',
        'col_Horz_Deviation': 'Déviation Horz.',
        'col_Design_Station': 'Station Projet',
        'col_Design_Offset': 'Décalage Projet',
        'col_Measured_Station': 'Station Mesurée',
        'col_Measured_Offset': 'Décalage Mesuré',
        'col_Precision_H': 'Précision H',
        'col_Precision_V': 'Précision V'
    },
    'ro': {
        'upload_header': '📋 Încărcare Date',
        'upload_info': 'Pentru a începe, selectați Regiunea și Limba, apoi încărcați fișierele TaskLog și Record.',
        'region_mode': 'Mod Regiune',
        'language_mode': 'Limbă',
        'upload_files': 'Încărcați fișierele jurnal',
        'parsing_spinner': 'Analizarea și îmbinarea jurnalelor...',
        'tasklog_missing': 'Niciun TaskLog mapat. Se afișează doar Records.',
        'parse_error': 'Eroare la analizarea înregistrărilor. Asigurați-vă că fișierele sunt valide.',
        'dash_header': '📋 Panou de Control',
        'clear_files': '🗑️ Ștergeți fișierele încărcate',
        'field_data_sel': '🗃️ Selecția Datelor de Teren',
        'sel_caption': 'Selectați rândurile de inclus în raport. Dacă nu este selectat niciunul, toate vor fi exportate.',
        'report_all': '📄 Raportați Toate Datele',
        'report_all_help': 'Niciun rând selectat. Făcând clic aici se vor utiliza TOATE datele.',
        'report_sel_base': '📄 Selecție Raport',
        'report_sel_help': 'Creați un raport din rândurile selectate.',
        'map_header': '📍 Prezentare Generală a Hărții Site-ului',
        'map_caption': 'Vizualizare interactivă a hărții punctelor de măsurare.',
        'map_style_label': 'Stil Hartă',
        'style_light': 'Luminos (Implicit)',
        'style_dark': 'Mod Întunecat',
        'style_road': 'Hartă Rutieră',
        'map_pt_name': 'Nume Punct',
        'map_no_coord': 'Nu au fost găsite coordonate geografice valide pentru afișare pe hartă.',
        'rep_header': '📄 Generator de Rapoarte',
        'back_dash': '← Înapoi la Panoul de Control',
        'proj_details': 'Detalii Proiect',
        'proj_name': 'Nume Proiect',
        'work_order': 'Comandă de Lucru',
        'client_name': 'Nume Client',
        'rep_meta': 'Metadate Raport',
        'company_name': 'Nume Companie',
        'rep_date': 'Data Raportului',
        'rep_time': 'Ora Raportului',
        'col_sel_expander': '⚙️ Selecția Coloanelor de Date (Faceți clic pentru a Deschide/Închide)',
        'col_sel_caption': 'Selectați coloanele de inclus în raportul exportat.',
        'col_warning': 'Nicio coloană selectată. Exportul va conține coloanele implicite.',
        'rep_preview': 'Previzualizare Raport',
        'rows': 'rânduri',
        'export_opts': 'Opțiuni de Export',
        'dl_pdf': 'Descărcați PDF',
        'dl_excel': 'Descărcați Excel',
        'dl_csv': 'Descărcați CSV',
        'dl_html': 'Descărcați HTML',
        'pdf_project': 'Proiect:',
        'pdf_wo': 'Comandă Lucru:',
        'pdf_client': 'Client:',
        'pdf_company': 'Companie:',
        'pdf_datetime': 'Dată/Oră:',
        'pdf_date': 'Dată:',
        'pdf_time': 'Oră:',
        'pdf_page': 'Pagină',
        'pdf_title': 'Raport SiteWords',
        # Sütun Çevirileri
        'col_Record_Type': 'Tip Înregistrare',
        'col_Sub_Type': 'Subtip',
        'col_Point_Name': 'Nume Punct',
        'col_Line_Name': 'Nume Linie',
        'col_Point_Code': 'Cod Punct',
        'col_Measured_E': 'Est Măsurat',
        'col_Measured_N': 'Nord Măsurat',
        'col_Measured_Elv': 'Cota Măsurată',
        'col_Design_N': 'Nord Proiect',
        'col_Design_E': 'Est Proiect',
        'col_Design_Elv': 'Cota Proiect',
        'col_Cut_Fill': 'Săpătură/Umplutură (+/-)',
        'col_Horz_Deviation': 'Deviație Horz.',
        'col_Design_Station': 'Stație Proiect',
        'col_Design_Offset': 'Decalaj Proiect',
        'col_Measured_Station': 'Stație Măsurată',
        'col_Measured_Offset': 'Decalaj Măsurat',
        'col_Precision_H': 'Precizie H',
        'col_Precision_V': 'Precizie V'
    },
    'it': {
        'upload_header': '📋 Caricamento Dati',
        'upload_info': 'Per iniziare, seleziona la tua Regione e Lingua, quindi carica i file TaskLog e Record.',
        'region_mode': 'Modalità Regione',
        'language_mode': 'Lingua',
        'upload_files': 'Carica i file di registro',
        'parsing_spinner': 'Analisi e unione dei registri in corso...',
        'tasklog_missing': 'Nessun TaskLog mappato. Visualizzazione solo dei Record.',
        'parse_error': 'Errore durante l\'analisi dei record. Assicurati che i file siano validi.',
        'dash_header': '📋 Pannello di Controllo',
        'clear_files': '🗑️ Cancella i file caricati',
        'field_data_sel': '🗃️ Selezione Dati di Campo',
        'sel_caption': 'Seleziona le righe da includere nel rapporto. Se non ne viene selezionata nessuna, verranno esportate tutte.',
        'report_all': '📄 Segnala Tutti i Dati',
        'report_all_help': 'Nessuna riga selezionata. Cliccando qui verranno utilizzati TUTTI i dati.',
        'report_sel_base': '📄 Selezione Rapporto',
        'report_sel_help': 'Crea un rapporto dalle righe selezionate.',
        'map_header': '📍 Panoramica Mappa del Sito',
        'map_caption': 'Vista interattiva della mappa dei punti di misurazione.',
        'map_style_label': 'Stile Mappa',
        'style_light': 'Chiaro (Predefinito)',
        'style_dark': 'Modalità Scura',
        'style_road': 'Mappa Stradale',
        'map_pt_name': 'Nome Punto',
        'map_no_coord': 'Nessuna coordinata geografica valida trovata per la visualizzazione sulla mappa.',
        'rep_header': '📄 Generatore di Rapporti',
        'back_dash': '← Torna al Pannello di Controllo',
        'proj_details': 'Dettagli Progetto',
        'proj_name': 'Nome Progetto',
        'work_order': 'Ordine di Lavoro',
        'client_name': 'Nome Cliente',
        'rep_meta': 'Metadati Rapporto',
        'company_name': 'Nome Azienda',
        'rep_date': 'Data Rapporto',
        'rep_time': 'Ora Rapporto',
        'col_sel_expander': '⚙️ Selezione Colonne Dati (Clicca per Aprire/Chiudere)',
        'col_sel_caption': 'Seleziona le colonne da includere nel rapporto esportato.',
        'col_warning': 'Nessuna colonna selezionata. L\'esportazione conterrà le colonne predefinite.',
        'rep_preview': 'Anteprima Rapporto',
        'rows': 'righe',
        'export_opts': 'Opzioni di Esportazione',
        'dl_pdf': 'Scarica PDF',
        'dl_excel': 'Scarica Excel',
        'dl_csv': 'Scarica CSV',
        'dl_html': 'Scarica HTML',
        'pdf_project': 'Progetto:',
        'pdf_wo': 'Ordine di Lavoro:',
        'pdf_client': 'Cliente:',
        'pdf_company': 'Azienda:',
        'pdf_datetime': 'Data/Ora:',
        'pdf_date': 'Data:',
        'pdf_time': 'Ora:',
        'pdf_page': 'Pagina',
        'pdf_title': 'Rapporto SiteWords',
        # Sütun Çevirileri
        'col_Record_Type': 'Tipo di Record',
        'col_Sub_Type': 'Sottotipo',
        'col_Point_Name': 'Nome Punto',
        'col_Line_Name': 'Nome Linea',
        'col_Point_Code': 'Codice Punto',
        'col_Measured_E': 'Est Misurato',
        'col_Measured_N': 'Nord Misurato',
        'col_Measured_Elv': 'Quota Misurata',
        'col_Design_N': 'Nord Progetto',
        'col_Design_E': 'Est Progetto',
        'col_Design_Elv': 'Quota Progetto',
        'col_Cut_Fill': 'Sterro/Riporto (+/-)',
        'col_Horz_Deviation': 'Deviazione Orizz.',
        'col_Design_Station': 'Stazione Progetto',
        'col_Design_Offset': 'Offset Progetto',
        'col_Measured_Station': 'Stazione Misurata',
        'col_Measured_Offset': 'Offset Misurato',
        'col_Precision_H': 'Precisione H',
        'col_Precision_V': 'Precisione V'
    }
}

# --- Dil Seçenekleri ---
LANG_OPTIONS = {
    'English': 'en',
    'Deutsch': 'de',
    'Français': 'fr',
    'Română': 'ro',
    'Italiano': 'it'
}

# --- Sütun Eşleştirme Sözlüğü ---
COLUMN_MAPPING = {
    'Record Type': 'col_Record_Type',
    'Datensatztyp': 'col_Record_Type',
    
    'Sub Type': 'col_Sub_Type',
    'Untertyp': 'col_Sub_Type',
    
    'Point Name': 'col_Point_Name',
    'Punktname': 'col_Point_Name',
    
    'Line Name': 'col_Line_Name',
    'Linienname': 'col_Line_Name',
    
    'Point Code': 'col_Point_Code',
    'Punktcode': 'col_Point_Code',
    
    'Measured E': 'col_Measured_E',
    'Gemess. Rechtswert': 'col_Measured_E',
    
    'Measured N': 'col_Measured_N',
    'Gemess. Hochwert': 'col_Measured_N',
    
    'Measured Elv': 'col_Measured_Elv',
    'Gemess. Höhe': 'col_Measured_Elv',
    
    'Design N': 'col_Design_N',
    'Soll Hochw.': 'col_Design_N',
    
    'Design E': 'col_Design_E',
    'Soll Rechtsw.': 'col_Design_E',
    
    'Design Elv': 'col_Design_Elv',
    'Sollhöhe': 'col_Design_Elv',
    
    'Cut/Fill (+/-)': 'col_Cut_Fill',
    'Abtr./Auftr. (+/-)': 'col_Cut_Fill',
    
    'Horz Deviation': 'col_Horz_Deviation',
    'Lageabw.': 'col_Horz_Deviation',
    
    'Design Station': 'col_Design_Station',
    'Sollstation': 'col_Design_Station',
    
    'Design Offset': 'col_Design_Offset',
    'Sollabstand': 'col_Design_Offset',
    
    'Measured Station': 'col_Measured_Station',
    'Gemess. Station': 'col_Measured_Station',
    
    'Measured Offset': 'col_Measured_Offset',
    'Gemess. Abstand': 'col_Measured_Offset',
    
    'Precision H': 'col_Precision_H',
    'Lagegenauigkeit': 'col_Precision_H',
    
    'Precision V': 'col_Precision_V',
    'Höhengenauigkeit': 'col_Precision_V'
}

def translate_columns(df, lang_code):
    """Veri çerçevesinin (DataFrame) sütun adlarını seçilen dile göre çevirir."""
    ui = UI_TEXT[lang_code]
    new_cols = {}
    for col in df.columns:
        if col in COLUMN_MAPPING:
            internal_key = COLUMN_MAPPING[col]
            new_cols[col] = ui.get(internal_key, col)
        else:
            new_cols[col] = col 
    return df.rename(columns=new_cols)

# --- Yardımcı Fonksiyonlar ---

def to_excel(df, header_info, lang):
    """Excel dosyası oluşturur ve biçimlendirir."""
    ui = UI_TEXT[lang]
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        start_row = 8 
        
        df.to_excel(writer, index=False, sheet_name='Report', startrow=start_row)
        
        workbook = writer.book
        worksheet = writer.sheets['Report']
        
        title_format = workbook.add_format({'bold': True, 'font_size': 16, 'font_color': '#2c3e50', 'align': 'left'})
        label_format = workbook.add_format({'bold': True, 'font_color': '#34495e', 'align': 'left'})
        text_format = workbook.add_format({'font_color': '#000000', 'align': 'left'})
        header_format = workbook.add_format({'bold': True, 'text_wrap': True, 'valign': 'top', 'fg_color': '#2980b9', 'font_color': 'white', 'border': 1})
        
        pdf_title_txt = ui.get('pdf_title', 'SiteWords Report')
        worksheet.write(0, 0, f"📑 {pdf_title_txt}", title_format)
        
        metadata = [
            (ui.get('pdf_project', 'Project:'), header_info['project']),
            (ui.get('pdf_wo', 'Work Order:'), header_info['wo']),
            (ui.get('pdf_client', 'Client:'), header_info['client']),
            (ui.get('pdf_company', 'Company:'), header_info['company']),
            (ui.get('pdf_date', 'Date:'), header_info['date']),
            (ui.get('pdf_time', 'Time:'), header_info['time'])
        ]
        
        for i, (label, value) in enumerate(metadata):
            worksheet.write(2 + i, 0, label, label_format)
            worksheet.write(2 + i, 1, value, text_format)

        for col_num, value in enumerate(df.columns.values):
            worksheet.write(start_row, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 15)
            
    return output.getvalue()

def to_csv(df):
    """CSV formatında dışa aktarır."""
    return df.to_csv(index=False).encode('utf-8')

def to_html(df, header_info, lang):
    """Stilize edilmiş HTML raporu oluşturur."""
    ui = UI_TEXT[lang]
    pdf_title_txt = ui.get('pdf_title', 'SiteWords Report')
    
    html = f"""
    <html>
    <head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; color: #333; }}
        
        .header-container {{ 
            border-bottom: 2px solid #3498db; 
            padding-bottom: 15px; 
            margin-bottom: 20px; 
        }}
        
        .header-container h1 {{ 
            border: none; 
            margin: 0; 
            padding: 0; 
            color: #2c3e50;
            font-size: 28px;
        }}
        
        .meta-container {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px; border-left: 5px solid #2980b9; }}
        .meta-row {{ display: flex; margin-bottom: 8px; align-items: center; }}
        .meta-icon {{ margin-right: 10px; font-size: 1.2em; }}
        .meta-label {{ font-weight: bold; width: 120px; color: #555; }}
        .meta-value {{ color: #000; }}
        table {{ border-collapse: collapse; width: 100%; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        th, td {{ border: 1px solid #e0e0e0; padding: 12px; text-align: left; font-size: 14px; }}
        th {{ background-color: #2980b9; color: white; text-transform: uppercase; font-size: 12px; letter-spacing: 0.5px; }}
        tr:nth-child(even) {{ background-color: #f8f9fa; }}
        tr:hover {{ background-color: #e9ecef; }}
    </style>
    </head>
    <body>
    <div class="header-container">
        <h1>📑 {pdf_title_txt}</h1>
    </div>
    
    <div class="meta-container">
        <div class="meta-row"><span class="meta-icon">🏗️</span><span class="meta-label">{ui.get('pdf_project', 'Project:')}</span><span class="meta-value">{header_info['project']}</span></div>
        <div class="meta-row"><span class="meta-icon">📋</span><span class="meta-label">{ui.get('pdf_wo', 'Work Order:')}</span><span class="meta-value">{header_info['wo']}</span></div>
        <div class="meta-row"><span class="meta-icon">👤</span><span class="meta-label">{ui.get('pdf_client', 'Client:')}</span><span class="meta-value">{header_info['client']}</span></div>
        <div class="meta-row"><span class="meta-icon">🏢</span><span class="meta-label">{ui.get('pdf_company', 'Company:')}</span><span class="meta-value">{header_info['company']}</span></div>
        <div class="meta-row"><span class="meta-icon">📅</span><span class="meta-label">{ui.get('pdf_datetime', 'Date/Time:')}</span><span class="meta-value">{header_info['date']} | {header_info['time']}</span></div>
    </div>
    
    {df.to_html(index=False)}
    </body>
    </html>
    """
    return html.encode('utf-8')

def create_pdf(df, header_info, lang):
    """Metin kaydırma ve dinamik düzen desteğiyle PDF oluşturur."""
    ui = UI_TEXT[lang]
    
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 16)
            self.set_text_color(44, 62, 80)
            title_text = ui.get('pdf_title', 'SiteWords Report').encode('latin-1', 'replace').decode('latin-1')
            self.cell(0, 10, title_text, 0, 1, 'L') 
            self.ln(5)
            
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(128)
            page_text = f"{ui.get('pdf_page', 'Page')} {self.page_no()}"
            self.cell(0, 10, page_text, 0, 0, 'C')

    pdf = PDF(orientation='L', unit='mm', format='A4') 
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0)
    pdf.set_fill_color(248, 249, 250)
    pdf.rect(10, 25, 277, 35, 'F') 
    
    start_y = 30
    pdf.set_xy(15, start_y)
    
    lbl_project = ui.get('pdf_project', 'Project:').encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(30, 8, lbl_project, 0, 0, 'L')
    pdf.set_font('Arial', '', 12)
    safe_project = header_info['project'].encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(100, 8, safe_project, 0, 1, 'L')
    
    pdf.set_x(15)
    pdf.set_font('Arial', 'B', 10)
    lbl_wo = ui.get('pdf_wo', 'Work Order:').encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(30, 6, lbl_wo, 0, 0, 'L')
    pdf.set_font('Arial', '', 10)
    safe_wo = header_info['wo'].encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(100, 6, safe_wo, 0, 1, 'L')
    
    pdf.set_x(15)
    pdf.set_font('Arial', 'B', 10)
    lbl_client = ui.get('pdf_client', 'Client:').encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(30, 6, lbl_client, 0, 0, 'L')
    pdf.set_font('Arial', '', 10)
    safe_client = header_info['client'].encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(100, 6, safe_client, 0, 1, 'L')
    
    pdf.set_x(15)
    pdf.set_font('Arial', 'B', 10)
    lbl_dt = ui.get('pdf_datetime', 'Date/Time:').encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(30, 6, lbl_dt, 0, 0, 'L')
    pdf.set_font('Arial', '', 10)
    pdf.cell(100, 6, f"{header_info['date']} | {header_info['time']}", 0, 1, 'L')
    
    pdf.ln(10)

    num_cols = len(df.columns)
    page_width = 277
    col_width = page_width / num_cols if num_cols > 0 else page_width
        
    font_size = 9
    if num_cols > 8: font_size = 7
    if num_cols > 12: font_size = 6
    
    line_height = pdf.font_size * 2
    
    pdf.set_font('Arial', 'B', font_size)
    pdf.set_fill_color(41, 128, 185)
    pdf.set_text_color(255)
    
    for col in df.columns:
        header_text = str(col).encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(col_width, line_height, header_text[:20], border=1, align='C', fill=True)
    pdf.ln(line_height)
    
    pdf.set_font('Arial', '', font_size)
    pdf.set_text_color(0)
    
    for index, row in df.iterrows():
        if pdf.get_y() > 180: 
            pdf.add_page()
            pdf.set_font('Arial', 'B', font_size)
            pdf.set_fill_color(41, 128, 185)
            pdf.set_text_color(255)
            for col in df.columns:
                header_text = str(col).encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(col_width, line_height, header_text[:20], border=1, align='C', fill=True)
            pdf.ln(line_height)
            pdf.set_font('Arial', '', font_size)
            pdf.set_text_color(0)

        start_y = pdf.get_y()
        max_y = start_y
        
        for col in df.columns:
            text = str(row[col]).encode('latin-1', 'replace').decode('latin-1')
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.multi_cell(col_width, line_height * 0.8, text, border=1, align='L')
            if pdf.get_y() > max_y:
                max_y = pdf.get_y()
            pdf.set_xy(x + col_width, y)
        pdf.set_y(max_y)

    output = pdf.output(dest='S')
    if isinstance(output, str):
        return output.encode('latin-1')
    return output

# --- Veri Ayrıştırma Fonksiyonları ---
def parse_latlon_value(coord_str):
    if pd.isna(coord_str): return math.nan
    if isinstance(coord_str, (int, float)): return float(coord_str)
    
    coord_str = str(coord_str).strip().replace(',', '.')
    
    if '°' in coord_str or "'" in coord_str or '"' in coord_str:
        match = re.search(r'(\d+)\D+(\d+)\D+([\d.]+)\D*([NSEW])?', coord_str)
        if not match: return math.nan
        deg = float(match.group(1))
        min = float(match.group(2))
        sec = float(match.group(3))
        direc = match.group(4) if match.lastindex >= 4 else None
        dd = deg + min / 60 + sec / 3600
        if direc in ['S', 'W']: dd *= -1
        return dd
    else:
        try: 
            return float(coord_str)
        except (ValueError, TypeError): 
            return math.nan

@st.cache_data(show_spinner=False)
def process_coordinates(df):
    """
    Gelişmiş koordinat işleyicisi:
    1. Satır bazında Total Station açılarının (HA/VA) Lat/Lon sanılmasını önler.
    2. Geçerli Lat/Lon yoksa UTM'den dönüştürme yapar. (Geçersiz büyük sayıları engeller)
    3. Cihazın DMS değerini Noktalı Derece (DD) gibi gizlediği hataları bulup çözer.
    """
    lat_col = next((c for c in ['HA / Lat', 'Hz / Breite'] if c in df.columns), None)
    lon_col = next((c for c in ['VA / Long', 'V / Länge'] if c in df.columns), None)
    e_col = next((c for c in ['Measured E', 'Gemess. Rechtswert'] if c in df.columns), None)
    n_col = next((c for c in ['Measured N', 'Gemess. Hochwert'] if c in df.columns), None)
    
    if lat_col:
        df['lat'] = pd.to_numeric(df[lat_col].apply(parse_latlon_value), errors='coerce')
    else:
        df['lat'] = math.nan
        
    if lon_col:
        df['lon'] = pd.to_numeric(df[lon_col].apply(parse_latlon_value), errors='coerce')
    else:
        df['lon'] = math.nan
        
    if e_col and n_col:
        df['__e'] = pd.to_numeric(df[e_col], errors='coerce')
        df['__n'] = pd.to_numeric(df[n_col], errors='coerce')
    else:
        df['__e'] = math.nan
        df['__n'] = math.nan

    # 1. Total Station Koruması (Yalnızca geçersiz olan AÇI satırlarını NaN yapar)
    invalid_mask = (df['lat'] > 90) | (df['lat'] < -90) | (df['lon'] > 180) | (df['lon'] < -180)
    df.loc[invalid_mask, ['lat', 'lon']] = math.nan

    # 2. UTM Dönüşümü Fallback (Sadece lat/lon olmayan ve UTM sınırlarında olan veriler için)
    for idx, row in df.iterrows():
        if pd.isna(row['lat']) or pd.isna(row['lon']):
            if pd.notna(row['__e']) and pd.notna(row['__n']):
                try:
                    e_float = float(row['__e'])
                    n_float = float(row['__n'])
                    
                    zone = 32 
                    
                    # 8 Haneli UTM düzeltmesi (Almanya için)
                    if 31000000 < e_float < 34000000:
                        zone = int(e_float / 1000000)
                        e_float = e_float % 10000000
                    elif 3200000 < e_float < 3400000:
                        zone = int(e_float / 100000)
                        e_float = e_float % 1000000

                    # UTM Geçerlilik Sınırı: Aşırı büyük lokal State Plane koordinatlarını (örn: 4.900.000) haritaya UTM gibi zorlamamak için
                    if 100000 < e_float < 999999 and 0 < n_float < 10000000:
                        epsg_code = f"epsg:{32600 + zone}"
                        transformer = Transformer.from_crs(epsg_code, "epsg:4326", always_xy=True)
                        new_lon, new_lat = transformer.transform(e_float, n_float)
                        
                        if -90 <= new_lat <= 90 and -180 <= new_lon <= 180:
                            df.at[idx, 'lat'] = new_lat
                            df.at[idx, 'lon'] = new_lon
                except:
                    pass

    def decode_dms(val):
        if pd.isna(val): return val
        sign = -1 if val < 0 else 1
        val = abs(val)
        d = int(val)
        m = int((val - d) * 100)
        s = (val - d - m / 100) * 10000
        return sign * (d + m / 60 + s / 3600)
                 
    # 3. DMS maskelenmesi durumu (GNSS verilerinde)
    valid_mask = df['lat'].notna() & df['lon'].notna() & df['__e'].notna() & df['__n'].notna()
    use_dms = False
    
    if valid_mask.any():
        idx = valid_mask.idxmax()
        test_lat = df.loc[idx, 'lat']
        test_lon = df.loc[idx, 'lon']
        try:
             e_val = float(df.loc[idx, '__e'])
             n_val = float(df.loc[idx, '__n'])
             
             zone = 32
             if 31000000 < e_val < 34000000:
                 zone = int(e_val / 1000000)
                 e_val = e_val % 10000000
             elif test_lon > 0:
                 zone = int(test_lon / 6) + 31
             
             # UTM koordinatı ise doğrula
             if 100000 < e_val < 999999 and 0 < n_val < 10000000:
                 epsg_code = f"epsg:{32600 + zone}" if test_lat >= 0 else f"epsg:{32700 + zone}"
                 transformer = Transformer.from_crs(epsg_code, "epsg:4326", always_xy=True)
                 utm_lon, utm_lat = transformer.transform(e_val, n_val)
                 
                 lat_dms = decode_dms(test_lat)
                 lon_dms = decode_dms(test_lon)
                 
                 dist_dd = (test_lat - utm_lat)**2 + (test_lon - utm_lon)**2
                 dist_dms = (lat_dms - utm_lat)**2 + (lon_dms - utm_lon)**2
                 
                 if dist_dms < dist_dd and dist_dms < 0.001:
                     use_dms = True
        except:
             pass

    if use_dms:
        df['lat'] = df['lat'].apply(decode_dms)
        df['lon'] = df['lon'].apply(decode_dms)

    df = df.drop(columns=['__e', '__n'])
    return df

@st.cache_data(show_spinner=False)
def parse_task_log_sessions(file_content, region_code):
    sessions = []
    # Dil varyasyonlarını destekleyen anahtar haritalama (EN/DE/FR/RO/IT)
    key_map = {
        "Date": "Date", "Datum": "Date", "Date": "Date", "Data": "Date",
        "Time": "Time", "Zeit": "Time", "Heure": "Time", "Ora": "Time",
        "Work Order": "Work Order", "Arbeitsauftrag": "Work Order", "Bon de Travail": "Work Order", "Comandă de Lucru": "Work Order", "Ordine di Lavoro": "Work Order",
        "Project": "Project", "Projekt": "Project", "Projet": "Project", "Proiect": "Project", "Progetto": "Project"
    }
    for block in re.split(r'\n\s*\n', file_content.strip()):
        lines = block.strip().split('\n')
        if not lines or not (
            lines[0].strip().startswith("Open WO") or 
            lines[0].strip().startswith("Auftrag öffnen") or
            lines[0].strip().startswith("Ouvrir BT") or
            lines[0].strip().startswith("Deschide CL") or
            lines[0].strip().startswith("Apri OL")
        ): continue
        session_data = {}
        for line in lines:
            parts = line.split('\t')
            if len(parts) >= 3:
                prop, val = parts[1].strip(), "".join(parts[2:]).strip()
                clean_key = key_map.get(prop)
                if clean_key: session_data[clean_key] = val
        if 'Date' in session_data and 'Time' in session_data: sessions.append(session_data)
    if not sessions: return None
    df = pd.DataFrame(sessions)
    if df.empty: return None
    
    datetime_str = df['Date'] + ' ' + df['Time']
    # Güvenli zaman damgası çözücü (Flexible Datetime)
    df['timestamp'] = pd.to_datetime(datetime_str, errors='coerce', dayfirst=(region_code == 'EU'))
    
    return df.dropna(subset=['timestamp']).sort_values('timestamp')[['timestamp', 'Project', 'Work Order']]

@st.cache_data(show_spinner=False)
def parse_record_log(file_content, region_code):
    lines = file_content.splitlines()
    
    # EN/DE ve diğer dillerdeki başlık satırını tespit et
    header_index = next((i for i, line in enumerate(lines) if (
        line.strip().startswith("Record Type") or 
        line.strip().startswith("Datensatztyp") or
        line.strip().startswith("Type d'enregistrement") or
        line.strip().startswith("Tip Înregistrare") or
        line.strip().startswith("Tipo di Record")
    )), -1)
    
    if header_index == -1: return None
    
    decimal_sep = '.' if region_code == 'US' else ','
    df = pd.read_csv(io.StringIO('\n'.join(lines[header_index:])), sep='\t', decimal=decimal_sep)
    df.columns = df.columns.str.strip()
    
    # Tüm yeni teknik kolon varyasyonlarını sayısal tipe dönüştürme listesi
    numeric_cols = [
        'Measured N', 'Gemess. Hochwert', 'Mesuré N', 'Nord Măsurat', 'Nord Misurato',
        'Measured E', 'Gemess. Rechtswert', 'Mesuré E', 'Est Măsurat', 'Est Misurato',
        'Measured Elv', 'Gemess. Höhe', 'Élévation Mesurée', 'Cota Măsurată', 'Quota Misurata',
        'Design N', 'Soll Hochw.',
        'Design E', 'Soll Rechtsw.',
        'Design Elv', 'Sollhöhe',
        'Cut/Fill (+/-)', 'Abtr./Auftr. (+/-)',
        'Horz Deviation', 'Lageabw.',
        'Design Offset', 'Sollabstand',
        'Measured Offset', 'Gemess. Abstand'
    ]
    for col in numeric_cols:
        if col in df.columns:
            if df[col].dtype == object:
                df[col] = pd.to_numeric(df[col].str.replace(',', '.'), errors='coerce')
            else:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
    time_col_name = next((c for c in ['Local Time', 'Ortszeit', 'Heure Locale', 'Ora Locală', 'Ora Locale'] if c in df.columns), None)
    date_col_name = next((c for c in ['Date', 'Datum', 'Date', 'Dată', 'Data'] if c in df.columns), None)
    
    if time_col_name and date_col_name:
        time_series = df[time_col_name].astype(str).str.replace(',', '.', regex=False)
        datetime_str = df[date_col_name].astype(str) + ' ' + time_series
        
        # Güvenli zaman damgası çözücü
        df['timestamp'] = pd.to_datetime(datetime_str, errors='coerce', dayfirst=(region_code == 'EU'))
        return df.dropna(subset=['timestamp']).sort_values('timestamp')
    
    return None

# --- Streamlit UI Temel Ayarları ---
st.set_page_config(page_title="SiteWords", layout="wide")

# Oturum Durumlarını Başlat
if 'app_mode' not in st.session_state:
    st.session_state['app_mode'] = 'Dashboard'
if 'report_data' not in st.session_state:
    st.session_state['report_data'] = None
if 'files_loaded' not in st.session_state:
    st.session_state['files_loaded'] = False
if 'lang' not in st.session_state:
    st.session_state['lang'] = 'en'
if 'raw_tasklog' not in st.session_state:
    st.session_state['raw_tasklog'] = None
if 'raw_record' not in st.session_state:
    st.session_state['raw_record'] = None
if 'region_code' not in st.session_state:
    st.session_state['region_code'] = 'EU'

# --- UYGULAMA MODLARI ---

def show_dashboard():
    lang = st.session_state['lang']
    ui = UI_TEXT[lang]
    
    if not st.session_state['files_loaded']:
        st.header(ui['upload_header']) 
        st.divider()
        st.info(ui['upload_info'])
        
        col1, col2, col3 = st.columns([1.5, 1.5, 4])
        with col1:
            region_code = st.selectbox(ui['region_mode'], ('EU', 'US'), index=0 if st.session_state['region_code'] == 'EU' else 1)
        with col2:
            selected_lang_name = st.selectbox(
                ui['language_mode'], 
                list(LANG_OPTIONS.keys()), 
                index=list(LANG_OPTIONS.values()).index(st.session_state['lang'])
            )
            selected_lang_code = LANG_OPTIONS[selected_lang_name]
            if selected_lang_code != st.session_state['lang']:
                st.session_state['lang'] = selected_lang_code
                st.rerun()

        with col3:
            uploaded_files = st.file_uploader(ui['upload_files'], type=['txt'], accept_multiple_files=True)

        tasklog_file = next((f for f in uploaded_files if 'tasklog' in f.name.lower()), None)
        record_file = next((f for f in uploaded_files if 'record' in f.name.lower()), None)

        if tasklog_file and record_file:
            def decode_file(file):
                content = file.getvalue()
                try: return content.decode("utf-8-sig")
                except UnicodeDecodeError: return content.decode("utf-16")
            
            tasklog_string_data = decode_file(tasklog_file)
            record_string_data = decode_file(record_file)
            
            st.session_state['raw_tasklog'] = tasklog_string_data
            st.session_state['raw_record'] = record_string_data
            st.session_state['region_code'] = region_code
            
            with st.spinner(ui['parsing_spinner']):
                df_sessions = parse_task_log_sessions(tasklog_string_data, region_code)
                df_points = parse_record_log(record_string_data, region_code)
                
                df = pd.DataFrame()
                if df_sessions is not None and df_points is not None:
                    df_points = df_points.sort_values('timestamp')
                    df_sessions = df_sessions.sort_values('timestamp')
                    df = pd.merge_asof(df_points, df_sessions, on='timestamp', direction='backward')
                elif df_points is not None:
                    df = df_points
                    st.warning(ui['tasklog_missing'])
                else:
                    st.error(ui['parse_error'])
                    return

            if not df.empty:
                df = process_coordinates(df)
                df = translate_columns(df, st.session_state['lang']) # Tablo başlıklarını çevir
                
                st.session_state['processed_df'] = df
                st.session_state['files_loaded'] = True
                
                st.rerun()
            return

    if st.session_state['files_loaded']:
        lang = st.session_state['lang']
        ui = UI_TEXT[lang]
        
        head_col1, head_col2, head_col3, head_col4 = st.columns([4, 2, 2, 2])
        with head_col1:
            st.header(ui['dash_header'])
        with head_col2:
            new_region = st.selectbox(ui['region_mode'], ('EU', 'US'), index=0 if st.session_state['region_code'] == 'EU' else 1, label_visibility="collapsed")
            if new_region != st.session_state['region_code']:
                st.session_state['region_code'] = new_region
                with st.spinner(ui['parsing_spinner']):
                    df_sessions = parse_task_log_sessions(st.session_state['raw_tasklog'], new_region)
                    df_points = parse_record_log(st.session_state['raw_record'], new_region)
                    
                    df = pd.DataFrame()
                    if df_sessions is not None and df_points is not None:
                        df_points = df_points.sort_values('timestamp')
                        df_sessions = df_sessions.sort_values('timestamp')
                        df = pd.merge_asof(df_points, df_sessions, on='timestamp', direction='backward')
                    elif df_points is not None:
                        df = df_points
                    
                    if not df.empty:
                        df = process_coordinates(df)
                        df = translate_columns(df, st.session_state['lang'])
                        st.session_state['processed_df'] = df
                        st.session_state['dashboard_selection'] = []
                st.rerun()

        with head_col3:
            selected_lang_name = st.selectbox(
                "Lang", 
                list(LANG_OPTIONS.keys()), 
                index=list(LANG_OPTIONS.values()).index(st.session_state['lang']),
                label_visibility="collapsed"
            )
            selected_lang_code = LANG_OPTIONS[selected_lang_name]
            if selected_lang_code != st.session_state['lang']:
                st.session_state['lang'] = selected_lang_code
                
                if st.session_state['raw_tasklog'] and st.session_state['raw_record']:
                    with st.spinner(ui['parsing_spinner']):
                        df_sessions = parse_task_log_sessions(st.session_state['raw_tasklog'], st.session_state['region_code'])
                        df_points = parse_record_log(st.session_state['raw_record'], st.session_state['region_code'])
                        df = pd.DataFrame()
                        if df_sessions is not None and df_points is not None:
                            df_points = df_points.sort_values('timestamp')
                            df_sessions = df_sessions.sort_values('timestamp')
                            df = pd.merge_asof(df_points, df_sessions, on='timestamp', direction='backward')
                        elif df_points is not None:
                            df = df_points
                        
                        if not df.empty:
                            df = process_coordinates(df)
                            df = translate_columns(df, st.session_state['lang'])
                            st.session_state['processed_df'] = df
                st.rerun()

        with head_col4:
            if st.button(ui['clear_files'], width='stretch'):
                st.session_state['files_loaded'] = False
                st.session_state['processed_df'] = None
                st.session_state['raw_tasklog'] = None
                st.session_state['raw_record'] = None
                if 'dashboard_selection' in st.session_state:
                    del st.session_state['dashboard_selection']
                st.rerun()
                
        st.divider()
            
        df = st.session_state['processed_df']
        
        col_table, col_map = st.columns([1, 1])

        with col_table:
            st.subheader(ui['field_data_sel'])
            st.caption(ui['sel_caption'])
            
            df_clean = df.copy().dropna(axis=1, how='all')
            df_export = df_clean.copy() 
            
            df_display = df_clean.copy()
            numeric_cols = df_display.select_dtypes(include=['float64', 'float32']).columns
            for col in numeric_cols:
                if st.session_state['region_code'] == 'EU':
                    df_display[col] = df_display[col].apply(lambda x: f"{x:,.3f}".replace(',', 'X').replace('.', ',').replace('X', '.') if pd.notna(x) else x)
                else:
                    df_display[col] = df_display[col].apply(lambda x: f"{x:,.3f}" if pd.notna(x) else x)
            
            event = st.dataframe(
                df_display, 
                key="dashboard_table", 
                width='stretch',
                height=600,
                hide_index=True,
                on_select="rerun",
                selection_mode="multi-row"
            )
            
            selected_rows_indices = event.selection.rows
            st.session_state['dashboard_selection'] = selected_rows_indices
            
            if not selected_rows_indices:
                btn_text = ui['report_all']
                help_text = ui['report_all_help']
                df_to_report = df_export
            else:
                btn_text = f"{ui['report_sel_base']} ({len(selected_rows_indices)} {ui.get('rows', 'rows')})"
                help_text = ui['report_sel_help']
                df_to_report = df_export.iloc[selected_rows_indices]

            if st.button(btn_text, type="primary", help=help_text, width='stretch'):
                st.session_state['report_data'] = df_to_report
                st.session_state['app_mode'] = 'Report'
                st.rerun()

        with col_map:
            c_map_title, c_map_style = st.columns([3, 2])
            with c_map_title:
                st.subheader(ui['map_header'])
                st.caption(ui['map_caption'])
            with c_map_style:
                style_options = {
                    ui['style_light']: 'light',
                    ui['style_dark']: 'dark',
                    ui['style_road']: 'road'
                }
                selected_style_name = st.selectbox(ui['map_style_label'], list(style_options.keys()), label_visibility="collapsed")
                selected_map_style = style_options[selected_style_name]
            
            map_data_cols = ['lat', 'lon']
            
            pt_col = ui.get('col_Point_Name', 'Point Name')
            tooltip_html = "<b>Lat:</b> {lat}<br/><b>Lon:</b> {lon}"
            if pt_col in df.columns:
                map_data_cols.append(pt_col)
                tooltip_html = f"<b>{ui['map_pt_name']}:</b> {{{pt_col}}}<br/>" + tooltip_html
            
            map_data = df[map_data_cols].dropna(subset=['lat', 'lon'])

            if not map_data.empty:
                center_lat = map_data['lat'].mean()
                center_lon = map_data['lon'].mean()
                
                view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=16, pitch=0)
                
                selected_indices = st.session_state.get('dashboard_selection', [])
                
                if selected_indices:
                    sel_idxs_pd = pd.Index(selected_indices)
                    valid_sel_idxs = sel_idxs_pd.intersection(map_data.index)
                    sel_pts = map_data.loc[valid_sel_idxs]
                    other_pts = map_data.loc[map_data.index.difference(valid_sel_idxs)]
                else:
                    sel_pts = pd.DataFrame(columns=map_data.columns)
                    other_pts = map_data
                
                layers = []
                if not other_pts.empty:
                    layers.append(pdk.Layer('ScatterplotLayer', data=other_pts, get_position='[lon, lat]', get_fill_color='[0, 100, 255]', get_radius=5, radius_units='pixels', pickable=True))
                
                if not sel_pts.empty:
                    layers.append(pdk.Layer('ScatterplotLayer', data=sel_pts, get_position='[lon, lat]', get_fill_color='[0, 255, 0]', get_radius=8, radius_units='pixels', pickable=True))
                
                st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=view_state, map_style=selected_map_style, tooltip={"html": tooltip_html}), height=600)
            else:
                st.info(ui['map_no_coord'])

def show_report_generator():
    lang = st.session_state['lang']
    ui = UI_TEXT[lang]
    
    st.header(ui['rep_header'])
    
    if st.button(ui['back_dash']):
        st.session_state['app_mode'] = 'Dashboard'
        st.rerun()
        
    df_raw = st.session_state['report_data']
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader(ui['proj_details'])
        def_proj = df_raw['Project'].iloc[0] if 'Project' in df_raw.columns else ""
        def_wo = df_raw['Work Order'].iloc[0] if 'Work Order' in df_raw.columns else ""
        
        r_project = st.text_input(ui['proj_name'], value=def_proj)
        r_wo = st.text_input(ui['work_order'], value=def_wo)
        r_client = st.text_input(ui['client_name'], "Client XYZ")
        
    with c2:
        st.subheader(ui['rep_meta'])
        r_company = st.text_input(ui['company_name'], "My Surveying Co.")
        r_date = st.date_input(ui['rep_date'], datetime.now())
        r_time = st.time_input(ui['rep_time'], datetime.now())
    
    st.divider()
    
    all_columns = df_raw.columns.tolist()
    
    # Rapor ekranında varsayılan olarak tikli (seçili) gelecek olan kolonlar.
    # Yeni Aplikasyon kolonları (Cut/Fill, Design Elv) buraya eklendi.
    preferred_cols = [
        ui.get('col_Sub_Type', 'Sub Type'),
        ui.get('col_Point_Name', 'Point Name'),
        ui.get('col_Measured_E', 'Measured Easting'),
        ui.get('col_Measured_N', 'Measured Northing'),
        ui.get('col_Measured_Elv', 'Measured Elevation'),
        ui.get('col_Design_Elv', 'Design Elv'),
        ui.get('col_Cut_Fill', 'Cut/Fill (+/-)'),
        ui.get('col_Horz_Deviation', 'Horz Deviation'),
        ui.get('col_Precision_H', 'Precision H'),
        ui.get('col_Precision_V', 'Precision V')
    ]
    
    selected_columns = []
    initial_selection = [c for c in preferred_cols if c in all_columns]
    
    with st.expander(ui['col_sel_expander'], expanded=False):
        st.caption(ui['col_sel_caption'])
        
        cols_grid = st.columns(5)
        
        for i, col_name in enumerate(all_columns):
            is_preferred = col_name in preferred_cols
            if cols_grid[i % 5].checkbox(col_name, value=is_preferred, key=f"chk_{i}"):
                selected_columns.append(col_name)
    
    if not selected_columns:
        st.warning(ui['col_warning'])
        cols_to_include = initial_selection
    else:
        cols_to_include = [c for c in all_columns if c in selected_columns]
        
    df_report = df_raw[cols_to_include]

    # Önizleme için tablo formatlamasını uygula
    df_report_display = df_report.copy()
    for col in df_report_display.select_dtypes(include=['float64', 'float32']).columns:
        if st.session_state['region_code'] == 'EU':
            df_report_display[col] = df_report_display[col].apply(lambda x: f"{x:,.3f}".replace(',', 'X').replace('.', ',').replace('X', '.') if pd.notna(x) else x)
        else:
            df_report_display[col] = df_report_display[col].apply(lambda x: f"{x:,.3f}" if pd.notna(x) else x)

    st.subheader(f"{ui.get('rep_preview', 'Report Preview')} ({len(df_report)} {ui.get('rows', 'rows')})")
    st.dataframe(df_report_display, width='stretch', hide_index=True)
    
    header_info = {
        "project": r_project, "wo": r_wo, "client": r_client,
        "company": r_company, "date": str(r_date), "time": str(r_time)
    }
    
    st.divider()
    st.subheader(ui['export_opts'])
    
    clean_project_name = re.sub(r'[^\w\-_]', '_', r_project) if r_project else "Project"
    
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        pdf_bytes = create_pdf(df_report, header_info, lang)
        st.download_button(
            label=ui['dl_pdf'],
            data=pdf_bytes,
            file_name=f"Report_{clean_project_name}.pdf",
            mime="application/pdf",
            type="primary",
            width='stretch',
            key="btn_download_pdf"
        )
        
    with c2:
        excel_bytes = to_excel(df_report, header_info, lang)
        st.download_button(
            label=ui['dl_excel'],
            data=excel_bytes,
            file_name=f"Report_{clean_project_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width='stretch',
            key="btn_download_excel"
        )
        
    with c3:
        csv_bytes = to_csv(df_report)
        st.download_button(
            label=ui['dl_csv'],
            data=csv_bytes,
            file_name=f"Report_{clean_project_name}.csv",
            mime="text/csv",
            width='stretch',
            key="btn_download_csv"
        )
        
    with c4:
        html_bytes = to_html(df_report, header_info, lang)
        st.download_button(
            label=ui['dl_html'],
            data=html_bytes,
            file_name=f"Report_{clean_project_name}.html",
            mime="text/html",
            width='stretch',
            key="btn_download_html"
        )

# --- ANA UYGULAMA YÖNLENDİRİCİSİ ---
if st.session_state['app_mode'] == 'Dashboard':
    show_dashboard()
elif st.session_state['app_mode'] == 'Report':
    show_report_generator()
