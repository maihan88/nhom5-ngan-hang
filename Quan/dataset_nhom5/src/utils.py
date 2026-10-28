from pathlib import Path
import hashlib
import os
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
FIN = ['roa', 'roe', 'nim', 'npl', 'car', 'ldr']
CAT = ['sk_tang_von', 'sk_chuyen_doi_so', 'sk_hop_tac_trung_thau', 'sk_doi_lanh_dao', 'sk_chinh_sach_nhnn', 'sk_khac']
EVENT = ['co_su_kien', 'so_luong_su_kien'] + CAT
KEY = ['ma_nh', 'quy', 'nam']
TARGET = 'xu_huong_quy_sau'
TABLES = ROOT / 'outputs/tables'
FIGURES = ROOT / 'outputs/figures'
REPORTS = ROOT / 'outputs/reports'
for folder in [TABLES, FIGURES, REPORTS]:
    folder.mkdir(parents=True, exist_ok=True)

def locate(stem, ext='csv'):
    paths = sorted(p for p in ROOT.rglob(f'{stem}*.{ext}') if '.venv' not in p.parts and 'outputs' not in p.parts)
    exact = [p for p in paths if p.name == f'{stem}.{ext}']
    if len(exact) == 1:
        return exact[0]
    if len(paths) != 1:
        raise ValueError(f'Không xác định duy nhất file {stem}: {paths}')
    return paths[0]

def load(stem):
    return pd.read_csv(locate(stem))

def save(df, name, index=False):
    df.to_csv(TABLES / f'{name}.csv', index=index, encoding='utf-8-sig')

def md(df):
    # Không phụ thuộc tabulate.
    clean = df.fillna('').astype(str)
    return '| ' + ' | '.join(map(str,clean.columns)) + ' |\n|' + '|'.join(['---']*len(clean.columns)) + '|\n' + '\n'.join('| ' + ' | '.join(row) + ' |' for row in clean.values)

def prediction_data(df):
    """Quy tắc Q4 trong dictionary; không chỉnh dữ liệu gốc hoặc CAR phân cụm."""
    result = df.copy()
    q3 = df[df.quy.eq('Q3')].set_index(['ma_nh', 'nam']).car
    rows = result.quy.eq('Q4')
    result.loc[rows, 'car'] = [q3.loc[(r.ma_nh, r.nam)] for r in result.loc[rows].itertuples()]
    return result

def hashes():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.csv')}
