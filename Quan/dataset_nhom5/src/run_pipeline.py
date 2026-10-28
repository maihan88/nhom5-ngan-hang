import json
import sys
import platform
import importlib.metadata
from utils import *
from data_validation import run as validate

def main():
    before=hashes()
    d,status=validate()
    if status!='READY FOR ML':
        (REPORTS/'ml_results.md').write_text('# ML Results\n\nNOT READY FOR ML. Dừng huấn luyện; xem data_readiness_report.md và validation_issues.csv.',encoding='utf-8')
        return
    from logistic_model import run as logistic
    from clustering import run as clustering
    perf,co=logistic(d)
    scores,k,profile,variance,loadings,bank=clustering(d)
    fin=perf[perf.Model.eq('Financial Only')].iloc[0]
    delta=perf[perf.Model.str.startswith('Financial +')].copy()
    for metric in ['Accuracy','F1','ROC-AUC']:
        delta['delta_'+metric]=delta[metric]-fin[metric]
    save(delta,'event_model_deltas')
    report='# Kết quả Machine Learning\n\n## 1. Data Readiness\n\nREADY FOR ML với bản CAR dự báo theo dictionary; 160 quan sát, 8 ngân hàng, 2021–2025. Không thay CSV gốc. Train 128; Test 32. Xem [Data Readiness](data_readiness_report.md).\n\n## 2. Logistic Regression\n\n'+md(perf.round(4))+'\n\nMặc định L2, C=1, ngưỡng 0.5; không tuning trên Test. Chỉ 6 biến tài chính được chuẩn hóa bằng Train; event giữ đơn vị tự nhiên (cờ/đếm), nên hệ số event không so trực tiếp magnitude với hệ số financial. Model 2A chọn cờ có sự kiện để tránh trùng thông tin với count. Model 2B giữ đủ 6 loại; hai loại chỉ có 2 quan sát Train nên hệ số dễ bất ổn. Regularization hỗ trợ nhưng không khắc phục thiếu thông tin.\n\n'+md(delta[['Model','delta_Accuracy','delta_F1','delta_ROC-AUC']].round(4))+'\n\nHệ số dương/âm biểu thị liên hệ cùng/ngược chiều với log-odds nhóm tăng, có điều kiện trên các biến khác trong mô hình; không chứng minh nhân quả. Hệ số và hướng chi tiết ở logistic_coefficients.csv. Financial standardized: một đơn vị là một độ lệch chuẩn Train.\n\n![Confusion matrices](../figures/confusion_matrices.png)\n\n![ROC](../figures/roc_curves.png)\n\n![Coefficients](../figures/logistic_coefficients.png)\n\n## 3. K-Means\n\n'+md(scores.round(4))+f'\n\nChọn K={k}: silhouette cao nhất trong 2–6, đối chiếu đường inertia và profile dưới đây. Đây là quy tắc có thể tái lập; elbow chỉ mang tính bổ trợ, không khẳng định có điểm gãy rõ. Nhóm không được chọn bằng target hoặc Test performance. Fit scaler toàn bộ 160 mẫu cho mục đích mô tả; không dùng cụm/PCA để dự báo.\n\n'+md(profile.reset_index().round(3))+'\n\nTên cụm theo hai độ lệch chuẩn lớn nhất so với trung bình toàn mẫu; “cao/thấp” là tương đối trong dataset, không phải xếp hạng chất lượng ngân hàng. Phân cụm các ngân hàng-quý, không phải 8 ngân hàng cố định. Số ngân hàng-quý theo ngân hàng:\n\n'+md(bank.reset_index())+'\n\nCluster_over_time và cluster_transitions cho thấy thay đổi theo thời gian; số cụm là nhãn tùy ý, không có thứ bậc. CAR phân cụm là CAR gốc đã được nhóm điền theo nguồn.\n\n![K selection](../figures/k_selection.png)\n\n![Cluster distribution](../figures/cluster_distribution.png)\n\n## 4. PCA\n\n'+md(variance.round(4))+'\n\n'+md(loadings.round(4))+'\n\nPCA dùng chính ma trận standardized của K-Means. Bảng trên là components_ (hệ số vector thành phần); dấu PC tùy quy ước. Hai chiều chỉ là phép chiếu, các cụm có thể chồng lấn và không thể hiện toàn bộ khoảng cách 6 chiều.\n\n'
    for pc in ['PC1','PC2']:
        top=loadings.iloc[loadings[pc].abs().nlargest(3).index]
        report+=f'{pc}: đóng góp mạnh theo trị tuyệt đối: '+', '.join(f'{r.Feature} ({getattr(r,pc):.3f})' for r in top.itertuples())+'. Không gán nhãn kinh tế vượt quá loadings.\n\n'
    report+='![PCA](../figures/pca_scatter.png)\n\n## 5. Research Question Answers\n\n'
    report+=f'**RQ1:** Financial Only đạt Accuracy {fin.Accuracy:.3f}, F1 {fin.F1:.3f}, ROC-AUC {fin["ROC-AUC"]:.3f} trên 32 mẫu Test 2025; cần đối chiếu baseline trong bảng. Đây là khả năng quan sát trong một năm kiểm tra, chưa chứng minh tính tổng quát.\n\n'
    report+='**RQ2:** Chênh lệch khi thêm event được tính ở bảng delta phía trên. '+ ('Cả hai phiên bản tăng F1 và AUC trong lần kiểm tra này' if (delta.delta_F1>0).all() and (delta['delta_ROC-AUC']>0).all() else 'Các chỉ số không đồng thời cải thiện ở cả hai phiên bản')+'; chưa đủ bằng chứng khẳng định cải thiện ổn định. Với 32 mẫu, một dự đoán khác làm Accuracy thay đổi 3.125 điểm %. Không chọn phiên bản “tốt nhất” dựa trên Test để triển khai.\n\n'
    report+=f'**RQ3:** {k} cụm tài chính mô tả theo profile thực tế ở trên, gồm '+ '; '.join(profile.description)+'.\n\n## 6. Limitations\n\n- Chỉ 160 quan sát, 8 ngân hàng, giai đoạn 2021–2025; các quan sát cùng ngân hàng và cùng quý phụ thuộc nhau.\n- Test chỉ năm 2025, chưa có validation qua nhiều năm; chưa có khoảng tin cậy hay kết luận ý nghĩa thống kê về cải thiện.\n- Event hiếm, nguồn tin và phân loại có thể thiếu; không âm thầm bỏ hoặc gộp loại.\n- CAR công bố theo năm, giá trị điền tiếp tạo nhiều quý lặp lại; chưa có nguồn manual trong project để kiểm chứng độc lập.\n- Financial VNDirect có thể là bản sau soát xét/kiểm toán; giả định BCTC biết ở +45 ngày chưa kiểm tra bằng ngày công bố thực tế.\n- Giá điều chỉnh có thể được điều chỉnh hồi tố; chưa có snapshot giá point-in-time.\n- Logistic chỉ thể hiện association, không causality. Nhãn là lợi suất giữa hai mốc +45 ngày, không phải lợi suất quý lịch.\n- K-Means phụ thuộc khoảng cách, outlier và giả định cụm dạng cầu; PCA 2D mất một phần thông tin.\n'
    report+='\n## 7. Đọc sâu kết quả và kiểm chứng diễn giải\n\n'
    baseline=perf.iloc[0]
    report+=f'Financial Only có F1 {fin.F1:.3f}, so với baseline {baseline.F1:.3f}; AUC {fin["ROC-AUC"]:.3f} gần mức ngẫu nhiên 0.5. Vì vậy khả năng dự báo hiện tại yếu. Model event tổng quát tăng Accuracy nhưng chưa vượt baseline về F1; Model categories không cải thiện F1 so với financial only.\n\n'
    for model,sub in co.groupby('Model',sort=False):
        strongest=sub[sub.feature.isin(FIN)].head(3)
        report+=model+': các financial có |hệ số| lớn nhất: '+', '.join(f'{r.feature} {r.coefficient:+.3f} ({r.direction})' for r in strongest.itertuples())+'. Đây là liên hệ có điều kiện, không phải tác động nhân quả.\n\n'
    assignments=pd.read_csv(TABLES/'cluster_assignments.csv')
    transitions=pd.read_csv(TABLES/'cluster_transitions.csv')
    changed=int(transitions.loc[transitions.previous_cluster.ne(transitions.cluster),'count'].sum())
    report+=f'Có {changed} lần chuyển cụm giữa các quý liên tiếp trong toàn bộ panel. '
    for c in sorted(assignments.cluster.unique()):
        sub=assignments[assignments.cluster.eq(c)]
        distribution=sub.ma_nh.value_counts()
        report+=f'Cụm {c}: '+', '.join(f'{bank} {count} mẫu' for bank,count in distribution.items())+'. '
    report+='Phân cụm chủ yếu phản ánh khác biệt cố hữu giữa ngân hàng, chưa chứng minh trạng thái tài chính biến đổi rộng theo thời gian. Các mẫu STB trong cụm ít quan sát: '+', '.join(f'{r.quy}/{r.nam}' for r in assignments[(assignments.ma_nh.eq('STB'))&(assignments.cluster.eq(profile.observations.idxmin()))].itertuples())+'.\n\n'
    report+=f'K={k} có silhouette {scores.loc[scores.K.eq(k),"Silhouette"].iloc[0]:.3f}; K=5 và 6 tạo cụm nhỏ nhất chỉ 3 mẫu. Đường inertia tiếp tục giảm nhưng tách thêm cụm kém gọn và khó bảo vệ trên dataset nhỏ. K=2 phù hợp hai profile đối lập về NPL/LDR, đồng thời nhóm NPL/LDR cao có NIM và CAR cao hơn, ROE thấp hơn. Chênh lệch ROA nhỏ, không nên gọi nhóm này profitability cao.\n\n'
    report+='PC1 có NIM, LDR, CAR cùng dấu và đóng góp mạnh; mô tả trục đồng biến ba tỷ lệ này, không gọi chung là “tốt hơn”. PC2 chủ yếu đối chiếu ROE/ROA dương với NPL âm; hỗ trợ cách đọc lợi nhuận tương đối đối lập nợ xấu trong phép chiếu này. PCA scatter vẫn có một điểm cụm NPL cao lệch xa theo PC2; không xem mọi điểm cùng cụm là đồng nhất.\n'
    (REPORTS/'ml_results.md').write_text(report,encoding='utf-8')
    assert before==hashes(), 'CSV nguồn bị thay đổi'
    (REPORTS/'reproducibility.json').write_text(json.dumps({'source_sha256':before,'python':platform.python_version(),'packages':{p:importlib.metadata.version(p) for p in ['pandas','numpy','scikit-learn','matplotlib']},'random_state':42,'csv_unchanged':True},indent=2),encoding='utf-8')
    print(perf.drop(columns='Features').to_string(index=False)); print('K=',k); print(variance.to_string(index=False))

if __name__=='__main__':
    main()
