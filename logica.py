import pandas as pd
import numpy as np

def processar_dados_milling(df):
    # --- 1. PREPARAÇÃO E COLUNAS PONDERADAS ---
    ## 1. Colunas Inteiras (CD_UNID_IND até CD_FREN_TRAN)
    cols_int = ['CD_UNID_IND', 'CD_UPNIVEL1', 'CD_UPNIVEL2', 'CD_UPNIVEL3', 'CD_FREN_TRAN']
    for col in cols_int:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0).astype(int)
    
    ## 2. VARCHAR(3) - Apenas garantindo que seja String e limitando caracteres se necessário
    df['DE_UNID_IND'] = df['DE_UNID_IND'].astype(str)
    
    ## 3. DATETIME (Formato DD/MM/YYYY HH:MM)
    df['HR_SAIDA'] = pd.to_datetime(df['HR_SAIDA'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
    
    ## 5. Nullable FLOATS (Manter como float permite o estado NaN nativamente)
    cols_float = [
        'QT_CANA', 'QT_BRIX', 'QT_POL', 'QT_FIBRA', 
        'QT_IMPUR_TERRA', 'QT_IMPUR_VEG', 'QT_DISTANCIA'
    ]

    for col in cols_float:
        # 1. Substitui a vírgula pelo ponto
        # 2. Converte para numérico
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
    
    # Coluna de tonelada
    df['QT_TON'] = df['QT_CANA'] / 1000
    
    # Garantir que NaNs sejam tratados como 0 para multiplicação, mas mantidos para identificação de amostras
    df['QT_TON_LAB'] = np.where(df['QT_BRIX'] > 0, df['QT_TON'], 0)
    df['QT_TON_IMPUR'] = np.where(df['QT_IMPUR_TERRA'] > 0, df['QT_TON'], 0)
    # Colunas ponderadas (Regra 1)
    df['QT_POL_POND'] = df['QT_TON'] * df['QT_POL'].fillna(0)
    df['QT_FIBRA_POND'] = df['QT_TON'] * df['QT_FIBRA'].fillna(0)
    df['QT_BRIX_POND'] = df['QT_TON'] * df['QT_BRIX'].fillna(0)
    df['QT_IMPUR_TERRA_POND'] = df['QT_TON'] * df['QT_IMPUR_TERRA'].fillna(0)
    # Extração de Data e Hora
    df['DATA'] = df['HR_SAIDA'].dt.date
    df['HORA'] = df['HR_SAIDA'].dt.hour
    
    def calcular_metricas_agrupadas(df_input, group_col):
        """Aplica a lógica de cumsum e fórmulas de qualidade por grupo."""
        # Agrupamento base: Dia, ID e Hora
        agrupado = df_input.groupby(['DATA', group_col, 'HORA']).agg(
            moagem_hora=('QT_TON', 'sum'),
            pol_pond=('QT_POL_POND', 'sum'),
            fibra_pond=('QT_FIBRA_POND', 'sum'),
            brix_pond=('QT_BRIX_POND', 'sum'),
            impur_pond=('QT_IMPUR_TERRA_POND', 'sum'),
            ton_lab=('QT_TON_LAB', 'sum'),
            ton_impur=('QT_TON_IMPUR', 'sum'),
            ult_entrega=('HR_SAIDA', 'max'),
            # Filtro para última análise (Regra 5)
            ult_analise=('HR_SAIDA', lambda x: x[df_input.loc[x.index, 'QT_BRIX'].notna()].max())
        ).reset_index()
        # Garantir que todas as 24 horas existam para a série (reindex)
        idx = pd.MultiIndex.from_product(
            [agrupado['DATA'].unique(), agrupado[group_col].unique(), range(24)],
            names=['DATA', group_col, 'HORA']
        )
        agrupado = agrupado.set_index(['DATA', group_col, 'HORA']).reindex(idx).fillna(0).reset_index()
        # Cálculos Cumulativos (Regra 2)
        agrupado = agrupado.sort_values(['DATA', group_col, 'HORA'])
        g = agrupado.groupby(['DATA', group_col])
        
        agrupado['moagem_acum'] = g['moagem_hora'].cumsum()
        agrupado['pol_acum'] = g['pol_pond'].cumsum()
        agrupado['fibra_acum'] = g['fibra_pond'].cumsum()
        agrupado['brix_acum'] = g['brix_pond'].cumsum()
        agrupado['impur_acum'] = g['impur_pond'].cumsum()
        agrupado['ton_lab_acum'] = g['ton_lab'].cumsum()
        agrupado['ton_impur_acum'] = g['ton_impur'].cumsum()
        # --- Fórmulas ATR e Impureza (Regra 3) ---
        # PolCana, FibraCana, BrixCana
        # Evitar divisão por zero usando .replace(0, np.nan)
        denominador = agrupado['ton_lab_acum'].replace(0, np.nan)
        pol_cana = agrupado['pol_acum'] / denominador
        fibra_cana = agrupado['fibra_acum'] / denominador
        brix_cana = agrupado['brix_acum'] / denominador
        # Parte 1 e Parte 2
        p1 = 10 * 0.905 * 1.0526 * (pol_cana * (1 - (0.01 * fibra_cana)) * (1.0313 - (0.00575 * fibra_cana))).round(4)
        p2_interna = (3.641 - (0.0343 * ((pol_cana / brix_cana) * 100).round(2))).round(2)
        p2 = 10 * 0.905 * (p2_interna * (1 - (0.01 * fibra_cana)) * (1.0313 - (0.00575 * fibra_cana))).round(2)
        
        agrupado['ATR'] = (p1 + p2).round(2)
        agrupado['IMPUR_MINERAL'] = (agrupado['impur_acum'] / agrupado['ton_impur_acum'].replace(0, np.nan)).round(2)
        
        return agrupado
    
    # Processar Unidades e Frentes
    df_unidades = calcular_metricas_agrupadas(df, 'DE_UNID_IND')
    df_frentes = calcular_metricas_agrupadas(df, 'CD_FREN_TRAN')
    # --- 4. CONSTRUÇÃO DO JSON (LOOP FINAL) ---
    json_output = {"dias": []}
    datas = sorted(df['DATA'].unique())
    for data in datas:
        dia_dict = {"data": data.strftime('%Y-%m-%d'), "unidades": [], "frentes": []}
        
        # Processar Unidades do Dia
        for unid_id in df_unidades[df_unidades['DATA'] == data]['DE_UNID_IND'].unique():
            df_u = df_unidades[(df_unidades['DATA'] == data) & (df_unidades['DE_UNID_IND'] == unid_id)]
            ultimo_registro = df_u.iloc[-1]

            # Mock de metas (Regra 4)
            unid_data = {
                "id": unid_id,
                "ult_entrega": str(df[df['DE_UNID_IND'] == unid_id]['HR_SAIDA'].max().time()),
                "ult_analise": str(df[(df['DE_UNID_IND'] == unid_id) & (df['QT_BRIX'].notna())]['HR_SAIDA'].max().time()),
                "moagem": {
                    "total": round(df_u['moagem_hora'].sum(), 2),
                    "meta": 7200.0, # Mock
                    "serie": [{"hora": f"{int(h):02d}:00", "valor": round(v, 2), "meta": 300.0} for h, v in zip(df_u['HORA'], df_u['moagem_acum'])]
                },
                "qualidade": {
                    "ATR": {
                        "valor": float(ultimo_registro['ATR']) if pd.notna(ultimo_registro['ATR']) else None,
                        "meta": 125.0,
                        "serie": [{"hora": f"{int(h):02d}:00", "valor": v if pd.notna(v) else None} for h, v in zip(df_u['HORA'], df_u['ATR'])]
                    },
                    "impureza": {
                        "valor": float(ultimo_registro['IMPUR_MINERAL']) if pd.notna(ultimo_registro['IMPUR_MINERAL']) else None,   
                        "meta": 8.0,
                        "serie": [{"hora": f"{int(h):02d}:00", "valor": v if pd.notna(v) else None} for h, v in zip(df_u['HORA'], df_u['IMPUR_MINERAL'])]
                    }
                }
            }
            dia_dict["unidades"].append(unid_data)
        # Repetir lógica similar para frentes (simplificado para o exemplo)
        for frente_id in df_frentes[df_frentes['DATA'] == data]['CD_FREN_TRAN'].unique():
            df_f = df_frentes[(df_frentes['DATA'] == data) & (df_frentes['CD_FREN_TRAN'] == frente_id)]
            # ... (Estrutura idêntica à de unidades, alterando nomes de campos se necessário)
            dia_dict["frentes"].append({"id": int(frente_id), "moagem": {"total": round(df_f['moagem_hora'].sum(), 2)}})
        json_output["dias"].append(dia_dict)
    
    #return json.dumps(json_output, indent=2) # Retorna uma string
    return json_output # Retorna dicionario