import json
import numpy as np
import pandas as pd
from utils import *

STEMS = ['bang1_tai_chinh_quy', 'bang2a_gia_ngay', 'bang2b_gia_quy', 'bang3a_su_kien_chi_tiet', 'bang3b_su_kien_quy', 'bang4_tong_hop']

def run():
    dictionary = locate('data_dictionary', 'md').read_text(encoding='utf-8-sig')
    frames = {s: load(s) for s in STEMS}
    d = frames[STEMS[-1]]
    year = test_year(d)  # Test = năm cuối có nhãn đủ 4 quý; quý sau đó chỉ để dự báo
    lab = labelled(d)
    issues, warnings, overview, schema = [], [], [], []
    def issue(file, col, indexes, text):
        for i in indexes:
            issues.append({'file': file, 'column': col, 'csv_line': int(i)+2, 'problem': text})
    for name, frame in frames.items():
        overview.append({'file': locate(name).name, 'rows': len(frame), 'columns': len(frame.columns), 'banks': frame.ma_nh.nunique(), 'years': ','.join(map(str, sorted(frame.nam.unique()))) if 'nam' in frame else '', 'quarters': ','.join(sorted(frame.quy.unique())) if 'quy' in frame else '', 'exact_duplicates': int(frame.duplicated().sum())})
        for c in frame:
            schema.append({'file': name, 'column': c, 'dtype': str(frame[c].dtype), 'missing': int(frame[c].isna().sum())})
        keys = ['ma_nh', 'ngay'] if name == STEMS[1] else KEY
        if name != STEMS[3]:
            issue(name, '+'.join(keys), frame.index[frame.duplicated(keys, keep=False)], 'Trùng khóa')
        issue(name, 'all', frame.index[frame.duplicated()], 'Trùng toàn bộ dòng')
    last = max(pd.Period(f'{r.nam}{r.quy}', freq='Q') for r in d.itertuples())
    periods = pd.period_range('2021Q1', last, freq='Q')
    expected = pd.MultiIndex.from_tuples([(b, f'Q{p.quarter}', p.year) for b in ['ACB','BID','CTG','MBB','STB','TCB','VCB','VPB'] for p in periods], names=KEY)
    for name in [STEMS[0], STEMS[2], STEMS[4], STEMS[5]]:
        actual = pd.MultiIndex.from_frame(frames[name][KEY])
        if set(actual) != set(expected):
            issues.append({'file': name, 'column': '+'.join(KEY), 'csv_line': '', 'problem': f'Sai lưới ngân hàng-quý: thiếu {list(set(expected)-set(actual))}; thừa {list(set(actual)-set(expected))}'})
    for c in FIN+EVENT+[TARGET, 'ty_suat_sinh_loi_quy_sau']:
        values = pd.to_numeric(d[c], errors='coerce')
        # Nhãn chỉ bắt buộc đến hết năm Test; quý cuối chưa tới mốc giá quý sau thì nhãn trống là đúng
        rows = lab if c in [TARGET, 'ty_suat_sinh_loi_quy_sau'] else d.index == d.index
        issue(STEMS[-1], c, d.index[rows & ~np.isfinite(values)], 'Thiếu hoặc không hữu hạn ở biến mô hình/nhãn')
    for c in [TARGET, 'co_su_kien', 'sk_tang_von']:
        issue(STEMS[-1], c, d.index[~d[c].isin([0,1]) & ~(d[c].isna() & (c == TARGET))], 'Biến nhị phân ngoài {0,1}')
    for c in EVENT[1:]:
        issue(STEMS[-1], c, d.index[(d[c]<0)|(d[c]%1!=0)], 'Biến đếm không nguyên không âm')
    has = d[TARGET].notna()
    issue(STEMS[-1], TARGET, d.index[has & d[TARGET].ne((d.ty_suat_sinh_loi_quy_sau>0).astype(int))], 'Nhãn không khớp lợi suất')
    issue(STEMS[-1], 'co_su_kien', d.index[d.co_su_kien.ne((d.so_luong_su_kien>0).astype(int))], 'Cờ sự kiện không khớp số lượng')
    issue(STEMS[-1], 'so_luong_su_kien', d.index[d.so_luong_su_kien.ne(d[CAT].sum(axis=1))], 'Tổng loại sự kiện không khớp số lượng')
    consistency = []
    for name in [STEMS[0],STEMS[2],STEMS[4]]:
        source = frames[name].set_index(KEY)
        main = d.set_index(KEY)
        for c in source.columns.intersection(main.columns):
            a,b = source[c].reindex(main.index), main[c]
            eq = np.isclose(a,b,rtol=1e-9,atol=1e-8,equal_nan=True) if pd.api.types.is_numeric_dtype(a) else a.fillna('').eq(b.fillna('')).to_numpy()
            consistency.append({'source':name,'column':c,'mismatches':int((~eq).sum())})
            issue(STEMS[-1], c, d.index[~eq], f'Không khớp {name}')
    events = frames[STEMS[3]]
    dates = pd.to_datetime(events.ngay_cong_bo, errors='coerce')
    issue(STEMS[3], 'ngay_cong_bo', events.index[dates.isna()|dates.dt.year.ne(events.nam)|('Q'+dates.dt.quarter.astype('Int64').astype(str)).ne(events.quy)], 'Ngày sự kiện không khớp quý/năm')
    for r in d.itertuples():
        e = events[(events.ma_nh==r.ma_nh)&(events.quy==r.quy)&(events.nam==r.nam)]
        if len(e)!=r.so_luong_su_kien:
            issue(STEMS[-1], 'so_luong_su_kien', [r.Index], 'Số sự kiện không khớp bảng chi tiết')
        for c in CAT:
            if int(e.loai_su_kien.eq(c[3:]).sum()) != getattr(r,c):
                issue(STEMS[-1], c, [r.Index], 'Loại sự kiện không khớp bảng chi tiết')
    # Tái tính nhãn theo mốc cuối quý +45 ngày từ giá ngày, kể cả quý cuối có nhãn.
    daily = frames[STEMS[1]].copy()
    daily['date'] = pd.to_datetime(daily.ngay)
    for c in ['gia_dong_cua_dieu_chinh','gia_mo_cua_dieu_chinh','gia_cao_nhat_dieu_chinh','gia_thap_nhat_dieu_chinh']:
        issue(STEMS[1],c,daily.index[daily[c].isna()|daily[c].le(0)],'Giá điều chỉnh thiếu/không dương')
    issue(STEMS[1],'OHLC',daily.index[(daily.gia_cao_nhat_dieu_chinh<daily.gia_thap_nhat_dieu_chinh)|(daily.gia_dong_cua_dieu_chinh>daily.gia_cao_nhat_dieu_chinh+0.011)|(daily.gia_dong_cua_dieu_chinh<daily.gia_thap_nhat_dieu_chinh-0.011)],'Giá OHLC bất hợp lý')
    for c in ['khoi_luong_gd','khoi_luong_thoa_thuan','gia_tri_gd_ty']:
        issue(STEMS[1],c,daily.index[daily[c].isna()|daily[c].lt(0)],'Giá trị giao dịch thiếu/âm')
    for c in ['npl','car','ldr']:
        issue(STEMS[-1],c,d.index[d[c].lt(0)],'Tỷ lệ tài chính âm, cần kiểm chứng')
    price_checks=[]
    for r in frames[STEMS[2]].itertuples():
        period=pd.Period(f'{r.nam}{r.quy}',freq='Q')
        prices=daily[daily.ma_nh.eq(r.ma_nh)].sort_values('date')
        in_quarter=prices[(prices.date>=period.start_time)&(prices.date<=period.end_time)]
        previous=prices[prices.date<period.start_time]
        calculated={'gia_dau_quy':previous.iloc[-1].gia_dong_cua_dieu_chinh,'gia_cuoi_quy':in_quarter.iloc[-1].gia_dong_cua_dieu_chinh,'so_phien_gd':len(in_quarter),'gia_max':in_quarter.gia_cao_nhat_dieu_chinh.max(),'gia_min':in_quarter.gia_thap_nhat_dieu_chinh.min(),'tong_kl_gd_quy':in_quarter.khoi_luong_gd.sum(),'kl_gd_tb_phien':in_quarter.khoi_luong_gd.mean()}
        calculated['ty_suat_sinh_loi_quy']=(calculated['gia_cuoi_quy']/calculated['gia_dau_quy']-1)*100
        for c,v in calculated.items():
            valid=np.isclose(v,getattr(r,c),atol=.011,rtol=1e-6)
            price_checks.append({'csv_line':r.Index+2,'column':c,'calculated':v,'stored':getattr(r,c),'match':bool(valid)})
            if not valid:
                issue(STEMS[2],c,[r.Index],'Không khớp tổng hợp giá ngày (dung sai làm tròn 0.011)')
    save(pd.DataFrame(price_checks),'quarter_price_audit')
    checks = []
    for r in d.itertuples():
        period = pd.Period(f'{r.nam}{r.quy}',freq='Q')
        start = period.end_time.normalize()+pd.Timedelta(days=45)
        end = (period+1).end_time.normalize()+pd.Timedelta(days=45)
        prices = daily[daily.ma_nh.eq(r.ma_nh)].sort_values('date')
        p0,p1 = prices[prices.date<=start], prices[prices.date<=end]
        if prices.date.max()<end:
            # Chưa tới mốc giá quý sau: nhãn phải để trống, và chỉ được xảy ra sau năm Test
            if pd.notna(r.ty_suat_sinh_loi_quy_sau) or r.nam<=year:
                issue(STEMS[1], 'ngay', [0], f'Không đủ giá đến mốc {end.date()} cho {r.ma_nh} {r.quy}/{r.nam}')
            continue
        value = (p1.iloc[-1].gia_dong_cua_dieu_chinh/p0.iloc[-1].gia_dong_cua_dieu_chinh-1)*100
        checks.append({'csv_line':r.Index+2,'ma_nh':r.ma_nh,'quy':r.quy,'nam':r.nam,'forecast_date':str(start.date()),'label_end':str(end.date()),'recomputed_return':value,'stored_return':r.ty_suat_sinh_loi_quy_sau,'difference':value-r.ty_suat_sinh_loi_quy_sau})
        if not np.isclose(value,r.ty_suat_sinh_loi_quy_sau,atol=0.011):
            issue(STEMS[-1], 'ty_suat_sinh_loi_quy_sau', [r.Index], 'Lợi suất không khớp giá ngày/mốc dictionary (dung sai 0.011 điểm %)')
    car = d[KEY+['car','car_nguon']].copy()
    car['car_prediction'] = prediction_data(d).car
    car['changed_for_prediction'] = car.car.ne(car.car_prediction)
    save(car,'car_audit')
    save(d.groupby(['quy','car_nguon']).size().rename('observations').reset_index(),'car_source_distribution')
    # Quy tắc điền tiếp của nhóm: Q2/Q3 phải tiếp tục CAR gần nhất trong năm.
    for (bank,year),sub in d.groupby(['ma_nh','nam']):
        by_quarter=sub.set_index('quy')
        for quarter in ['Q2','Q3']:
            if quarter in by_quarter.index and by_quarter.loc[quarter,'car_nguon']=='dien_tiep_ky_truoc' and not np.isclose(by_quarter.loc[quarter,'car'],by_quarter.loc['Q1','car']):
                issue(STEMS[-1],'car',sub.index[sub.quy.eq(quarter)],'CAR điền tiếp Q2/Q3 không khớp Q1; cần nhóm kiểm tra')
    for split,sub in [('Train',d[d.nam<year]),('Test',d[d.nam==year])]:
        if sub[TARGET].nunique()!=2:
            issues.append({'file':STEMS[-1],'column':TARGET,'csv_line':'','problem':f'{split} không đủ hai lớp cho phân loại/AUC'})
    warnings += ['CAR Q4 dùng Q3 cùng năm CHỈ ở bản đầu vào dự báo theo dictionary; CAR gốc dùng cho phân cụm mô tả. Không xử lý lại quy tắc điền CAR của nhóm.', 'Không có ngày công bố BCTC thực tế: mốc +45 ngày là giả định của dictionary, chưa xác minh point-in-time; số VNDirect là bản sau cùng.', 'Thiếu data_dictionary.csv và data/manual/car_tra_thu_cong.csv được dẫn chiếu: chưa thể xác minh nguồn CAR tra thủ công độc lập.']
    outliers=[]
    for c in FIN:
        q1,q3=d[c].quantile([.25,.75]); span=q3-q1
        for i in d.index[(d[c]<q1-1.5*span)|(d[c]>q3+1.5*span)]:
            outliers.append({'csv_line':int(i)+2, **d.loc[i,KEY].to_dict(),'feature':c,'value':d.loc[i,c],'rule':'1.5 IQR; chỉ đánh dấu, không loại'})
    freq = pd.DataFrame([{'feature':c,'sum_all':int(d[c].sum()),'nonzero_all':int((d[c]>0).sum()),'sum_train':int(d.loc[d.nam<year,c].sum()),'nonzero_train':int((d.loc[d.nam<year,c]>0).sum()),'rare_train_lt5':int((d.loc[d.nam<year,c]>0).sum())<5} for c in EVENT])
    train_model=prediction_data(d[d.nam<year])
    redundancy=[]
    for name,features in [('Financial',FIN),('Financial + general',FIN+['co_su_kien']),('Financial + categories',FIN+CAT)]:
        a=train_model[features].to_numpy(dtype=float)
        std=a.std(axis=0); a=(a-a.mean(axis=0))/np.where(std==0,1,std)
        design=np.column_stack([np.ones(len(a)),a])
        redundancy.append({'model':name,'columns_including_intercept':design.shape[1],'rank':int(np.linalg.matrix_rank(design)),'condition_number_standardized':float(np.linalg.cond(design))})
    save(pd.DataFrame(redundancy),'train_design_redundancy')
    save(train_model[FIN+EVENT].corr().reset_index(),'train_feature_correlations')
    target=[]
    for split,sub in [('All',d[lab]),(f'Train 2021–{year-1}',d[d.nam<year]),(f'Test {year}',d[d.nam==year])]:
        for cls in [0,1]:
            count=int(sub[TARGET].eq(cls).sum()); target.append({'split':split,'class':cls,'count':count,'percent':round(100*count/len(sub),2)})
    missing=d[FIN+EVENT+[TARGET]].isna().sum().rename_axis('feature').reset_index(name='missing')
    save(pd.DataFrame(overview),'dataset_overview'); save(pd.DataFrame(schema),'dataset_schema_missing'); save(pd.DataFrame(consistency),'table_consistency'); save(pd.DataFrame(checks),'label_audit'); save(pd.DataFrame(outliers),'financial_outliers'); save(freq,'event_frequency'); save(pd.DataFrame(target),'target_distribution'); save(missing,'model_missing'); save(d[FIN].describe().reset_index(),'financial_descriptive'); save(d[FIN+EVENT].corr().reset_index(),'feature_correlations'); save(pd.DataFrame(issues,columns=['file','column','csv_line','problem']),'validation_issues')
    status='NOT READY FOR ML' if issues else 'READY FOR ML'
    report = f'# DATA READINESS REPORT\n\n**{status}**\n\n## 1. Dataset Overview\n\n'+md(pd.DataFrame(overview))+ '\n\nNgân hàng: '+', '.join(sorted(d.ma_nh.unique()))+f'; Q1/2021–Q{last.quarter}/{last.year}'+(f' (các quý sau {year} chỉ dùng để dự báo).' if last.year>year else '.')+' Mỗi mẫu là ngân hàng × quý.\n\n## 2. Missing Data\n\n'+md(missing)+'\n\nCác ô trống mô tả sự kiện khi không có sự kiện là hợp lệ. Toàn bộ cột/kiểu/missing nằm trong dataset_schema_missing.csv.\n\n## 3. Duplicate và consistency\n\n'+f'{len(issues)} lỗi nghiêm trọng; chi tiết dòng CSV (bao gồm header) ở validation_issues.csv. Đối chiếu mọi cột chung Bảng 1/2b/3b với Bảng 4; đối chiếu số sự kiện với 3a; tái tính nhãn từ 2a.\n\n## 4. Target Distribution\n\n'+md(pd.DataFrame(target))+'\n\n## 5. Event Frequency\n\n'+md(freq)+'\n\nHiếm: dưới 5 quan sát khác 0 trong Train, chỉ là ngưỡng cảnh báo. co_su_kien được suy ra từ count; Model 2A chọn co_su_kien trước khi xem kết quả Test. Model 2B giữ tất cả loại, không thêm tổng count vì tổng này bằng tổng các loại.\n\n## 6. Leakage Check\n\nCấm xu_huong_quy_sau và ty_suat_sinh_loi_quy_sau. Đối chiếu: roa_ttm_vnd, roe_ttm_vnd, nim_ttm_vnd, ldr_vnd. Các ngày, nguồn, URL, tiêu đề, car_nguon là mô tả, không làm input. Chỉ whitelist 6 financial và event được chọn. Train 2021–'+str(year-1)+'; Test '+str(year)+'; mọi scaler dự báo fit Train. Nhãn theo mốc +45 ngày, không phải quý lịch. Không dùng Test chọn feature/hyperparameter.\n\n## 7. CAR Check và giới hạn thời điểm\n\n'+'\n'.join('- '+w for w in warnings)+f'\n\n{int(car.changed_for_prediction.sum())} dòng Q4 có CAR đầu vào dự báo khác CAR gốc; xem car_audit.csv.\n\n## 8. Kết luận\n\n'+status+' — điều kiện: dùng bản CAR dự báo theo dictionary, chấp nhận hạn chế dữ liệu công bố nêu trên.\n'
    if issues:
        report+='\n'+md(pd.DataFrame(issues))+'\n\nĐề xuất: nhóm kiểm tra lại nguồn và phép tổng hợp các dòng liệt kê; không tự sửa dữ liệu gốc. Dừng toàn bộ huấn luyện.\n'
    report+='\n## Kiểm tra redundancy trên Train\n\n'+md(pd.DataFrame(redundancy).round(3))+'\n\nRank và condition number được kiểm tra trước train. Correlation ở train_feature_correlations.csv. Các financial giữ theo câu hỏi nghiên cứu; regularization L2 hỗ trợ khi tương quan lớn, nhưng hệ số cần diễn giải có điều kiện. Tổng count bằng tổng category nên không đưa đồng thời vào Model 2B.\n'
    (REPORTS/'data_readiness_report.md').write_text(report,encoding='utf-8')
    (REPORTS/'validation_status.json').write_text(json.dumps({'status':status,'errors':len(issues),'warnings':warnings},ensure_ascii=False,indent=2),encoding='utf-8')
    print(status, f'errors={len(issues)}')
    return d, status

if __name__=='__main__':
    run()
