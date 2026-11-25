import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from modules.cpu_scheduling import fcfs, sjf, round_robin, srtf, preemptive_priority
from modules.disk_scheduling import fcfs as disk_fcfs, sstf, scan, c_scan
from modules.deadlock import is_safe_state

st.set_page_config(page_title="OS Resource Management Dashboard", page_icon="⚙️", layout="wide")

st.markdown("""
<style>
/* Clean pastel theme with high-contrast readable text */
:root { color-scheme: light; }
.stApp, [data-testid="stAppViewContainer"] {
  background: linear-gradient(135deg, #f7f8fc 0%, #f1f5fb 55%, #f8f4fb 100%) !important;
  color: #263449 !important;
}
.stApp p, .stApp li, .stApp label, .stApp .stMarkdown,
.stApp [data-testid="stWidgetLabel"], .stApp small,
.stApp [data-testid="stCaptionContainer"] {
  color: #34445b !important;
}
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 {
  color: #263b57 !important;
}
.stApp [data-testid="stCaptionContainer"] { color: #596b83 !important; }
section[data-testid="stSidebar"] {
  background: #e9eef8 !important;
  border-right: 1px solid #d1daea !important;
}
section[data-testid="stSidebar"] * { color: #263b57 !important; }
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #435671 !important; }
section[data-testid="stSidebar"] input { color: #263449 !important; background: #ffffff !important; }
/* Metrics: soft pastel blue with dark readable values */
div[data-testid="stMetric"] {
  background: #e7efff !important;
  padding: 17px !important;
  border: 1px solid #c8d8f6 !important;
  border-radius: 14px !important;
}
div[data-testid="stMetric"] label,
div[data-testid="stMetric"] [data-testid="stMetricLabel"] { color: #405775 !important; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #244b86 !important; }
/* Inputs and dropdowns */
.stApp input, .stApp textarea,
.stApp [data-baseweb="select"] > div,
.stApp [data-testid="stNumberInput"] button {
  background-color: #ffffff !important;
  color: #263449 !important;
  border-color: #c7d2e3 !important;
}
.stApp input::placeholder, .stApp textarea::placeholder { color: #738198 !important; }
.stApp [data-baseweb="select"] * { color: #263449 !important; }
ul[role="listbox"], [data-baseweb="popover"] { background: #ffffff !important; }
[role="option"] { color: #263449 !important; }
/* Buttons: muted blue, not neon */
div.stButton > button, .stDownloadButton button {
  border-radius: 9px !important; font-weight: 600 !important;
  color: #ffffff !important; border: 1px solid #6f91c7 !important;
  background: #6f91c7 !important;
}
div.stButton > button:hover, .stDownloadButton button:hover {
  background: #587db7 !important; border-color: #587db7 !important;
}
[data-testid="stAlert"] { border-radius: 10px !important; }
[data-testid="stDataFrame"], [data-testid="stTable"] { color: #263449 !important; }
[data-testid="stDataFrame"] * { color: #263449; }
.stApp [data-testid="stPlotlyChart"] { border-radius: 10px; }
/* Keep links readable */
.stApp a { color: #416da8 !important; }
</style>
""", unsafe_allow_html=True)

st.title("⚙️ OS Resource Management")
st.caption("Interactive simulator dashboard · CPU scheduling · Memory allocation · Deadlock · Disk scheduling")

page = st.sidebar.radio("NAVIGATION", ["Overview", "CPU Scheduling", "Memory Management", "Deadlock & Banker’s", "Disk Scheduling"])
st.sidebar.markdown("---")
st.sidebar.caption("Python · Streamlit · OS Algorithms")

def sample_processes():
    return [
        {"pid":"P1","arrival":0,"burst":5,"priority":3},
        {"pid":"P2","arrival":1,"burst":4,"priority":1},
        {"pid":"P3","arrival":2,"burst":2,"priority":4},
        {"pid":"P4","arrival":4,"burst":6,"priority":2},
        {"pid":"P5","arrival":6,"burst":3,"priority":5},
    ]

def memory_allocate(blocks, processes, strategy):
    remaining = blocks.copy()
    rows=[]
    for i,size in enumerate(processes):
        candidates=[j for j,b in enumerate(remaining) if b>=size]
        chosen=None
        if candidates:
            if strategy=="First Fit": chosen=candidates[0]
            elif strategy=="Best Fit": chosen=min(candidates,key=lambda j:remaining[j])
            else: chosen=max(candidates,key=lambda j:remaining[j])
            remaining[chosen]-=size
        rows.append({"Process":f"P{i+1}","Size":size,"Block":f"B{chosen+1}" if chosen is not None else "—","Status":"Allocated" if chosen is not None else "Not allocated"})
    return pd.DataFrame(rows), remaining

if page == "Overview":
    st.subheader("System overview")
    st.write("Explore classic operating-system resource management algorithms with editable inputs and clear result tables.")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("CPU algorithms", "5")
    c2.metric("Memory strategies", "3")
    c3.metric("Deadlock tools", "2")
    c4.metric("Disk algorithms", "4")
    st.markdown("### Modules")
    cards=st.columns(4)
    for col, title, desc in zip(cards, ["🧠 CPU Scheduling","🧩 Memory Management","🔐 Deadlock","💽 Disk Scheduling"], ["FCFS, SJF, RR, SRTF, Priority","First Fit, Best Fit, Worst Fit","Banker’s safe-state analysis","FCFS, SSTF, SCAN, C-SCAN"]):
        with col:
            st.markdown(f"**{title}**")
            st.caption(desc)
    st.info("Choose a module from the left sidebar to run a simulation. The values shown are sample inputs and can be changed.")
    st.markdown("### Sample project metrics")
    st.dataframe(pd.DataFrame([
        {"Module":"CPU","Purpose":"Calculate waiting and turnaround time"},
        {"Module":"Memory","Purpose":"Allocate processes to available blocks"},
        {"Module":"Deadlock","Purpose":"Check safe state and safe sequence"},
        {"Module":"Disk","Purpose":"Calculate disk-head movement"},
    ]), use_container_width=True, hide_index=True)

elif page == "CPU Scheduling":
    st.subheader("🧠 CPU Scheduling Simulator")
    algo=st.selectbox("Algorithm",["FCFS","SJF (Non-preemptive)","Round Robin","SRTF","Preemptive Priority"])
    default=pd.DataFrame(sample_processes())
    edited=st.data_editor(default, num_rows="dynamic", use_container_width=True, key="cpu_editor")
    quantum=st.number_input("Round Robin time quantum", min_value=1, value=2) if algo=="Round Robin" else 2
    if st.button("Run CPU simulation", type="primary"):
        try:
            procs=[]
            for _,r in edited.iterrows():
                procs.append({"pid":str(r["pid"]),"arrival":int(r["arrival"]),"burst":int(r["burst"]),"priority":int(r["priority"])})
            if not procs or any(p["arrival"]<0 or p["burst"]<=0 for p in procs): raise ValueError("Arrival must be ≥ 0 and burst must be > 0.")
            funcs={"FCFS":fcfs,"SJF (Non-preemptive)":sjf,"Round Robin":lambda p:round_robin(p,quantum),"SRTF":srtf,"Preemptive Priority":preemptive_priority}
            results,gantt=funcs[algo](procs)
            df=pd.DataFrame(results)
            a,b=st.columns(2)
            a.metric("Average waiting time",f'{df["waiting"].mean():.2f}')
            b.metric("Average turnaround time",f'{df["turnaround"].mean():.2f}')
            st.markdown("#### Process results")
            st.dataframe(df,use_container_width=True,hide_index=True)
            st.markdown("#### Gantt chart")
            fig,ax=plt.subplots(figsize=(11,2.4))
            for pid,start,end in gantt:
                ax.barh(0,end-start,left=start,height=.45)
                ax.text((start+end)/2,0,pid,ha="center",va="center",color="white",fontweight="bold")
            ax.set_xlabel("Time"); ax.set_yticks([]); ax.grid(axis="x",alpha=.25); fig.tight_layout()
            st.pyplot(fig)
            st.download_button("Download results CSV",df.to_csv(index=False),"cpu_results.csv","text/csv")
        except Exception as e: st.error(f"Could not run simulation: {e}")

elif page == "Memory Management":
    st.subheader("🧩 Memory Allocation Simulator")
    c1,c2=st.columns(2)
    with c1: blocks_text=st.text_input("Memory block sizes (comma-separated)","100, 500, 200, 300, 600")
    with c2: processes_text=st.text_input("Process sizes (comma-separated)","212, 417, 112, 426")
    strategy=st.selectbox("Allocation strategy",["First Fit","Best Fit","Worst Fit"])
    if st.button("Allocate memory",type="primary"):
        try:
            blocks=[int(x.strip()) for x in blocks_text.split(",") if x.strip()]
            processes=[int(x.strip()) for x in processes_text.split(",") if x.strip()]
            if not blocks or not processes or min(blocks+processes)<=0: raise ValueError("Enter positive block and process sizes.")
            df,remaining=memory_allocate(blocks,processes,strategy)
            x,y,z=st.columns(3)
            x.metric("Allocated",f'{(df["Status"]=="Allocated").sum()} / {len(processes)}')
            y.metric("Not allocated",int((df["Status"]!="Allocated").sum()))
            z.metric("Remaining memory",sum(remaining))
            st.dataframe(df,use_container_width=True,hide_index=True)
            st.markdown("#### Remaining size in each block")
            st.bar_chart(pd.DataFrame({"Block":[f"B{i+1}" for i in range(len(remaining))],"Remaining memory":remaining}).set_index("Block"))
            st.write("Remaining memory:",remaining)
            st.download_button("Download allocation CSV",df.to_csv(index=False),"memory_allocation.csv","text/csv")
        except Exception as e: st.error(f"Input error: {e}")

elif page == "Deadlock & Banker’s":
    st.subheader("🔐 Deadlock Avoidance — Banker’s Algorithm")
    st.write("This module uses the sample resource-allocation matrices configured in the original project.")
    allocation=[[0,1,0],[2,0,0],[3,0,2],[2,1,1],[0,0,2]]
    maximum=[[7,5,3],[3,2,2],[9,0,2],[2,2,2],[4,3,3]]
    available=[3,3,2]
    safe,sequence,need=is_safe_state(available,allocation,maximum)
    a,b=st.columns(2)
    a.metric("Available resources",str(available))
    b.metric("System state","SAFE" if safe else "UNSAFE")
    st.markdown("#### Need matrix (Maximum − Allocation)")
    st.dataframe(pd.DataFrame(need,index=[f"P{i}" for i in range(len(need))],columns=["Resource A","Resource B","Resource C"]),use_container_width=True)
    if safe: st.success("Safe sequence: "+" → ".join(sequence))
    else: st.error("No complete safe sequence found.")
    st.caption("A safe state means processes can finish in an order that releases resources for the remaining processes.")

elif page == "Disk Scheduling":
    st.subheader("💽 Disk Scheduling Simulator")
    c1,c2,c3=st.columns(3)
    with c1: req_text=st.text_input("Disk requests","98, 183, 37, 122, 14, 124, 65, 67")
    with c2: head=st.number_input("Initial head position",min_value=0,max_value=9999,value=53)
    with c3: disk_size=st.number_input("Disk size (cylinders)",min_value=2,max_value=10000,value=200)
    algo=st.selectbox("Algorithm",["FCFS","SSTF","SCAN","C-SCAN"])
    direction=st.selectbox("Direction (SCAN/C-SCAN)",["left","right"],index=1)
    if st.button("Run disk simulation",type="primary"):
        try:
            requests=[int(x.strip()) for x in req_text.split(",") if x.strip()]
            if not requests: raise ValueError("Enter at least one request.")
            if head>=disk_size or any(r<0 or r>=disk_size for r in requests): raise ValueError("Head and requests must be within 0 to disk size − 1.")
            if algo=="FCFS": order,movement,path=disk_fcfs(requests,int(head))
            elif algo=="SSTF": order,movement,path=sstf(requests,int(head))
            elif algo=="SCAN": order,movement,path=scan(requests,int(head),int(disk_size),direction)
            else: order,movement,path=c_scan(requests,int(head),int(disk_size),direction)
            a,b=st.columns(2)
            a.metric("Total head movement",f"{movement} cylinders")
            b.metric("Requests serviced",len(order))
            st.write("Service order:", " → ".join(map(str,order)))
            st.write("Head path:", " → ".join(map(str,path)))
            fig,ax=plt.subplots(figsize=(10,3.5))
            ax.plot(range(len(path)),path,marker="o")
            ax.set_xlabel("Step"); ax.set_ylabel("Cylinder"); ax.grid(alpha=.25); fig.tight_layout()
            st.pyplot(fig)
            st.download_button("Download disk path CSV",pd.DataFrame({"Step":range(len(path)),"Cylinder":path}).to_csv(index=False),"disk_path.csv","text/csv")
        except Exception as e: st.error(f"Input error: {e}")

st.markdown("---")
st.caption("OS Resource Management Simulator · Dashboard interface")
