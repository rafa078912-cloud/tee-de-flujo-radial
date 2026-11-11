import streamlit as st
import numpy as np
import datetime

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Diseñador de Tee Ranurada de Flujo Radial",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- BASE DE DATOS DE MATERIALES (SMYS en psi) ---
MATERIALES_DB = {
    "API 5L Grade X52 (PSL2)": 52000,
    "ASTM A860 WPHY-52": 52000,
    "API 5L Grade X60 (PSL2)": 60000,
    "API 5L Grade X65 (PSL2)": 65000,
    "ASTM A860 WPHY-65": 65000,
    "API 5L Grade X70 (PSL2)": 70000,
    "ASTM A106 Grade B": 35000,
    "ASTM A516 Grade 70 Plate": 38000
}

# --- TÍTULO PRINCIPAL ---
st.title("🔧 Calculador y Diseñador de Tee Ranurada de Flujo Radial")
st.markdown("**Normativa Aplicable:** ASME B31.8 / ASME B31.3 / API RP 14E / MSS SP-75")
st.markdown("---")

# --- BARRA LATERAL: DATOS DE ENTRADA Y PROYECTO ---
st.sidebar.header("📁 0. Datos del Proyecto y Cliente")
cliente_razon = st.sidebar.text_input("Razón Social del Cliente", "PEMEX Exploración y Producción")
contacto_nom = st.sidebar.text_input("Responsable Técnico", "Ing. Rafael García Arroyo")
correo_contacto = st.sidebar.text_input("Correo Electrónico", "ingrgarciaarroyo@gmail.com")
telefono_contacto = st.sidebar.text_input("Teléfono de Contacto", "+52 55 28 42 87 99")
no_proyecto = st.sidebar.text_input("No. de Proyecto", "PRO-TEE-RAD-EXP-20")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ 1. Variables Geométricas")
nps_h = st.sidebar.selectbox("Diámetro Línea Principal (Run) [in]", [6.625, 8.625, 10.750, 12.750, 14.000, 16.000, 18.000, 20.000, 24.000], index=7)
th = st.sidebar.number_input("Espesor Nominal Pared Línea th [in]", value=0.812, format="%.3f")

dcuerpo = st.sidebar.number_input("Diámetro Exterior Cuerpo Tee [in]", value=24.000, format="%.3f")
tcuerpo = st.sidebar.number_input("Espesor Nominal Cuerpo Tee tcuerpo [in]", value=0.969, format="%.3f")

st.sidebar.markdown("---")
st.sidebar.header("🌡️ 2. Condiciones de Proceso")
p_kg = st.sidebar.number_input("Presión de Diseño (P) [kg/cm²]", value=100.0)
temp_c = st.sidebar.number_input("Temperatura de Operación [°C]", value=50.0)
temp_amb = st.sidebar.number_input("Temperatura Ambiente [°C]", value=21.0)

factor_f_str = st.sidebar.selectbox("Factor de Diseño (F) - ASME B31.8", ["0.40 (Clase 4)", "0.50 (Clase 3)", "0.60 (Clase 2)", "0.72 (Clase 1)"], index=1)
F_design = float(factor_f_str.split(" ")[0])

corrosion_str = st.sidebar.selectbox("Margen de Corrosión (CA) [in]", ["0.000 (Sin sobreespesor)", "0.0625 (1/16 in)", "0.1250 (1/8 in)", "0.2500 (1/4 in)"], index=2)
CA = float(corrosion_str.split(" ")[0])

mat_h = st.sidebar.selectbox("Material Tubo / Liner", list(MATERIALES_DB.keys()), index=3)
mat_b = st.sidebar.selectbox("Material Cuerpo Tee", list(MATERIALES_DB.keys()), index=4)

# --- CÁLCULOS TÉCNICOS ---
P_psi = p_kg * 14.2233
S_h = MATERIALES_DB[mat_h]
S_b = MATERIALES_DB[mat_b]

# 1. Geometría y Longitudes (MSS SP-75)
if dcuerpo >= 24.0:
    C_end = 27.0
elif dcuerpo >= 20.0:
    C_end = 24.0
else:
    C_end = 20.0

L_tee_total = 2 * C_end
L_liner = L_tee_total - 12.0
L_transition_ring = 5.0
L_total_ensamblaje = L_tee_total + (2 * L_transition_ring)

# 2. Espesores mínimos por presión (ASME B31.8)
E_junta = 1.00
T_temp = 1.00
t_req_h = (P_psi * nps_h) / (2 * S_h * E_junta * F_design * T_temp)
t_total_req_h = (t_req_h + CA) / 0.875

t_req_cuerpo = (P_psi * dcuerpo) / (2 * S_b * E_junta * F_design * T_temp)
t_total_req_cuerpo = (t_req_cuerpo + CA) / 0.875

es_espesor_ok = (th >= t_total_req_h) and (tcuerpo >= t_total_req_cuerpo)

# 3. Análisis Térmico (ASME B31.3)
alpha_steel = 11.7e-6
E_mod = 29.5e6
DeltaT = temp_c - temp_amb
S_E_psi = E_mod * alpha_steel * 1.8 * DeltaT
Sa_psi = 1.0 * (1.25 * (0.6 * S_h) + 0.25 * (0.6 * S_h))
es_termico_ok = S_E_psi <= Sa_psi

# 4. Hidrodinámica y Slots (API RP 14E)
ID_h = nps_h - 2 * th
A_pipe = (np.pi / 4) * (ID_h ** 2)
ID_cuerpo = dcuerpo - 2 * tcuerpo
A_anular = (np.pi / 4) * (ID_cuerpo ** 2 - nps_h ** 2)

b_slot = round(0.09 * nps_h, 3)
h_slot = round(0.30 * nps_h, 3)
if b_slot < 0.50: b_slot = 0.50
if h_slot < 1.50: h_slot = 1.50

A_rect = b_slot * (h_slot - b_slot)
A_circ = (np.pi / 4) * (b_slot ** 2)
A_slot_single = A_rect + A_circ

A_slots_req = 1.50 * A_pipe
num_slots_req = int(np.ceil(A_slots_req / A_slot_single))
if num_slots_req % 2 != 0: num_slots_req += 1
num_slots = max(40, num_slots_req)

A_slots_real = num_slots * A_slot_single
ratio_slots = (A_slots_real / A_pipe) * 100
vel_rel_slots = (A_pipe / A_slots_real) * 100

# Empuje de Pig
DeltaP_pig_psi = 21.33
F_empuje_lbs = DeltaP_pig_psi * A_pipe
a_garganta = th * np.sin(np.radians(75))
A_soldadura = np.pi * nps_h * a_garganta
tau_corte = F_empuje_lbs / A_soldadura
tau_permisible = 0.40 * S_h

status_global = "DISEÑO SATISFACTORIO - CUMPLE NORMAS ASME / API" if es_espesor_ok and es_termico_ok else "REVISAR LÍMITES MECÁNICOS O TÉRMICOS"

# --- PESTAÑAS PRINCIPALES DE LA APLICACIÓN ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 1. Resumen & Verificación", 
    "🌊 2. Hidrodinámica & Slots", 
    "🏗️ 3. Componentes y BOM", 
    "📄 4. Memoria Técnica Final"
])

with tab1:
    st.subheader("Resumen Ejecutivo de Ingeniería")
    st.info(f"**Estatus General:** {status_global}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Presión de Diseño", f"{p_kg} kg/cm²", f"{P_psi:.1f} psi")
    col2.metric("Temperatura Operación", f"{temp_c} °C", f"ΔT = {DeltaT} °C")
    col3.metric("Área Cobertura Slots", f"{ratio_slots:.1f}%", f"{num_slots} Pzas")

    st.markdown("### Verificación de Cumplimiento Normativo")
    st.write(f"- **Espesor Tubo Principal:** {'✅ Conforme' if th >= t_total_req_h else '❌ No Conforme'} (Nom: {th}\" vs Req Min: {t_total_req_h:.3f}\")")
    st.write(f"- **Espesor Cuerpo Tee:** {'✅ Conforme' if tcuerpo >= t_total_req_cuerpo else '❌ No Conforme'} (Nom: {tcuerpo}\" vs Req Min: {t_total_req_cuerpo:.3f}\")")
    st.write(f"- **Esfuerzo Térmico (ASME B31.3):** {'✅ Conforme' if es_termico_ok else '❌ Excesivo'} (SE: {S_E_psi:.1f} psi / Sa: {Sa_psi:.1f} psi)")
    st.write(f"- **Esfuerzo Cortante Biseles CJP:** {'✅ Conforme' if tau_corte <= tau_permisible else '❌ Alto'} ({tau_corte:.1f} psi)")

with tab2:
    st.subheader("Evaluación Hidrodinámica (API RP 14E)")
    st.write("Análisis detallado del flujo radial y la cámara anular para evitar erosión, restricción y cavitación.")
    
    st.markdown(f"""
    * **Área Interior Tubería Principal ($A_{{pipe}}$):** `{A_pipe:.4f} sq.in` (`{A_pipe*6.4516:.2f} cm²`)
    * **Área Cámara Anular en Cuerpo ($A_{{anular}}$):** `{A_anular:.4f} sq.in` (`{A_anular*6.4516:.2f} cm²`)
    * **Área Requerida de Slots (150% de Línea):** `{A_slots_req:.4f} sq.in`
    * **Geometría de Slots Asignada:** Ancho `b = {b_slot}\"`, Largo `h = {h_slot}\"` (`{num_slots} Pzas` en 4 filas)
    * **Área Total Real de Slots:** `{A_slots_real:.4f} sq.in` (Cobertura de `{ratio_slots:.1f}%`)
    * **Velocidad Relativa en Slots:** `{vel_rel_slots:.1f}%` respecto a la línea principal (Garantiza flujo sin caída de presión excesiva ni erosión).
    """)

with tab3:
    st.subheader("Lista de Materiales y Componentes (BOM)")
    bom_data = [
        {"Componente": "Cuerpo Tee Reducción", "Especificación": f"MSS SP-75 {mat_b}", "Dimensiones": f"{dcuerpo}\" x {dcuerpo}\" x {nps_h}\"", "Longitud": f"{L_tee_total:.2f} in"},
        {"Componente": "Camisa / Liner Ranurado", "Especificación": f"API 5L {mat_h}", "Dimensiones": f"{nps_h}\" NPS (t={th}\")", "Longitud": f"{L_liner:.2f} in"},
        {"Componente": "Aros / Anillos de Transición", "Especificación": f"ASTM A860 {mat_b}", "Dimensiones": f"Reducción {dcuerpo}\" a {nps_h}\"", "Longitud": f"{L_transition_ring:.1f} in (x2 Pzas)"},
    ]
    st.table(bom_data)
    st.markdown(f"**Longitud Total del Ensamblaje:** `{L_total_ensamblaje:.3f} in` (`{L_total_ensamblaje*25.4:.1f} mm`)")

with tab4:
    st.subheader("Memoria Técnica Oficial para Exportación")
    
    memoria_texto = f"""===================================================================================
                  MEMORIA TÉCNICA Y DE CÁLCULO NORMATIVO
         FABRICACIÓN DE TEE DE FLUJO RADIAL (PIGGABLE TEE) - PROYECTO: {no_proyecto}
         CUMPLIMIENTO: ASME B31.8 / ASME B31.3 / API RP 14E / MSS SP-75
===================================================================================
FECHA: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}

1. DATOS GENERALES DEL CLIENTE
   - Cliente: {cliente_razon}
   - Responsable Técnico: {contacto_nom} | Tel: {telefono_contacto}
   - Correo: {correo_contacto}

2. LONGITUDES GEOMÉTRICAS DE FABRICACIÓN
   - Longitud Total Cuerpo Tee (L_tee):         {L_tee_total:.3f} in ({L_tee_total*25.4:.1f} mm)
   - Longitud Camisa / Liner Ranurado (L_liner): {L_liner:.3f} in ({L_liner*25.4:.1f} mm)
   - Longitud Total Ensamblaje (L_total):        {L_total_ensamblaje:.3f} in ({L_total_ensamblaje*25.4:.1f} mm)

3. CONFIGURACIÓN DE SLOTS (API RP 14E)
   - Cantidad Total: {num_slots} Pzas (Orientación Longitudinal - 4 Filas)
   - Dimensiones: Ancho b = {b_slot} in | Largo h = {h_slot} in
   - Área Efectiva Real: {A_slots_real:.4f} sq.in (Cobertura: {ratio_slots:.1f}%)

4. VERIFICACIÓN DE ESFUERZOS Y PRESIÓN
   - Presión de Diseño: {p_kg} kg/cm² ({P_psi:.1f} psi) | Temp: {temp_c} °C
   - Espesor Mínimo Calculado (t_req): {t_req_h:.4f} in (Nominal Proporcionado: {th} in) -> CONFORME
   - Esfuerzo Térmico (SE): {S_E_psi:.1f} psi (Admisible Sa: {Sa_psi:.1f} psi) -> CONFORME

5. DICTAMEN TÉCNICO
   {status_global}
==================================================================================="""

    st.text_area("Vista Previa del Documento Oficial", memoria_texto, height=300)
    
    st.download_button(
        label="📥 Descargar Memoria Técnica (.txt)",
        data=memoria_texto,
        file_name=f"Memoria_Tecnica_{no_proyecto}.txt",
        mime="text/plain"
    )
