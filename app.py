import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import date, datetime
import os

# ==========================================
# 1. CONFIGURACIÓN DE BASE DE DATOS (SQLite)
# ==========================================
DB_FILE = 'cotizaciones_v3.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS cotizaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE,
            proveedor TEXT,
            contacto TEXT,
            equipo TEXT,
            especificacion TEXT,
            tipo_tarifa TEXT,
            origen TEXT,
            destino TEXT,
            costo_alquiler REAL,
            costo_flete REAL,
            observaciones TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insertar_cotizacion(fecha, prov, contacto, equipo, esp, tarifa, origen, destino, alquiler, flete, obs):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO cotizaciones (fecha, proveedor, contacto, equipo, especificacion, tipo_tarifa, origen, destino, costo_alquiler, costo_flete, observaciones)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (fecha, prov, contacto, equipo, esp, tarifa, origen, destino, alquiler, flete, obs))
    conn.commit()
    conn.close()

def actualizar_cotizacion(id_cot, fecha, prov, contacto, equipo, esp, tarifa, origen, destino, alquiler, flete, obs):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        UPDATE cotizaciones 
        SET fecha=?, proveedor=?, contacto=?, equipo=?, especificacion=?, tipo_tarifa=?, origen=?, destino=?, costo_alquiler=?, costo_flete=?, observaciones=?
        WHERE id=?
    ''', (fecha, prov, contacto, equipo, esp, tarifa, origen, destino, alquiler, flete, obs, id_cot))
    conn.commit()
    conn.close()

def eliminar_cotizacion(id_cot):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM cotizaciones WHERE id=?', (id_cot,))
    conn.commit()
    conn.close()

def cargar_datos():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query('SELECT * FROM cotizaciones', conn)
    conn.close()
    return df

def formato_pesos(valor):
    return f"$ {valor:,.0f}".replace(",", ".")

# Inicializar BD
init_db()

# ==========================================
# 2. INTERFAZ DE USUARIO (UI)
# ==========================================
st.set_page_config(page_title="Directorio Polyuprotec", layout="wide")

# --- LOGO EN LA BARRA LATERAL ---
# Busca un archivo llamado 'logo.png' o 'logo.jpg' en tu carpeta
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)
elif os.path.exists("logo.jpg"):
    st.sidebar.image("logo.jpg", use_container_width=True)
else:
    st.sidebar.info("📌 Guarda el logo de Polyuprotec como 'logo.png' en esta misma carpeta para que aparezca aquí.")

st.title("🚜 Panel Interactivo de Cotizaciones y Fletes")

df = cargar_datos()

opciones_equipos = ["Camión Grúa", "Grúa Telescópica", "Montacarga", "Manlift", "Tijeras", "Andamios", "Otro"]
opciones_tarifas = ["Por Día", "Por Mes", "Global (Todo el proyecto)"]

# --- SECCIÓN A: REGISTRAR NUEVA COTIZACIÓN ---
with st.expander("➕ Registrar Nueva Cotización", expanded=False):
    with st.container(border=True):
        st.markdown("### 🏢 Datos del Proveedor")
        col1, col2, col3 = st.columns(3)
        with col1: fecha_cot = st.date_input("Fecha de Cotización", date.today())
        with col2: prov = st.text_input("Nombre del Proveedor *")
        with col3: contacto = st.text_input("Teléfono/Email de Contacto")

    with st.container(border=True):
        st.markdown("### 🏗️ Detalles del Equipo")
        col_eq1, col_eq2, col_eq3 = st.columns(3)
        with col_eq1: 
            equipo = st.selectbox("Tipo de Equipo", opciones_equipos)
        
        with col_eq2:
            if equipo in ["Grúa Telescópica", "Camión Grúa", "Montacarga"]:
                esp_val = st.number_input("Capacidad de Carga (Toneladas)", min_value=0.0, step=1.0)
                esp_final = f"{esp_val} Toneladas"
            elif equipo in ["Manlift", "Tijeras", "Andamios"]:
                esp_val = st.number_input("Altura de Trabajo (Metros)", min_value=0.0, step=1.0)
                esp_final = f"{esp_val} Metros"
            else:
                esp_final = st.text_input("Especificación Técnica")

        with col_eq3:
            tarifa = st.selectbox("Tipo de Tarifa", opciones_tarifas)

    with st.container(border=True):
        st.markdown("### 🚚 Logística y Costos")
        col_log1, col_log2, col_log3, col_log4 = st.columns(4)
        with col_log1: orig = st.text_input("Origen (Ciudad/Depto) *")
        with col_log2: dest = st.text_input("Destino *")
        with col_log3: alquiler = st.number_input("Costo de Alquiler", min_value=0, step=50000)
        with col_log4: flete = st.number_input("Costo de Flete", min_value=0, step=50000)
            
    obs = st.text_area("Observaciones")
    
    if st.button("💾 Guardar Cotización", type="primary", use_container_width=True):
        if prov and orig and dest:
            insertar_cotizacion(fecha_cot, prov, contacto, equipo, esp_final, tarifa, orig, dest, alquiler, flete, obs)
            st.success("✅ Cotización guardada correctamente.")
            st.rerun()
        else:
            st.error("Por favor, completa los campos obligatorios (*).")


# --- SECCIÓN B: GESTIONAR REGISTROS (EDITAR / ELIMINAR) ---
if not df.empty:
    with st.expander("✏️ Editar o 🗑️ Eliminar un Registro", expanded=False):
        opciones_registro = df['id'].astype(str) + " - " + df['proveedor'] + " (" + df['equipo'] + " de " + df['especificacion'] + ")"
        seleccion = st.selectbox("Selecciona la cotización a modificar:", opciones_registro)
        
        if seleccion:
            id_seleccionado = int(seleccion.split(" - ")[0])
            registro = df[df['id'] == id_seleccionado].iloc[0]
            
            try: fecha_actual = datetime.strptime(registro['fecha'], "%Y-%m-%d").date()
            except: fecha_actual = date.today()

            tab1, tab2 = st.tabs(["✏️ Editar Cotización", "🗑️ Eliminar Cotización"])
            
            with tab1:
                st.info("Modifica los campos necesarios y presiona Actualizar.")
                c1, c2, c3 = st.columns(3)
                
                with c1:
                    n_fecha = st.date_input("Fecha", fecha_actual, key="ed_f")
                    n_prov = st.text_input("Proveedor", registro['proveedor'], key="ed_p")
                    n_cont = st.text_input("Contacto", registro['contacto'] if pd.notna(registro['contacto']) else "", key="ed_c")
                
                with c2:
                    idx_eq = opciones_equipos.index(registro['equipo']) if registro['equipo'] in opciones_equipos else 0
                    n_eq = st.selectbox("Equipo", opciones_equipos, index=idx_eq, key="ed_eq")
                    
                    if n_eq in ["Grúa Telescópica", "Camión Grúa", "Montacarga"]:
                        val_def = float(registro['especificacion'].split()[0]) if "Ton" in str(registro['especificacion']) else 0.0
                        n_esp_val = st.number_input("Capacidad (Ton)", min_value=0.0, step=1.0, value=val_def, key="ed_esp_t")
                        n_esp = f"{n_esp_val} Toneladas"
                    elif n_eq in ["Manlift", "Tijeras", "Andamios"]:
                        val_def = float(registro['especificacion'].split()[0]) if "Met" in str(registro['especificacion']) else 0.0
                        n_esp_val = st.number_input("Altura (Mts)", min_value=0.0, step=1.0, value=val_def, key="ed_esp_m")
                        n_esp = f"{n_esp_val} Metros"
                    else:
                        n_esp = st.text_input("Especificación", str(registro['especificacion']), key="ed_esp_o")
                        
                    n_ori = st.text_input("Origen", registro['origen'], key="ed_o")
                
                with c3:
                    idx_tar = opciones_tarifas.index(registro['tipo_tarifa']) if registro['tipo_tarifa'] in opciones_tarifas else 0
                    n_tar = st.selectbox("Tarifa", opciones_tarifas, index=idx_tar, key="ed_tar")
                    n_des = st.text_input("Destino", registro['destino'], key="ed_d")
                    n_alq = st.number_input("Alquiler", min_value=0, value=int(registro['costo_alquiler']), step=50000, key="ed_a")
                    n_fle = st.number_input("Flete", min_value=0, value=int(registro['costo_flete']), step=50000, key="ed_fl")
                
                n_obs = st.text_area("Observaciones", registro['observaciones'] if pd.notna(registro['observaciones']) else "", key="ed_obs")
                
                if st.button("Actualizar Registro", type="primary", key="btn_actualizar"):
                    actualizar_cotizacion(id_seleccionado, n_fecha, n_prov, n_cont, n_eq, n_esp, n_tar, n_ori, n_des, n_alq, n_fle, n_obs)
                    st.success("¡Registro actualizado con éxito!")
                    st.rerun()

            with tab2:
                st.warning(f"⚠️ Estás a punto de eliminar la cotización #{id_seleccionado} de {registro['proveedor']}")
                if st.button("Sí, Eliminar Definitivamente", type="primary", key="btn_eliminar"):
                    eliminar_cotizacion(id_seleccionado)
                    st.success("Registro eliminado.")
                    st.rerun()

# ==========================================
# 3. PROCESAMIENTO Y DASHBOARD
# ==========================================
st.divider()

if not df.empty:
    df['costo_total'] = df['costo_alquiler'] + df['costo_flete']
    
    # --- KPIs Visuales Rápidos ---
    c_kpi1, c_kpi2, c_kpi3 = st.columns(3)
    c_kpi1.metric("Total Cotizaciones", len(df))
    c_kpi2.metric("Equipos Únicos", df['equipo'].nunique())
    c_kpi3.metric("Proveedores", df['proveedor'].nunique())
    
    # --- Sidebar Filtros ---
    st.sidebar.header("Filtros de Búsqueda")
    equipo_sel = st.sidebar.selectbox("Filtro por Equipo", ['Todos'] + list(df['equipo'].unique()))
    tarifa_sel = st.sidebar.selectbox("Filtro por Tarifa", ['Todos'] + list(df['tipo_tarifa'].unique()))
    origen_sel = st.sidebar.selectbox("Filtro por Origen", ['Todos'] + list(df['origen'].unique()))
    
    df_filtrado = df.copy()
    if equipo_sel != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['equipo'] == equipo_sel]
    if tarifa_sel != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['tipo_tarifa'] == tarifa_sel]
    if origen_sel != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['origen'] == origen_sel]
    
    # --- Tabla Formateada ---
    df_display = df_filtrado.copy()
    for col in ['costo_alquiler', 'costo_flete', 'costo_total']:
        df_display[col] = df_display[col].apply(formato_pesos)
    
    df_display = df_display[['id', 'fecha', 'proveedor', 'equipo', 'especificacion', 'tipo_tarifa', 'origen', 'destino', 'costo_alquiler', 'costo_flete', 'costo_total', 'contacto', 'observaciones']]
    
    # Botón de Descarga Excel / CSV
    st.write("### Base de Datos General")
    csv_data = df_display.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Tabla a Excel (CSV)",
        data=csv_data,
        file_name=f"Cotizaciones_Equipos_{date.today()}.csv",
        mime='text/csv',
        use_container_width=True
    )
    
    st.dataframe(
        df_display, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "observaciones": st.column_config.TextColumn("Observaciones", width="large"),
            "proveedor": st.column_config.TextColumn("Proveedor", width="medium"),
            "costo_total": st.column_config.TextColumn("Costo Total", width="medium")
        }
    )
    
    # --- Gráficos ---
    st.subheader("Análisis de Costos Comparativos")
    if not df_filtrado.empty:
        fig = px.bar(
            df_filtrado, 
            x='proveedor', 
            y=['costo_alquiler', 'costo_flete'],
            title=f"Desglose de Costos (Alquiler + Flete)",
            labels={'value': 'Costo (COP)', 'variable': 'Concepto', 'proveedor': 'Proveedor'},
            color_discrete_sequence=['#1f77b4', '#2ca02c'], 
            text_auto='.2s'
        )
        fig.update_layout(yaxis_tickformat=',.0f', barmode='stack')
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("La base de datos está vacía. Registra tu primera cotización arriba.")