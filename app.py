import streamlit as st
import pandas as pd
import pydeck as pdk
import io
import re
from pyproj import Transformer, CRS

def parse_latlon_value(coord_str):
    if not isinstance(coord_str, str):
        return None
    coord_str = coord_str.strip().replace(',', '.')
    if '°' in coord_str or "'" in coord_str or '"' in coord_str:
        match = re.search(r'(\d+)\D+(\d+)\D+([\d.]+)\D*([NSEW])', coord_str)
        if not match: return None
        deg, min, sec, direc = match.groups()
        dd = float(deg) + float(min) / 60 + float(sec) / 3600
        if direc in ['S', 'W']: dd *= -1
        return dd
    else:
        try: return float(coord_str)
        except (ValueError, TypeError): return None

def convert_ne_to_latlon(df, easting_col, northing_col, source_epsg="epsg:32632"):
    try:
        source_crs = CRS(source_epsg)
        target_crs = CRS("epsg:4326")
        transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
        
        valid_data = df.loc[pd.to_numeric(df[easting_col], errors='coerce').notna() & 
                            pd.to_numeric(df[northing_col], errors='coerce').notna()]
        
        if valid_data.empty:
            return pd.Series(None, index=df.index), pd.Series(None, index=df.index)
            
        lon, lat = transformer.transform(valid_data[easting_col].values, valid_data[northing_col].values)
        
        lat_series = pd.Series(lat, index=valid_data.index)
        lon_series = pd.Series(lon, index=valid_data.index)
        
        return lat_series, lon_series
    except Exception as e:
        st.warning(f"Coordinate conversion failed: {e}. Check EPSG code.")
        return pd.Series(None, index=df.index), pd.Series(None, index=df.index)

def parse_task_log_sessions(file_content, region_code):
    sessions = []
    key_map = {"Date": "Date", "Datum": "Date", "Time": "Time", "Zeit": "Time", "Work Order": "Work Order", "Arbeitsauftrag": "Work Order", "Project": "Project", "Projekt": "Project"}
    
    for block in re.split(r'\n\s*\n', file_content.strip()):
        lines = block.strip().split('\n')
        if not lines or not (lines[0].strip().startswith("Open WO") or lines[0].strip().startswith("Auftrag öffnen")):
            continue
        
        session_data = {}
        for line in lines:
            parts = line.split('\t')
            if len(parts) >= 3:
                prop, val = parts[1].strip(), "".join(parts[2:]).strip()
                clean_key = key_map.get(prop)
                if clean_key: 
                    session_data[clean_key] = val
        if 'Date' in session_data and 'Time' in session_data:
            sessions.append(session_data)
            
    if not sessions: 
        return None
        
    df = pd.DataFrame(sessions)
    
    datetime_str = df['Date'] + ' ' + df['Time']
    
    if region_code == "US":
        date_format = '%m/%d/%Y %I:%M:%S %p'
    else:
        date_format = '%d.%m.%Y %H:%M:%S'
        
    df['timestamp'] = pd.to_datetime(datetime_str, format=date_format, errors='coerce')
    
    if df['timestamp'].isnull().any():
        if region_code == "US":
            fallback_format = '%d.%m.%Y %H:%M:%S'
        else:
            fallback_format = '%m/%d/%Y %I:%M:%S %p'
        df['timestamp'] = df['timestamp'].fillna(pd.to_datetime(datetime_str, format=fallback_format, errors='coerce'))

    return df.dropna(subset=['timestamp']).sort_values('timestamp')[['timestamp', 'Project', 'Work Order']]

def parse_record_log(file_content, region_code):
    lines = file_content.splitlines()
    header_index = next((i for i, line in enumerate(lines) if line.strip().startswith("Record Type")), -1)
    if header_index == -1: return None
    
    decimal_sep = '.' if region_code == 'US' else ','
    
    df = pd.read_csv(io.StringIO('\n'.join(lines[header_index:])), sep='\t', decimal=decimal_sep)
    df.columns = df.columns.str.strip()
    
    for col in ['Measured N', 'Measured E', 'Measured Elv']:
        if col in df.columns: 
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    time_col = df['Local Time'].str.replace(',', '.', regex=False)
    datetime_str = df['Date'] + ' ' + time_col
    
    if region_code == "US":
        date_format = '%m/%d/%Y %H:%M:%S.%f'
        fallback_format = '%d.%m.%Y %H:%M:%S.%f'
    else:
        date_format = '%d.%m.%Y %H:%M:%S.%f'
        fallback_format = '%m/%d/%Y %H:%M:%S.%f'

    df['timestamp'] = pd.to_datetime(datetime_str, format=date_format, errors='coerce')
    df['timestamp'] = df['timestamp'].fillna(pd.to_datetime(datetime_str, format=fallback_format, errors='coerce'))
    
    return df.dropna(subset=['timestamp']).sort_values('timestamp')

st.set_page_config(page_title="SiteWords: Reporting Tool", layout="wide")

st.sidebar.header('📋 SiteWords: Reporting Tool') 

map_container = st.sidebar.container() 

st.sidebar.divider()
region_code = st.sidebar.selectbox("Region Mode (Dates/Decimals)", ('EU', 'US'))
uploaded_files = st.sidebar.file_uploader("Upload Log Files", type=['txt'], accept_multiple_files=True)

tasklog_file = next((f for f in uploaded_files if 'tasklog' in f.name.lower()), None)
record_file = next((f for f in uploaded_files if 'record' in f.name.lower()), None)

if tasklog_file and record_file:
    def decode_file(file):
        content = file.getvalue()
        try: return content.decode("utf-8-sig")
        except UnicodeDecodeError: return content.decode("utf-16")
    
    tasklog_string_data = decode_file(tasklog_file)
    record_string_data = decode_file(record_file)
    
    with st.spinner('Parsing and combining all log data...'):
        df_sessions = parse_task_log_sessions(tasklog_string_data, region_code)
        df_points = parse_record_log(record_string_data, region_code)
        df = pd.DataFrame()
        if df_sessions is not None and df_points is not None:
            df = pd.merge_asof(df_points, df_sessions, on='timestamp', direction='backward')
        elif df_points is not None:
            df = df_points
            st.warning("Could not parse TaskLog file. Showing only Record data.")
        else:
            st.error("Failed to parse the Record log file. Please check the file format.")

    if not df.empty:
        st.caption(f'Found and processed {len(df)} measurement records. Region: **{region_code}**')
        
        df['lat'] = df['HA / Lat'].apply(parse_latlon_value) if 'HA / Lat' in df.columns else None
        df['lon'] = df['VA / Long'].apply(parse_latlon_value) if 'VA / Long' in df.columns else None
        
        missing_coords = df['lat'].isnull()
        if missing_coords.any() and 'Measured E' in df.columns and 'Measured N' in df.columns:
            st.info("Attempting to convert Northing/Easting for some points...")
            lat_converted, lon_converted = convert_ne_to_latlon(df[missing_coords], 'Measured E', 'Measured N')
            df.loc[missing_coords, 'lat'] = lat_converted
            df.loc[missing_coords, 'lon'] = lon_converted

        st.subheader("Field Data Table")
        
        df_display = df.copy().dropna(axis=1, how='all')
        df_display.insert(0, "Select", False)
        
        final_display_columns = [col for col in df_display.columns if col != 'Select']
        
        edited_df = st.data_editor(
            df_display, 
            key="data_editor", 
            width='stretch', 
            hide_index=True,
            disabled=final_display_columns
        )
        
        selected_rows = edited_df[edited_df.Select] 

        map_data_columns = ['lat', 'lon']
        tooltip_html = "<b>Lat:</b> {lat}<br/><b>Lon:</b> {lon}"
        
        if "Point Name" in df.columns:
            map_data_columns.append("Point Name")
            tooltip_html = "<b>Point Name:</b> {Point Name}<br/>" + tooltip_html
        
        map_data = df[map_data_columns].dropna(subset=['lat', 'lon'])

        if not map_data.empty:
            
            first_point_df = map_data.iloc[[0]]
            first_point_index = first_point_df.index[0]
            
            view_state = pdk.ViewState(
                latitude=first_point_df['lat'].iloc[0], 
                longitude=first_point_df['lon'].iloc[0], 
                zoom=15, 
                pitch=0
            )
            
            selected_indices = selected_rows.index
            selected_points_df = map_data.loc[selected_indices.difference([first_point_index])]
            other_indices = map_data.index.difference(selected_indices).difference([first_point_index])
            other_points_df = map_data.loc[other_indices]
            
            layers = [
                pdk.Layer('ScatterplotLayer', data=other_points_df, get_position='[lon, lat]', get_fill_color='[0, 100, 255]', get_radius=5, radius_units='pixels', pickable=True),
                pdk.Layer('ScatterplotLayer', data=first_point_df, get_position='[lon, lat]', get_fill_color='[255, 0, 0]', get_radius=8, radius_units='pixels', pickable=True)
            ]

            if not selected_points_df.empty:
                layers.append(pdk.Layer(
                    'ScatterplotLayer', data=selected_points_df, get_position='[lon, lat]', 
                    get_fill_color='[0, 255, 0]', get_radius=8, radius_units='pixels'
                ))
                last_selected = selected_points_df.iloc[-1]
                view_state.latitude = last_selected['lat']
                view_state.longitude = last_selected['lon']
                view_state.zoom = 17

            with map_container:
                
                carto_light_style = 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json'

                st.pydeck_chart(pdk.Deck(
                    layers=layers, 
                    initial_view_state=view_state,
                    map_style=carto_light_style,
                    tooltip={"html": tooltip_html}
                ))
            
        else:
            with map_container:
                st.info("No valid coordinates found to display on the map.")
            
    elif uploaded_files:
        st.error("Could not process the uploaded file(s). Please check the file format.")
        
else:
    st.header('📋 SiteWords: Reporting Tool') 
    st.info('To begin, select your Region and upload both a TaskLog and a Record file using the sidebar.')
