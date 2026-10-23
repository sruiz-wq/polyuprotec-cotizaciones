import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
from datetime import date, datetime
from supabase import create_client, Client

# ==========================================
# 1. CONFIGURACIÓN DE BASE DE DATOS Y NUBE (SUPABASE)
# ==========================================
# Conexión al Storage (Para los PDFs)
supabase_url = st.secrets["SUPABASE_URL"]
supabase_key = st.secrets["SUPABASE_KEY"]
supabase_client: Client = create_client(supabase_url, supabase_key)

def get_connection():
    # Conexión a PostgreSQL (Para los datos de las tablas)
    return psycopg2.connect(st.secrets["DATABASE_URL"])

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS cotizaciones (
            id SERIAL PRIMARY KEY,
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
            archivo_pdf TEXT,
            observaciones TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS servicios (
            id SERIAL PRIMARY KEY,
            fecha DATE,
            proveedor TEXT,
            contacto TEXT,
            tipo_servicio TEXT,
            alcance TEXT,
            ubicacion TEXT,
            costo_total REAL,
            archivo_pdf TEXT,
            observaciones TEXT
        )
    ''')
    conn.commit()
    c.close()
    conn.close()

# --- FUNCIONES EQUIPOS ---
def insertar_cotizacion(fecha, prov, contacto, equipo, esp, tarifa, origen, destino, alquiler, flete, pdf_nombre, obs):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO cotizaciones (fecha, proveedor, contacto, equipo, especificacion, tipo_tarifa, origen, destino, costo_alquiler, costo_flete, archivo_pdf, observaciones)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (fecha, prov, contacto, equipo, esp, tarifa, origen, destino, alquiler, flete, pdf_nombre, obs))
    conn.commit()
    c.close()
    conn.close()
    st.cache_data.clear()

def actualizar_cotizacion(id_cot, fecha, prov, contacto, equipo, esp, tarifa, origen, destino, alquiler, flete, obs):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE cotizaciones 
        SET fecha=%s, proveedor=%s, contacto=%s, equipo=%s, especificacion=%s, tipo_tarifa=%s, origen=%s, destino=%s, costo_alquiler=%s, costo_flete=%s, observaciones=%s
        WHERE id=%s
    ''', (fecha, prov, contacto, equipo, esp, tarifa, origen, destino, alquiler, flete, obs, id_cot))
    conn.commit()
    c.close()
    conn.close()
    st.cache_data.clear()

def eliminar_cotizacion(id_cot):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM cotizaciones WHERE id=%s', (id_cot,))
    conn.commit()
    c.close()
    conn.close()
    st.cache_data.clear()

@st.cache_data(ttl=300)
def cargar_datos():
    conn = get_connection()
    df = pd.read_sql_query('SELECT * FROM cotizaciones', conn)
    conn.close()
    return df

# --- FUNCIONES SERVICIOS ---
def insertar_servicio(fecha, prov, contacto, tipo_serv, alcance, ubicacion, costo, pdf_nombre, obs):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO servicios (fecha, proveedor, contacto, tipo_servicio, alcance, ubicacion, costo_total, archivo_pdf, observaciones)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (fecha, prov, contacto, tipo_serv, alcance, ubicacion, costo, pdf_nombre, obs))
    conn.commit()
    c.close()
    conn.close()
    st.cache_data.clear()

def actualizar_servicio(id_serv, fecha, prov, contacto, tipo_serv, alcance, ubicacion, costo, obs):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE servicios 
        SET fecha=%s, proveedor=%s, contacto=%s, tipo_servicio=%s, alcance=%s, ubicacion=%s, costo_total=%s, observaciones=%s
        WHERE id=%s
    ''', (fecha, prov, contacto, tipo_serv, alcance, ubicacion, costo, obs, id_serv))
    conn.commit()
    c.close()
    conn.close()
    st.cache_data.clear()

def eliminar_servicio(id_serv):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM servicios WHERE id=%s', (id_serv,))
    conn.commit()
    c.close()
    conn.close()
    st.cache_data.clear()

@st.cache_data(ttl=300)
def cargar_servicios():
    conn = get_connection()
    df = pd.read_sql_query('SELECT * FROM servicios', conn)
    conn.close()
    return df

def formato_pesos(valor):
    return f"$ {valor:,.0f}".replace(",", ".")

init_db()

# --- ÍCONOS DINÁMICOS ---
iconos_equipos = {
    "Todos": "🌍", "Camión Grúa": "🚛", "Grúa Telescópica": "🏗️", 
    "Montacarga": "🚜", "Manlift": "🦒", "Brazos Articulados": "🦾", 
    "Tijeras": "✂️", "Andamios": "🪜", "Contenedor": "📦", 
    "Baños Portátiles": "🚻", "Otro": "🛠️"
}

# ==========================================
# 2. INTERFAZ DE USUARIO (UI)
# ==========================================
st.set_page_config(page_title="Directorio Polyuprotec", layout="wide", initial_sidebar_state="expanded")

st.sidebar.markdown("---")
st.sidebar.header("📌 Menú Principal")
menu_principal = st.sidebar.radio("Selecciona el Módulo:", ["🚜 Equipos y Fletes", "🛠️ Módulo de Servicios"])

# ==========================================
# MÓDULO 1: EQUIPOS Y FLETES
# ==========================================
if menu_principal == "🚜 Equipos y Fletes":
    st.title("🚜 Panel de Cotizaciones: Equipos y Fletes")
    df = cargar_datos()

    opciones_equipos = ["Camión Grúa", "Grúa Telescópica", "Montacarga", "Manlift", "Brazos Articulados", "Tijeras", "Andamios", "Contenedor", "Baños Portátiles", "Otro"]
    opciones_tarifas = ["Por Día", "Por Mes", "Global (Todo el proyecto)"]

    with st.expander("➕ Registrar Nueva Cotización de Equipo", expanded=False):
        with st.form("form_registro_equipo", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1: fecha_cot = st.date_input("Fecha", date.today())
            with col2: prov = st.text_input("Proveedor *")
            with col3: contacto = st.text_input("Contacto")
            
            col_eq1, col_eq2, col_eq3 = st.columns(3)
            with col_eq1: equipo = st.selectbox("Equipo", opciones_equipos)
            with col_eq2:
                esp_val = st.number_input("Capacidad / Altura (Ton o Mts)", min_value=0.0, step=1.0)
                esp_final = f"{esp_val} Unidades"
            with col_eq3: tarifa = st.selectbox("Tarifa", opciones_tarifas)

            col_l1, col_l2, col_l3, col_l4 = st.columns(4)
            with col_l1: orig = st.text_input("Origen *")
            with col_l2: dest = st.text_input("Destino *")
            with col_l3: alquiler = st.number_input("Alquiler", min_value=0, step=50000)
            with col_l4: flete = st.number_input("Flete", min_value=0, step=50000)
                
            archivo_pdf = st.file_uploader("PDF", type=["pdf"])
            obs = st.text_area("Observaciones")
            
            if st.form_submit_button("💾 Guardar Cotización", use_container_width=True):
                if prov and orig and dest:
                    nombre_pdf = ""
                    if archivo_pdf:
                        # Generar nombre único con la hora exacta
                        nombre_pdf = f"{int(datetime.now().timestamp())}_{prov}_{equipo}.pdf".replace(" ", "_")
                        # Subir archivo directamente a Supabase Storage
                        supabase_client.storage.from_("documentos").upload(
                            file=archivo_pdf.getvalue(),
                            path=nombre_pdf,
                            file_options={"content-type": "application/pdf"}
                        )
                    insertar_cotizacion(fecha_cot, prov, contacto, equipo, esp_final, tarifa, orig, dest, alquiler, flete, nombre_pdf, obs)
                    st.success("¡Agregado exitosamente a la nube!")
                    st.rerun()
                else:
                    st.error("Por favor completa los campos obligatorios (*).")

    if not df.empty:
        with st.expander("✏️ Editar o 🗑️ Eliminar un Registro de Equipo", expanded=False):
            opciones_registro = df['id'].astype(str) + " - " + df['proveedor'] + " (" + df['equipo'] + ")"
            seleccion = st.selectbox("Selecciona la cotización a modificar:", opciones_registro)
            if seleccion:
                id_sel = int(seleccion.split(" - ")[0])
                reg = df[df['id'] == id_sel].iloc[0]
                try: f_act = datetime.strptime(str(reg['fecha']), "%Y-%m-%d").date()
                except: f_act = date.today()

                tab1, tab2 = st.tabs(["✏️ Editar Cotización", "🗑️ Eliminar Cotización"])
                with tab1:
                    with st.form("form_edit_eq"):
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            nf = st.date_input("Fecha", f_act)
                            np = st.text_input("Proveedor", reg['proveedor'])
                            nc = st.text_input("Contacto", reg['contacto'] if pd.notna(reg['contacto']) else "")
                        with c2:
                            idx_eq = opciones_equipos.index(reg['equipo']) if reg['equipo'] in opciones_equipos else 0
                            neq = st.selectbox("Equipo", opciones_equipos, index=idx_eq)
                            nesp = st.text_input("Especificación", reg['especificacion'])
                            nori = st.text_input("Origen", reg['origen'])
                        with c3:
                            idx_tar = opciones_tarifas.index(reg['tipo_tarifa']) if reg['tipo_tarifa'] in opciones_tarifas else 0
                            ntar = st.selectbox("Tarifa", opciones_tarifas, index=idx_tar)
                            ndes = st.text_input("Destino", reg['destino'])
                            nalq = st.number_input("Alquiler", min_value=0, value=int(reg['costo_alquiler']), step=50000)
                            nfle = st.number_input("Flete", min_value=0, value=int(reg['costo_flete']), step=50000)
                        nobs = st.text_area("Observaciones", reg['observaciones'] if pd.notna(reg['observaciones']) else "")
                        
                        if st.form_submit_button("Actualizar Registro"):
                            actualizar_cotizacion(id_sel, nf, np, nc, neq, nesp, ntar, nori, ndes, nalq, nfle, nobs)
                            st.success("¡Registro actualizado con éxito!")
                            st.rerun()
                with tab2:
                    st.warning(f"⚠️ Vas a eliminar el registro de **{reg['proveedor']}**.")
                    if st.button("Sí, Eliminar Definitivamente", type="primary"):
                        eliminar_cotizacion(id_sel)
                        st.success("Registro eliminado.")
                        st.rerun()

    st.markdown("---")
    if
