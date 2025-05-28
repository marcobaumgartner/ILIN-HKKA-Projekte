import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import io

st.set_page_config(page_title="Projekt-Netzwerk Visualisierung", layout="wide")
st.title("🔗 Projekt-Hashtag-Netzwerk")
st.markdown("""
Lade eine Excel- oder CSV-Datei hoch, um ein Netzwerk von Projekten zu visualisieren.
- Knoten = Projekte
- Kanten = gemeinsame Hashtags (beschriftet)
- Farbige Cluster zeigen thematische Gruppen
""")

# Datei-Upload
datei = st.file_uploader("📁 Datei hochladen (Excel oder CSV)", type=["xlsx", "csv"])

if datei:
    if datei.name.endswith(".csv"):
        df = pd.read_csv(datei)
    else:
        df = pd.read_excel(datei)

    st.success("Datei erfolgreich geladen!")

    projekte = {}
    for idx, row in df.iterrows():
        projekt = row[0]
        hashtags = [str(tag).strip() for tag in row[1:] if pd.notna(tag)]
        projekte[projekt] = hashtags

    # Netzwerk aufbauen
    G = nx.Graph()
    hashtag_to_projects = {}
    for projekt, tags in projekte.items():
        for tag in tags:
            hashtag_to_projects.setdefault(tag, []).append(projekt)

    for tag, proj_list in hashtag_to_projects.items():
        for i in range(len(proj_list)):
            for j in range(i + 1, len(proj_list)):
                u, v = proj_list[i], proj_list[j]
                if G.has_edge(u, v):
                    G[u][v]['label'].add(tag)
                else:
                    G.add_edge(u, v, label={tag})

    # Community Clustering
    from networkx.algorithms import community
    communities = community.greedy_modularity_communities(G)
    cluster_map = {}
    for i, cluster in enumerate(communities):
        for node in cluster:
            cluster_map[node] = i

    pos = nx.spring_layout(G, seed=42)

    edge_traces = []
    edge_labels = []
    for u, v, data in G.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_traces.append(go.Scatter(x=[x0, x1], y=[y0, y1], mode='lines', line=dict(width=1, color='gray'), hoverinfo='none'))
        xm, ym = (x0 + x1)/2, (y0 + y1)/2
        edge_labels.append(go.Scatter(x=[xm], y=[ym], mode='text', text=[", ".join(data['label'])], hoverinfo='none', textfont=dict(size=8)))

    node_x = [pos[n][0] for n in G.nodes]
    node_y = [pos[n][1] for n in G.nodes]
    node_text = ["<br>".join(projekte[n]) for n in G.nodes]
    node_color = [cluster_map[n] for n in G.nodes]

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        marker=dict(size=20, color=node_color, colorscale='Viridis', showscale=True),
        text=list(G.nodes),
        hovertext=node_text,
        hoverinfo='text',
        textposition='top center'
    )

    fig = go.Figure()
    for edge in edge_traces:
        fig.add_trace(edge)
    for label in edge_labels:
        fig.add_trace(label)
    fig.add_trace(node_trace)
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=700, showlegend=False)

    st.plotly_chart(fig, use_container_width=True)

    # Exportoptionen
    html_buffer = io.StringIO()
    fig.write_html(html_buffer)
    st.download_button("💾 HTML herunterladen", html_buffer.getvalue(), file_name="netzwerk.html")

    csv_export = df.to_csv(index=False)
    st.download_button("📄 Original CSV herunterladen", csv_export, file_name="daten.csv")

