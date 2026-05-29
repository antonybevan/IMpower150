import os
import json
import sqlite3
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import duckdb
from graph_builder import SemanticGraphBuilder
from qc_engine import QCEngine

def generate_vis_network_html(g):
    nodes = []
    edges = []
    
    # Scale node size by clinical hierarchy layer
    size_map = {
        "OBJECTIVE": 26,
        "CONCEPT": 30,
        "ENDPOINT": 22,
        "ESTIMAND": 20,
        "RULE": 18,
        "VARIABLE": 14,
        "RESULT": 16,
        "ARTIFACT": 12
    }
    
    for n, data in g.nodes(data=True):
        ntype = data.get("type", "UNKNOWN")
        label = data.get("label", n)
        color = data.get("color", "#76E4F7")
        
        # Build beautifully styled HTML tooltip for vis.js hover
        desc = f"<b>{label}</b> ({ntype})<br/><hr style='border: 0; border-top: 1px solid #181D2E; margin: 5px 0;'/>"
        if ntype == "OBJECTIVE":
            desc += f"<b>M11 Section:</b> {data.get('section','')}<br/><b>Text:</b> {data.get('text','')}"
        elif ntype == "CONCEPT":
            desc += f"<b>COSMoS ID:</b> {data.get('cosmos_id','')}<br/><b>Category:</b> {data.get('category','')}"
        elif ntype == "ENDPOINT":
            desc += f"<b>Concept:</b> {data.get('concept','')}<br/><b>Criteria:</b> {data.get('criteria','')}"
        elif ntype == "ESTIMAND":
            desc += f"<b>Population:</b> {data.get('population','')}<br/><b>Summary:</b> {data.get('summary','')}"
        elif ntype == "RULE":
            desc += f"<b>Logic Type:</b> {data.get('logic_type','')}<br/><b>Assessor:</b> {data.get('assessor','')}"
        elif ntype == "VARIABLE":
            desc += f"<b>Role:</b> {data.get('role','')}<br/><b>Datatype:</b> {data.get('datatype','')}"
        elif ntype == "RESULT":
            desc += f"<b>Label:</b> {label}"
        elif ntype == "ARTIFACT":
            desc += f"<b>Format:</b> {data.get('format','')}"
        
        node = {
            "id": n,
            "label": label,
            "title": desc,
            "color": {
                "background": color,
                "border": "#1A202C",
                "highlight": {
                    "background": "#FFFFFF",
                    "border": color
                },
                "hover": {
                    "background": color,
                    "border": "#FFFFFF"
                }
            },
            "size": size_map.get(ntype, 15),
            "shape": "dot",
            "font": {
                "color": "#EDF2F7",
                "size": 11,
                "face": "system-ui, -apple-system, sans-serif"
            },
            "shadow": {
                "enabled": True,
                "color": "rgba(0,0,0,0.4)",
                "size": 4,
                "x": 2,
                "y": 2
            }
        }
        nodes.append(node)
        
    for u, v, data in g.edges(data=True):
        rel = data.get("rel", "")
        edge = {
            "from": u,
            "to": v,
            "label": rel,
            "color": {
                "color": "#2D3748",
                "highlight": "#76E4F7",
                "hover": "#76E4F7",
                "inherit": False
            },
            "arrows": "to",
            "font": {
                "color": "#718096",
                "size": 9,
                "align": "middle",
                "face": "monospace"
            },
            "width": 1.5,
            "smooth": {
                "type": "cubicBezier",
                "roundness": 0.4
            }
        }
        edges.append(edge)
        
    nodes_json = json.dumps(nodes)
    edges_json = json.dumps(edges)
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
        <style type="text/css">
            html, body {{
                margin: 0;
                padding: 0;
                background-color: #060810;
                width: 100%;
                height: 100%;
                overflow: hidden;
            }}
            #mynetwork {{
                width: 100%;
                height: 100%;
                background-color: #0A0D18;
                border: 1px solid #181D2E;
                border-radius: 8px;
            }}
            div.vis-tooltip {{
                background-color: #0F1220 !important;
                border: 1px solid #181D2E !important;
                border-radius: 6px !important;
                color: #C8D4E4 !important;
                font-family: monospace !important;
                font-size: 11px !important;
                padding: 10px !important;
                max-width: 300px !important;
                white-space: normal !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.5) !important;
            }}
        </style>
    </head>
    <body>
    <div id="mynetwork"></div>
    <script type="text/javascript">
        var nodes = new vis.DataSet({nodes_json});
        var edges = new vis.DataSet({edges_json});

        var container = document.getElementById('mynetwork');
        var data = {{
            nodes: nodes,
            edges: edges
        }};
        var options = {{
            nodes: {{
                shape: 'dot',
                borderWidth: 2
            }},
            edges: {{
                arrows: {{
                    to: {{ enabled: true, scaleFactor: 0.8 }}
                }},
                smooth: {{
                    enabled: true,
                    type: 'cubicBezier',
                    roundness: 0.4
                }}
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 100,
                zoomView: true,
                dragView: true
            }},
            physics: {{
                enabled: true,
                solver: 'forceAtlas2Based',
                forceAtlas2Based: {{
                    gravitationalConstant: -55,
                    centralGravity: 0.015,
                    springConstant: 0.06,
                    springLength: 95,
                    damping: 0.45,
                    avoidOverlap: 0.8
                }},
                stabilization: {{
                    iterations: 200,
                    updateInterval: 50
                }}
            }}
        }};
        var network = new vis.Network(container, data, options);
    </script>
    </body>
    </html>
    """
    return html_code

# Set Page Config
st.set_page_config(
    page_title="IMpower150 Computable Submission Platform",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark theme custom css injection
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Syne:wght@400;600;700;800&display=swap');
    
    html, body, [class*="ViewCreator"] {
        font-family: 'JetBrains Mono', monospace;
        background-color: #060810;
        color: #C8D4E4;
    }
    .stApp {
        background-color: #060810;
    }
    h1, h2, h3 {
        font-family: 'Syne', sans-serif !important;
        font-weight: 700 !important;
        color: #EDF2F7 !important;
    }
    .card {
        background-color: #0A0D18;
        border: 1px solid #181D2E;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 15px;
    }
    .badge {
        background-color: rgba(183, 148, 244, 0.12);
        border: 1px solid rgba(183, 148, 244, 0.3);
        color: #B794F4;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: bold;
        letter-spacing: 0.08em;
    }
    .accent-header {
        border-left: 3px solid #76E4F7;
        padding-left: 12px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Design
st.sidebar.markdown("""
<div style="text-align: center; padding: 15px 0;">
    <h2 style="margin: 0; color: #B794F4;">IMpower150</h2>
    <p style="font-size: 10px; color: #6B7A94; letter-spacing: 0.15em;">SEMANTIC PLATFORM v3.0</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.divider()
view = st.sidebar.radio(
    "NAVIGATION",
    ["1. Protocol & Estimands", "2. Semantic DB Schema", "3. Active Lineage Graph", "4. Explainable QC Review", "5. Define.xml Submission", "6. Reproducibility Ledger"]
)

# Load Databases
db_path = 'metadata.db'
duck_path = 'analytics.duckdb'

# Check if data exists, if not initialize
if not os.path.exists(db_path):
    st.warning("Database not initialized. Please run automated tests to initialize.")
    st.stop()

# ─── VIEW 1: PROTOCOL & ESTIMANDS ───
if view == "1. Protocol & Estimands":
    st.markdown("<div class='accent-header'><h1>Trial Specifications & ICH E9(R1) Estimands</h1></div>", unsafe_allow_html=True)
    
    st.markdown("This section digests protocol attributes extracted from **`NEJM_IMpower150_protocol.pdf`** and **`SAP_IMpower150.pdf`** structured using the ICH M11 protocol specifications.")
    
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("M11 Trial Objectives")
        objs = pd.read_sql("SELECT obj_id, obj_type, obj_text, m11_section FROM protocol_objectives", conn)
        for _, row in objs.iterrows():
            st.markdown(f"""
            <div class='card'>
                <span class='badge' style='color:#76E4F7; border-color:#76E4F7;'>{row['obj_type'].upper()}</span>
                <span style='font-size:11px; color:#6B7A94; float:right;'>{row['m11_section']}</span>
                <h4 style='margin: 8px 0;'>{row['obj_id']}</h4>
                <p style='font-size:12px; color:#C8D4E4; line-height:1.55;'>{row['obj_text']}</p>
            </div>
            """, unsafe_allow_html=True)
            
    with col2:
        st.subheader("ICH E9(R1) Estimand Attributes")
        ests = pd.read_sql("SELECT estimand_id, name, target_population, ice_strategy, summary_measure FROM estimands", conn)
        for _, row in ests.iterrows():
            st.markdown(f"""
            <div class='card'>
                <span class='badge' style='color:#63B3ED; border-color:#63B3ED;'>ESTIMAND</span>
                <h4 style='margin: 8px 0;'>{row['estimand_id']} - {row['name']}</h4>
                <p style='font-size:12px; color:#C8D4E4; margin-bottom: 6px;'><b>Target Population:</b> {row['target_population']}</p>
                <p style='font-size:12px; color:#C8D4E4; margin-bottom: 6px;'><b>Intercurrent Events:</b> {row['ice_strategy']}</p>
                <p style='font-size:12px; color:#C8D4E4;'><b>Summary Measure:</b> {row['summary_measure']}</p>
            </div>
            """, unsafe_allow_html=True)
            
    conn.close()

# ─── VIEW 2: SEMANTIC DB SCHEMA ───
elif view == "2. Semantic DB Schema":
    st.markdown("<div class='accent-header'><h1>12-Table Semantic OLTP Schema (SQLite)</h1></div>", unsafe_allow_html=True)
    st.markdown("Unlike traditional variable-centric clinical platforms, the **v3 Semantic Schema** positions the clinical concept (`bc_id`) as the primary key of the architecture. Variables are realization artifacts.")
    
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    
    st.subheader("1. COSMoS Biomedical Concepts (Primary Clinical Root)")
    bcs = pd.read_sql("SELECT bc_id, bc_name, bc_category, cosmos_bc_id, sdtmig_class, bc_definition FROM biomedical_concepts", conn)
    st.dataframe(bcs, use_container_width=True)
    
    st.subheader("2. Endpoint Definitions (BC-to-Estimand Bridge)")
    eps = pd.read_sql("SELECT endpoint_id, bc_id, estimand_id, endpoint_type, analysis_concept, criteria_type FROM endpoint_definitions", conn)
    st.dataframe(eps, use_container_width=True)
    
    st.subheader("3. Declarative Derivation Rules (Compilable Rules)")
    rules = pd.read_sql("SELECT rule_id, endpoint_id, target_variable, logic_type, assessor, criteria_type, approval_status FROM derivation_rules", conn)
    st.dataframe(rules, use_container_width=True)
    
    st.subheader("4. Realized Variables (CDISC Implementation fields)")
    vars_df = pd.read_sql("SELECT variable, dataset, role, datatype, bc_id, origin FROM variables", conn)
    st.dataframe(vars_df, use_container_width=True)
    
    st.subheader("5. Analysis Results Metadata (ARM Core - Phase 2)")
    arm_df = pd.read_sql("SELECT analysis_id, endpoint_id, dataset, paramcd, stat_method, stat_test, tfl_reference, arm_display_label FROM analysis_results", conn)
    st.dataframe(arm_df, use_container_width=True)
    
    st.subheader("6. Variable Level Metadata Where Clauses")
    wc_df = pd.read_sql("SELECT where_clause_id, dataset, variable, filter_operator, filter_value FROM where_clauses", conn)
    st.dataframe(wc_df, use_container_width=True)
    
    conn.close()

# ─── VIEW 3: ACTIVE LINEAGE GRAPH ───
elif view == "3. Active Lineage Graph":
    st.markdown("<div class='accent-header'><h1>8-Layer Semantic Lineage Knowledge Graph</h1></div>", unsafe_allow_html=True)
    st.markdown("This knowledge graph spans from M11 Protocol Objectives down to CDISC XPT/Dataset-JSON submission artifacts. Hover over nodes to explore deep metadata definitions and relationships.")
    
    builder = SemanticGraphBuilder(db_path)
    g = builder.build_graph()
    
    # Render Interactive Vis.js Network at full width
    st.subheader("🧬 Interactive Graph Visualizer")
    html_network = generate_vis_network_html(g)
    components.html(html_network, height=520, scrolling=False)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Lineage Traversals")
        q_type = st.selectbox("QUERY TYPE", ["downstream_chain", "impact_analysis", "gap_audit"])
        
        if q_type == "downstream_chain":
            bc_id = st.selectbox("Select Biomedical Concept", ["PFS", "OS", "iPFS"])
            if st.button("RUN Downstream Lineage Scan"):
                visited = builder.concept_to_artifacts(bc_id)
                st.success(f"Downstream clinical chain for '{bc_id}' returned {len(visited)} nodes:")
                for n in visited:
                    st.markdown(f"**[{n['type']}]** {n['label']} (Color: `{n['color']}`)")
                    
        elif q_type == "impact_analysis":
            rule_id = st.selectbox("Select Derivation Rule to modify", ["RULE_PFS_AVAL", "RULE_PFS_CNSR", "RULE_IPFS_AVAL"])
            if st.button("RUN Impact Risk Analysis"):
                impact = builder.impact_analysis(rule_id)
                st.warning(f"Modifying '{rule_id}' has down-stream impact on {len(impact)} entities:")
                for n in impact:
                    st.markdown(f"**[{n['type']}]** {n['label']}")
                    
        elif q_type == "gap_audit":
            if st.button("RUN Semantic Gap Audit"):
                gaps = builder.semantic_gap_audit()
                if gaps:
                    st.error(f"Audit identified {len(gaps)} clinical metadata gaps:")
                    for gap in gaps:
                        st.markdown(f"**{gap['type']}:** {gap['entity']} — *{gap['detail']}*")
                else:
                    st.success("No clinical gaps found. Metadata repository is 100% semantically anchored!")

    with col2:
        st.subheader("Graph Statistics")
        st.markdown(f"• **Nodes in active graph:** {g.number_of_nodes()}")
        st.markdown(f"• **Edges (Lineage connections):** {g.number_of_edges()}")
        st.markdown("#### Hierarchical Knowledge Representation Mapping")
        
        # Display list of node types
        node_types = {}
        for n, data in g.nodes(data=True):
            ntype = data.get("type", "UNKNOWN")
            node_types[ntype] = node_types.get(ntype, 0) + 1
            
        st.write(pd.DataFrame(list(node_types.items()), columns=["Layer Type", "Count"]))

# ─── VIEW 4: EXPLAINABLE QC REVIEW ───
elif view == "4. Explainable QC Review":
    st.markdown("<div class='accent-header'><h1>Level 3 explainable QC Conformance Review</h1></div>", unsafe_allow_html=True)
    st.markdown("Ingests validations from CORE and RECIST oncology rules, then traverses the graph to compile explainable narratives.")
    
    if not os.path.exists(duck_path):
        st.warning("No QC findings recorded. Please run automated verification tests first to generate findings.")
    else:
        conn = duckdb.connect(duck_path)
        findings = pd.read_sql("SELECT usubjid, rule_source, severity, target_variable, clinical_narrative FROM qc_findings", conn)
        
        for _, row in findings.iterrows():
            severity_color = "#FC8181" if row['severity'] == "critical" else "#ECC94B"
            st.markdown(f"""
            <div class='card' style='border-left: 4px solid {severity_color};'>
                <span class='badge' style='color:{severity_color}; border-color:{severity_color}; background-color:rgba(0,0,0,0.1);'>{row['severity'].upper()}</span>
                <span style='font-size:11px; color:#6B7A94; float:right;'>Source: {row['rule_source']}</span>
                <h4 style='margin: 8px 0;'>Subject ID: {row['usubjid']} | Target: {row['target_variable']}</h4>
                <pre style='background-color:#0F1220; padding:12px; border-radius:5px; font-size:11px; white-space:pre-wrap; border:1px solid #181D2E;'>{row['clinical_narrative']}</pre>
            </div>
            """, unsafe_allow_html=True)
            
        conn.close()

# ─── VIEW 5: DEFINE.XML SUBMISSION ───
elif view == "5. Define.xml Submission":
    st.markdown("<div class='accent-header'><h1>CDISC Define.xml v2.1 & JSON-LD Exporters</h1></div>", unsafe_allow_html=True)
    st.markdown("Compiled single-source XML/JSON-LD exports synchronized with active concepts.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Define.xml v2.1 Spec")
        xml_path = "outputs/submission/define.xml"
        if os.path.exists(xml_path):
            with open(xml_path, 'r') as f:
                code = f.read()
            st.text_area("XML Code", code, height=400)
        else:
            st.warning("Define.xml file not compiled. Run automated tests first.")
            
    with col2:
        st.subheader("JSON-LD SDRG Metadata Graph")
        sdrg_path = "outputs/submission/sdrg.jsonld"
        if os.path.exists(sdrg_path):
            with open(sdrg_path, 'r') as f:
                code = f.read()
            st.text_area("JSON-LD Code", code, height=400)
        else:
            st.warning("SDRG JSON-LD file not compiled. Run automated tests first.")

# ─── VIEW 6: REPRODUCIBILITY LEDGER ───
elif view == "6. Reproducibility Ledger":
    st.markdown("<div class='accent-header'><h1>Deterministic Snapshot & Reproducibility Ledger</h1></div>", unsafe_allow_html=True)
    st.markdown("Achieving clinical submission excellence requires rigorous, absolute auditability. This ledger captures the exact state of all oncology rules, database schemas, and environment properties for each pipeline run.")
    
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    
    try:
        snapshots = pd.read_sql("SELECT snapshot_id, run_id, sdtmig_version, adamig_version, python_version, sas_version, rule_hash_manifest, metadata_db_hash, environment_hash, created_ts FROM execution_snapshots ORDER BY created_ts DESC", conn)
        
        if snapshots.empty:
            st.info("No reproducibility snapshots recorded yet. Run the E2E verification test pipeline to capture a snapshot.")
        else:
            for _, row in snapshots.iterrows():
                st.markdown(f"""
                <div class='card' style='border-left: 4px solid #B794F4;'>
                    <span class='badge' style='color:#B794F4; border-color:#B794F4; background-color:rgba(0,0,0,0.1);'>SNAPSHOT</span>
                    <span style='font-size:11px; color:#6B7A94; float:right;'>Recorded: {row['created_ts']}</span>
                    <h3 style='margin: 8px 0; color:#EDF2F7;'>Run ID: {row['run_id']}</h3>
                    <p style='font-size:12px; color:#6B7A94; margin-bottom: 12px;'><b>Snapshot Unique ID:</b> <code style='color:#F6AD55; background-color:#0F1220; padding:2px 6px; border-radius:4px;'>{row['snapshot_id']}</code></p>
                    
                    <div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 15px;'>
                        <div style='background-color:#0F1220; padding:10px; border-radius:6px; border:1px solid #181D2E; text-align:center;'>
                            <span style='font-size:9px; color:#6B7A94; display:block; text-transform:uppercase;'>Python Version</span>
                            <span style='font-size:13px; font-weight:bold; color:#76E4F7;'>{row['python_version']}</span>
                        </div>
                        <div style='background-color:#0F1220; padding:10px; border-radius:6px; border:1px solid #181D2E; text-align:center;'>
                            <span style='font-size:9px; color:#6B7A94; display:block; text-transform:uppercase;'>SAS Runtime</span>
                            <span style='font-size:13px; font-weight:bold; color:#76E4F7;'>{row['sas_version']}</span>
                        </div>
                        <div style='background-color:#0F1220; padding:10px; border-radius:6px; border:1px solid #181D2E; text-align:center;'>
                            <span style='font-size:9px; color:#6B7A94; display:block; text-transform:uppercase;'>CDISC SDTMIG</span>
                            <span style='font-size:13px; font-weight:bold; color:#76E4F7;'>v{row['sdtmig_version']}</span>
                        </div>
                        <div style='background-color:#0F1220; padding:10px; border-radius:6px; border:1px solid #181D2E; text-align:center;'>
                            <span style='font-size:9px; color:#6B7A94; display:block; text-transform:uppercase;'>CDISC ADAMIG</span>
                            <span style='font-size:13px; font-weight:bold; color:#76E4F7;'>v{row['adamig_version']}</span>
                        </div>
                    </div>
                    
                    <p style='font-size:11px; color:#C8D4E4; margin: 4px 0;'><b>Metadata DB Hash:</b> <code style='font-size:10px; color:#68D391;'>{row['metadata_db_hash']}</code></p>
                    <p style='font-size:11px; color:#C8D4E4; margin: 4px 0;'><b>Composite Environment Hash:</b> <code style='font-size:10px; color:#68D391;'>{row['environment_hash']}</code></p>
                </div>
                """, unsafe_allow_html=True)
                
                # Parse and display active rules manifest for this snapshot
                try:
                    manifest_data = json.loads(row['rule_hash_manifest'])
                    if manifest_data:
                        with st.expander(f"🔍 Explore Compiled Oncology Rules Manifest ({len(manifest_data)} Active Rules)", expanded=False):
                            manifest_df = pd.DataFrame(manifest_data)
                            # Rename columns for pristine aesthetics
                            manifest_df.columns = ["Rule ID", "Target Variable", "Logic Type", "Rule Hash (SHA256)"]
                            st.dataframe(manifest_df, use_container_width=True)
                except Exception as e:
                    st.error(f"Error parsing rule hash manifest: {e}")
                    
            # Display SAS execution log findings if they exist
            st.divider()
            st.subheader("🤖 SAS Execution Log Parser (DuckDB analytical store)")
            st.markdown("Automated parsing of all compiled SAS programs for clinical execution errors, warnings, and empty data sets.")
            if os.path.exists(duck_path):
                try:
                    duck_conn = duckdb.connect(duck_path)
                    log_df = pd.read_sql("SELECT program_name, line_num, log_type, message FROM execution_log ORDER BY program_name, line_num", duck_conn)
                    if log_df.empty:
                        st.success("No execution errors, warnings, or anomalies found in compiled SAS logs &bull; 100% CLEAN")
                    else:
                        st.dataframe(log_df, use_container_width=True)
                    duck_conn.close()
                except Exception as dex:
                    st.warning(f"No execution log history available yet: {dex}")
                    
    except Exception as ex:
        st.error(f"Failed to query reproducibility ledger: {ex}")
    finally:
        conn.close()

