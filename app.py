from __future__ import annotations
import io, sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st
from parsers.sources import SOURCES, scrape

st.set_page_config(page_title='Monitor Cen PL',page_icon='💰',layout='wide')
st.title('Monitor Cen PL')
st.caption('MVP v0.1.1 • retail osobno od marketplace • wyszukiwanie po EAN, następnie PN')

def load_products(file):
    df=pd.read_excel(file,dtype=str).fillna('')
    df.columns=[str(c).strip().upper() for c in df.columns]
    if 'PN' not in df.columns: raise ValueError('Plik musi zawierać kolumnę PN.')
    for c in ['EAN','NAZWA']:
        if c not in df.columns: df[c]=''
    df=df[['PN','EAN','NAZWA']]
    df=df[df['PN'].str.strip()!=''].drop_duplicates('PN')
    return df

def save_history(df):
    con=sqlite3.connect('price_history.db')
    out=df.copy(); out['data_pomiaru']=datetime.now().isoformat(timespec='seconds')
    out.to_sql('prices',con,if_exists='append',index=False); con.close()

def xlsx_bytes(df):
    bio=io.BytesIO()
    retail=df[df.typ=='retail']; market=df[df.typ=='marketplace']
    ok=df[df.cena.notna()].sort_values(['pn','cena'])
    low=ok.groupby('pn',as_index=False).first() if not ok.empty else ok
    with pd.ExcelWriter(bio,engine='openpyxl') as w:
        df.to_excel(w,index=False,sheet_name='Wszystkie wyniki')
        retail.to_excel(w,index=False,sheet_name='Retail')
        market.to_excel(w,index=False,sheet_name='Marketplace')
        low.to_excel(w,index=False,sheet_name='Najniższe ceny')
    return bio.getvalue()

uploaded=st.file_uploader('Wgraj listę produktów XLSX',type=['xlsx'])
use_demo=st.checkbox('Użyj dołączonego pliku products.xlsx',value=uploaded is None)
try:
    products=load_products(uploaded if uploaded else 'products.xlsx') if (uploaded or use_demo) else pd.DataFrame()
except Exception as e:
    st.error(str(e)); st.stop()

if not products.empty:
    st.success(f'Wczytano produktów: {len(products)}')
    st.dataframe(products,use_container_width=True,height=240)
    selected=st.multiselect('Źródła',list(SOURCES),default=list(SOURCES))
    limit=st.number_input('Limit produktów dla jednego skanu',1,len(products),min(20,len(products)))
    st.warning('Sklepy mogą blokować automatyczne zapytania. Status „zablokowano” nie oznacza błędu pliku produktu.')
    if st.button('Uruchom skan',type='primary',disabled=not selected):
        rows=[]; bar=st.progress(0); total=int(limit)*len(selected); done=0
        for _,p in products.head(int(limit)).iterrows():
            for source in selected:
                rows.append(scrape(source,p.PN,p.EAN,p.NAZWA).dict())
                done+=1; bar.progress(done/total)
        result=pd.DataFrame(rows)
        st.session_state['result']=result
        save_history(result)

if 'result' in st.session_state:
    result=st.session_state['result']
    c1,c2,c3=st.columns(3)
    c1.metric('Rekordy',len(result)); c2.metric('Z ceną',int(result.cena.notna().sum())); c3.metric('Źródła',result.zrodlo.nunique())
    tab1,tab2,tab3=st.tabs(['Wszystkie','Retail','Marketplace'])
    tab1.dataframe(result,use_container_width=True)
    tab2.dataframe(result[result.typ=='retail'],use_container_width=True)
    tab3.dataframe(result[result.typ=='marketplace'],use_container_width=True)
    st.download_button('Pobierz raport Excel',xlsx_bytes(result),'raport_cen.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
