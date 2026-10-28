"""Báo cáo kết luận lấy số liệu trực tiếp từ các output ML đã lưu."""
from pathlib import Path
import csv
import json
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
TABLES=ROOT/'outputs/tables'
FIGURES=ROOT/'outputs/figures'
QA=ROOT/'outputs/docx_qa'
QA.mkdir(exist_ok=True)
OUT=ROOT/'Ket_luan_Machine_Learning_Hoang_Manh_Quan.docx'
data={p.stem:list(csv.DictReader(p.open(encoding='utf-8-sig'))) for p in TABLES.glob('*.csv')}
metrics={r['Model']:r for r in data['model_comparison']}
coeff={(r['Model'],r['feature']):float(r['coefficient']) for r in data['logistic_coefficients']}
profiles=data['cluster_profiles']
variance=data['pca_explained_variance']
fin=metrics['Financial Only']; general=metrics['Financial + General Event']; categories=metrics['Financial + Event Categories']
assert len(metrics)==4 and len(profiles)==2 and not data['validation_issues']
assert all(int(r['missing'])==0 for r in data['model_missing'])
for p in (ROOT/'notebooks').glob('*.ipynb'):
    nb=json.loads(p.read_text(encoding='utf-8'))
    assert all(c.get('execution_count') is not None for c in nb['cells'] if c['cell_type']=='code')

def number(x,d=4):
    return f'{float(x):.{d}f}'.replace('.',',')

def percent(x,d=2):
    return number(float(x)*100,d)+'%'

doc=Document()
doc.core_properties.author='Hoàng Mạnh Quân'
doc.core_properties.title='Kết luận Machine Learning trong phân tích tài chính ngân hàng niêm yết'
doc.core_properties.subject='Logistic Regression K Means và PCA'
section=doc.sections[0]
section.page_width=Cm(21); section.page_height=Cm(29.7)
section.top_margin=section.bottom_margin=section.left_margin=section.right_margin=Cm(2.54)
for name,size in [('Normal',13),('Title',16),('Heading 1',14),('Heading 2',13),('Caption',13)]:
    style=doc.styles[name]
    style.font.name='Times New Roman'; style.font.size=Pt(size); style.font.color.rgb=RGBColor(0,0,0)
    style.font.bold=name in ['Title','Heading 1','Heading 2']
    fonts=style.element.get_or_add_rPr().get_or_add_rFonts()
    for key in list(fonts.attrib):
        if 'theme' in key.lower():
            del fonts.attrib[key]
    for key in ['ascii','hAnsi','eastAsia','cs']:
        fonts.set(qn('w:'+key),'Times New Roman')
    style.paragraph_format.line_spacing=1.3
    style.paragraph_format.space_after=Pt(4)
    style.paragraph_format.space_before=Pt(0 if name=='Normal' else 8)
    style.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
    style.paragraph_format.widow_control=True
    for border in style.element.xpath('./w:pPr/w:pBdr'):
        border.getparent().remove(border)
    if name.startswith('Heading'):
        style.paragraph_format.keep_with_next=True
doc.styles['Title'].paragraph_format.alignment=WD_ALIGN_PARAGRAPH.CENTER
footer=section.footer.paragraphs[0]; footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
field=OxmlElement('w:fldSimple'); field.set(qn('w:instr'),'PAGE'); footer._p.append(field)

def p(text,bold=False):
    para=doc.add_paragraph(); run=para.add_run(text); run.bold=bold
    para.paragraph_format.keep_together=True
    return para

def heading(text,level=1):
    doc.add_heading(text,level)

def page():
    # Cho Word phân trang tự nhiên để tránh khoảng trống và trang chỉ có vài dòng.
    pass

table_count=0; figure_count=0; evidence=[]
def table(title,headers,rows,widths):
    global table_count
    table_count+=1
    cap=p(f'Bảng {table_count}. {title}',True); cap.paragraph_format.keep_with_next=True
    t=doc.add_table(rows=1,cols=len(headers)); t.alignment=WD_TABLE_ALIGNMENT.CENTER; t.autofit=False
    for i,w in enumerate(widths):
        t.columns[i].width=Cm(w)
    for c,value in zip(t.rows[0].cells,headers):
        c.text=str(value)
        sh=OxmlElement('w:shd'); sh.set(qn('w:fill'),'F2F2F2'); c._tc.get_or_add_tcPr().append(sh)
    repeat=OxmlElement('w:tblHeader'); t.rows[0]._tr.get_or_add_trPr().append(repeat)
    for values in rows:
        for c,value in zip(t.add_row().cells,values):
            c.text=str(value)
    borders=OxmlElement('w:tblBorders')
    for tag in ['top','left','bottom','right','insideH','insideV']:
        e=OxmlElement('w:'+tag); e.set(qn('w:val'),'single'); e.set(qn('w:sz'),'4'); e.set(qn('w:color'),'D9D9D9'); borders.append(e)
    t._tbl.tblPr.append(borders)
    for ri,row in enumerate(t.rows):
        no_split=OxmlElement('w:cantSplit'); row._tr.get_or_add_trPr().append(no_split)
        for ci,c in enumerate(row.cells):
            c.width=Cm(widths[ci]); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            margins=OxmlElement('w:tcMar')
            for edge,v in [('top','45'),('bottom','45'),('left','70'),('right','70')]:
                el=OxmlElement('w:'+edge); el.set(qn('w:w'),v); el.set(qn('w:type'),'dxa'); margins.append(el)
            c._tc.get_or_add_tcPr().append(margins)
            for para in c.paragraphs:
                para.alignment=WD_ALIGN_PARAGRAPH.LEFT if ci==0 else WD_ALIGN_PARAGRAPH.CENTER
                para.paragraph_format.space_before=Pt(0); para.paragraph_format.space_after=Pt(0); para.paragraph_format.line_spacing=1.3
                for run in para.runs:
                    run.font.name='Times New Roman'; run.font.size=Pt(13); run.font.color.rgb=RGBColor(0,0,0); run.bold=ri==0
    return t

def figure(file,title,comment,width=14):
    global figure_count
    figure_count+=1
    para=doc.add_paragraph(); para.alignment=WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.space_after=Pt(3); para.paragraph_format.keep_with_next=True
    source=QA/file if (QA/file).exists() else FIGURES/file
    run=para.add_run(); inline=run.add_picture(str(source),width=Cm(width))
    inline._inline.docPr.set('descr',title)
    cap=p(f'Hình {figure_count}. {title}',True); cap.paragraph_format.keep_with_next=True
    p(comment)

# Trang 1
doc.add_paragraph('KẾT LUẬN PHẦN MACHINE LEARNING',style='Title')
para=p('Đề tài: Phân tích tài chính các công ty niêm yết ngành ngân hàng',True); para.alignment=WD_ALIGN_PARAGRAPH.CENTER
para=p('Người thực hiện: Hoàng Mạnh Quân'); para.alignment=WD_ALIGN_PARAGRAPH.CENTER
p('Phần Machine Learning đánh giá khả năng phân loại xu hướng giá cổ phiếu kỳ tiếp theo bằng Logistic Regression, kiểm tra thông tin bổ sung từ sự kiện phi tài chính và khám phá các nhóm đặc điểm tài chính bằng K-Means kết hợp PCA. Kết quả cho thấy khả năng dự báo còn hạn chế; phân cụm và trực quan hóa có giá trị trong việc nhận diện cấu trúc dữ liệu.')
heading('1 Kết quả kiểm tra dữ liệu')
overview=next(r for r in data['dataset_overview'] if r['file']=='bang4_tong_hop.csv')
p(f"Bảng tổng hợp có {overview['rows']} quan sát và {overview['columns']} cột, gồm {overview['banks']} ngân hàng: ACB, BID, CTG, MBB, STB, TCB, VCB và VPB. Giai đoạn phân tích là 2021–2025, với bốn quý mỗi năm. Mỗi dòng đại diện cho một ngân hàng tại một quý.")
targets=data['target_distribution']
rows=[]
for split,label in [('All','Toàn bộ'),('Train 2021–2024','Train 2021–2024'),('Test 2025','Test 2025')]:
    sub={r['class']:r for r in targets if r['split']==split}
    rows.append([label,str(sum(int(r['count']) for r in sub.values())),f"{sub['0']['count']} ({number(sub['0']['percent'],2)}%)",f"{sub['1']['count']} ({number(sub['1']['percent'],2)}%)"])
table('Quy mô mẫu và phân bố biến mục tiêu',['Tập dữ liệu','Số mẫu','Không tăng 0','Tăng 1'],rows,[4.8,2,4.56,4.56])
p('Các biến đầu vào tài chính, sự kiện và nhãn không có giá trị thiếu; không phát hiện trùng khóa ma_nh + quy + nam hoặc dòng trùng hoàn toàn. Các ô trống mô tả ở quý không có sự kiện là hợp lệ. Đối chiếu Bảng 1, 2b, 3b với Bảng 4, tổng hợp giá quý và tính lại nhãn từ giá ngày không phát hiện lỗi nghiêm trọng.')
p('Kết luận kiểm tra là READY FOR ML, với điều kiện tuân thủ quy tắc thời điểm của Data Dictionary. Nhãn được tính giữa các mốc cuối quý cộng 45 ngày, không phải lợi suất của quý lịch. CAR đầu vào dự báo ở Q4 lấy CAR Q3 cùng năm; dữ liệu gốc và CAR dùng cho phân cụm được giữ nguyên. Các hạn chế về bản công bố dữ liệu được trình bày tại mục 7.')

# Trang 2
page(); heading('2 Kết quả Logistic Regression')
heading('2 1 Các mô hình và phương pháp đánh giá',2)
p('Bốn mô hình đã thực hiện gồm Baseline (DummyClassifier dự đoán lớp phổ biến), Financial Only (ROA, ROE, NIM, NPL, CAR, LDR), Financial + General Event (thêm co_su_kien) và Financial + Event Categories (thêm sáu loại sự kiện).')
p('Huấn luyện trên 2021–2024 và kiểm tra trên 2025; không chia mẫu ngẫu nhiên. StandardScaler chỉ fit trên Train cho biến tài chính; sự kiện giữ đơn vị cờ hoặc đếm. Logistic Regression dùng cấu hình mặc định có regularization L2, ngưỡng phân loại 0,5; không tối ưu tham số bằng Test.')
heading('2 2 Bảng so sánh hiệu quả',2)
labels={'Baseline':'Baseline','Financial Only':'Financial Only','Financial + General Event':'Financial + General Event','Financial + Event Categories':'Financial + Event Categories'}
rows=[[labels[name]]+[number(r[c],4) for c in ['Accuracy','Precision','Recall','F1','ROC-AUC']] for name,r in metrics.items()]
table('Hiệu quả phân loại trên Test 2025',['Mô hình','Accu-\nracy','Preci-\nsion','Recall','F1','ROC-\nAUC'],rows,[5.02,2.18,2.18,2.18,2.18,2.18])
# Vẽ riêng ma trận mô hình chính từ bảng chính thức để chữ đọc được khi in.
cm=next(r for r in data['confusion_matrices'] if r['Model']=='Financial Only')
im=Image.new('RGB',(1000,680),'white'); draw=ImageDraw.Draw(im)
font=ImageFont.truetype('C:/Windows/Fonts/times.ttf',36)
big=ImageFont.truetype('C:/Windows/Fonts/timesbd.ttf',54)
draw.text((500,45),'Financial Only',font=big,fill='black',anchor='mm')
draw.text((585,115),'Nhãn dự đoán',font=font,fill='black',anchor='mm')
draw.text((570,640),'0 = không tăng     1 = tăng',font=font,fill='black',anchor='mm')
for j,label in enumerate(['0','1']):
    draw.text((465+j*240,175),label,font=font,fill='black',anchor='mm')
    draw.text((290,300+j*180),label,font=font,fill='black',anchor='mm')
draw.text((150,370),'Nhãn thực tế',font=font,fill='black',anchor='mm')
for i,row in enumerate([[cm['TN'],cm['FP']],[cm['FN'],cm['TP']]]):
    for j,val in enumerate(row):
        x,y=345+j*240,210+i*180
        draw.rectangle((x,y,x+240,y+180),fill='#F2F2F2' if i==j else 'white',outline='black',width=3)
        draw.text((x+120,y+90),str(val),font=big,fill='black',anchor='mm')
im.save(FIGURES/'financial_only_confusion.png')
figure('financial_only_confusion.png','Ma trận nhầm lẫn của mô hình Financial Only','Financial Only phân loại đúng 15 mẫu tăng nhưng chỉ đúng 1 mẫu không tăng. Phiên bản General Event phân loại đúng 12 mẫu tăng và 8 mẫu không tăng theo bảng kết quả, cho thấy phân loại cân bằng hơn giữa hai lớp.',width=11)

# Trang 3
page(); heading('2 3 Nhận xét về hiệu quả mô hình',2)
p(f"Financial Only đạt Accuracy {percent(fin['Accuracy'])}, F1 {number(fin['F1'])} và ROC-AUC {number(fin['ROC-AUC'])}. Accuracy bằng Baseline, F1 thấp hơn Baseline ({number(metrics['Baseline']['F1'])}); AUC chỉ nhỉnh hơn mức ngẫu nhiên 0,5. Recall cao nhưng Precision chỉ {number(fin['Precision'])}, phù hợp với xu hướng dự đoán phần lớn mẫu vào lớp tăng.")
delta={r['Model']:r for r in data['event_model_deltas']}
dg=delta['Financial + General Event']; dc=delta['Financial + Event Categories']
p(f"General Event có Accuracy {percent(general['Accuracy'])} và ROC-AUC {number(general['ROC-AUC'])}, cao nhất trong các mô hình đã kiểm tra. So với Financial Only, Accuracy tăng {number(float(dg['delta_Accuracy'])*100,2)} điểm phần trăm, F1 tăng {number(dg['delta_F1'])} và AUC tăng {number(dg['delta_ROC-AUC'])}. Tuy nhiên, F1 {number(general['F1'])} chỉ bằng Baseline.")
p(f"Event Categories đạt Accuracy {percent(categories['Accuracy'])}, F1 {number(categories['F1'])} và AUC {number(categories['ROC-AUC'])}. Accuracy tăng {number(float(dc['delta_Accuracy'])*100,2)} điểm phần trăm nhưng F1 giảm {number(abs(float(dc['delta_F1'])))} so với Financial Only. Vì vậy, thêm loại sự kiện không cải thiện đồng thời các tiêu chí.")
figure('roc_curves.png','Đường ROC trên tập Test 2025','Các AUC đều gần 0,5. General Event có kết quả quan sát tốt hơn về Accuracy và AUC, nhưng chưa có khoảng tin cậy hoặc kiểm định để khẳng định cải thiện có ý nghĩa thống kê.',width=11)
p('“Tốt nhất” ở đây chỉ là so sánh mô tả trên một tập Test nhỏ, không phải cơ sở chọn mô hình triển khai. Kết luận phù hợp là event tổng quát cải thiện một số chỉ số trong lần kiểm tra này, nhưng chưa đủ bằng chứng về cải thiện ổn định.')

# Trang 4
page(); heading('3 Phân tích hệ số Logistic Regression')
p('Hệ số dương/âm được diễn giải là có mối liên hệ cùng chiều/ngược chiều với khả năng được phân loại vào nhóm tăng giá, khi giữ các biến khác trong mô hình. Bảng dưới trình bày các financial nổi bật và toàn bộ biến sự kiện; dấu gạch thể hiện biến không có trong mô hình.')
features=['roa','roe','car','co_su_kien','sk_tang_von','sk_chuyen_doi_so','sk_hop_tac_trung_thau','sk_doi_lanh_dao','sk_chinh_sach_nhnn','sk_khac']
rows=[[feature]+[number(coeff[(name,feature)]) if (name,feature) in coeff else '—' for name in ['Financial Only','Financial + General Event','Financial + Event Categories']] for feature in features]
table('Các hệ số nổi bật và hệ số sự kiện',['Feature','Financial Only','General Event','Event Categories'],rows,[6.32,3.2,3.2,3.2])
p(f"ROA có hệ số dương trong cả ba mô hình ({number(coeff[('Financial Only','roa')])}; {number(coeff[('Financial + General Event','roa')])}; {number(coeff[('Financial + Event Categories','roa')])}). ROE và CAR có hệ số âm. Trong Financial Only, ROA, ROE và CAR có trị tuyệt đối hệ số lớn nhất trong nhóm financial.")
figure('logistic_coefficients.png','Hệ số của ba mô hình Logistic Regression','Các financial đã chuẩn hóa nên hệ số ứng với một độ lệch chuẩn Train. Event giữ đơn vị tự nhiên, vì vậy không so trực tiếp magnitude giữa event và financial như một thước đo mức độ quan trọng.',width=15.92)
p('co_su_kien, sk_tang_von, sk_doi_lanh_dao và sk_khac có hệ số âm; sk_chuyen_doi_so, sk_hop_tac_trung_thau và sk_chinh_sach_nhnn có hệ số dương. Chuyển đổi số và chính sách NHNN chỉ có 2 quan sát khác 0 trong Train mỗi loại, nên hệ số có thể không ổn định. Hệ số khác 0 không chứng minh tác động nhân quả hoặc ý nghĩa thống kê.')

# Trang 5
page(); heading('4 Kết quả K Means Clustering')
heading('4 1 Lựa chọn số cụm',2)
p('Phân cụm thực hiện trên các quan sát ngân hàng theo quý, sử dụng sáu biến tài chính đã chuẩn hóa. Scaler được fit trên toàn kỳ cho phân tích mô tả; không sử dụng target, sự kiện hoặc cụm làm đầu vào dự báo Logistic Regression.')
ks=data['k_selection']
table('Inertia và Silhouette của các K đã thử',['K','Inertia','Silhouette','Cụm nhỏ nhất'],[[r['K'],number(r['Inertia']),number(r['Silhouette']),r['smallest_cluster']] for r in ks],[1.5,5.2,4.5,4.72])
figure('k_selection.png','Elbow và Silhouette khi thử K từ 2 đến 6','Inertia giảm khi tăng K, còn Silhouette cao nhất tại K = 2. Elbow cung cấp bằng chứng bổ trợ nhưng không thể hiện một điểm gãy đủ rõ để quyết định độc lập.',width=15.92)
k2=next(r for r in ks if r['K']=='2')
p(f"K cuối cùng là 2, với Silhouette {number(k2['Silhouette'])}. Các K còn lại có Silhouette thấp hơn; K = 5 và K = 6 tạo cụm nhỏ nhất chỉ 3 mẫu. Hai cụm được chọn có profile diễn giải được theo khác biệt NPL và LDR, nên lựa chọn này kết hợp chất lượng phân tách và khả năng giải thích tài chính.")
p('Số cụm là kết quả mô tả trong phạm vi dữ liệu đã có, không phải số nhóm ngân hàng cố định trong thực tế. Nhãn Cluster 0 và Cluster 1 chỉ là mã số, không có thứ bậc chất lượng.')

# Trang 6
page(); heading('4 2 Đặc điểm tài chính và phân bố cụm',2)
features=['roa','roe','nim','npl','car','ldr']
table('Giá trị trung bình của các cụm',['Chỉ tiêu','Cluster 0','Cluster 1'],[[f.upper()+' (%)',number(profiles[0][f],3),number(profiles[1][f],3)] for f in features]+[['Số quan sát',profiles[0]['observations'],profiles[1]['observations']]],[6.52,4.7,4.7])
p('Cluster 0 được mô tả là nhóm NPL thấp tương đối và LDR thấp tương đối; đồng thời ROE cao hơn Cluster 1. Cluster 1 có NPL, LDR, NIM và CAR cao hơn nhưng ROE thấp hơn. ROA của hai nhóm khá gần nhau, nên không gọi Cluster 1 là nhóm sinh lời cao chỉ dựa trên NIM hoặc ROA.')
table('Số quan sát theo ngân hàng và cụm',['Ngân hàng','Cluster 0','Cluster 1'],[[r['ma_nh'],r['0'],r['1']] for r in data['bank_cluster_distribution']],[6.52,4.7,4.7])
p('Cluster 0 gồm toàn bộ các quý của ACB, BID, CTG, MBB, TCB, VCB và 19 quý của STB. Cluster 1 gồm toàn bộ 20 quý của VPB cùng STB Q4/2025. Bảng chuyển cụm chỉ ghi nhận một lần chuyển, từ Cluster 0 sang Cluster 1 của STB ở quý cuối giai đoạn.')
p('Kết quả chủ yếu phản ánh sự khác biệt tài chính giữa ngân hàng; bằng chứng về biến đổi nhóm theo thời gian còn ít. NPL và LDR cao hơn không đủ để kết luận một ngân hàng kém hơn toàn diện, vì các nhóm còn khác nhau về CAR, NIM và lợi nhuận.')

# Trang 7
page(); heading('5 Kết quả PCA')
p('PCA sử dụng chính ma trận StandardScaler đã dùng cho K-Means. Hai thành phần chính phục vụ trực quan hóa và hỗ trợ diễn giải cụm; không được dùng để huấn luyện mô hình dự báo trong pipeline này.')
table('Tỷ lệ phương sai giải thích',['Thành phần','Phương sai giải thích','Lũy kế'],[[r['PC'],percent(r['explained_variance_ratio']),percent(r['cumulative'])] for r in variance],[3.92,6,6])
table('Hệ số thành phần PCA từ components_',['Feature','PC1','PC2'],[[r['Feature'].upper(),number(r['PC1']),number(r['PC2'])] for r in data['pca_loadings']],[6.52,4.7,4.7])
p('PC1 có đóng góp mạnh nhất theo trị tuyệt đối từ NIM, LDR và CAR, cùng dấu dương. PC2 chủ yếu gắn với ROE và ROA dương, NPL âm. Điều này hỗ trợ cách đọc các trục dựa trên tỷ lệ tài chính, nhưng không xem PC1 lớn hơn là trạng thái tốt hơn.')
figure('pca_scatter.png','Các quan sát ngân hàng quý trên không gian PCA','Hai cụm tách khá rõ trên phép chiếu, chủ yếu theo PC1; vẫn có một điểm thuộc Cluster 1 lệch xa theo PC2. Tổng phương sai giữ lại là '+percent(variance[-1]['cumulative'])+', nên biểu đồ không thể hiện toàn bộ khoảng cách trong sáu chiều.',width=10.8)

# Trang 8
page(); heading('6 Trả lời câu hỏi nghiên cứu')
heading('6 1 Khả năng dự báo từ chỉ số tài chính',2)
p(f"Khả năng phân loại của Financial Only còn hạn chế: Accuracy {percent(fin['Accuracy'])}, F1 {number(fin['F1'])}, ROC-AUC {number(fin['ROC-AUC'])} trên Test 2025. Mô hình chưa vượt Baseline về Accuracy hoặc F1 và AUC gần ngẫu nhiên. Các chỉ số tài chính hiện tại có giá trị khám phá mối liên hệ, nhưng chưa cho thấy sức dự báo thực tế cao.")
heading('6 2 Giá trị bổ sung của sự kiện phi tài chính',2)
p('Kết luận là có cải thiện ở một số chỉ số với event tổng quát, nhưng cải thiện tổng thể chưa đủ rõ ràng và chưa được chứng minh ổn định. General Event tăng Accuracy và AUC, F1 chỉ bằng Baseline. Event Categories tăng Accuracy và AUC nhẹ so với Financial Only nhưng làm F1 giảm. Không thể kết luận mọi cách bổ sung event đều tốt hơn.')
heading('6 3 Các nhóm đặc điểm tài chính',2)
p('Các quan sát ngân hàng theo quý hình thành hai cụm: nhóm NPL/LDR thấp tương đối và nhóm NPL/LDR cao tương đối. Nhóm thứ hai đồng thời có NIM/CAR cao hơn và ROE thấp hơn. Đây là cấu trúc đa biến của 160 quan sát, không phải việc phân chia cố định chỉ tám ngân hàng.')
heading('7 Hạn chế')
p('Quy mô và kiểm tra ngoài mẫu: chỉ 160 quan sát thuộc 8 ngân hàng trong 2021–2025; Train có 128 mẫu và Test có 32 mẫu. Các quan sát cùng ngân hàng hoặc cùng quý có thể phụ thuộc. Chỉ một năm Test, chưa có kiểm tra qua nhiều giai đoạn, khoảng tin cậy hoặc bằng chứng ý nghĩa thống kê cho chênh lệch mô hình.')
p('Sự kiện và CAR: một số loại sự kiện rất hiếm; việc tìm tin và phân loại có thể thiếu. CAR công bố theo năm, được điền tiếp theo quy tắc của nhóm; khi dự báo Q4 phải dùng Q3. Project chưa có tệp nguồn CAR tra thủ công để kiểm chứng độc lập.')
p('Thời điểm dữ liệu: VNDirect có thể lưu số liệu sau soát xét/kiểm toán; giả định công bố BCTC tại mốc cộng 45 ngày chưa được xác minh bằng ngày công bố thực tế. Giá điều chỉnh có thể được điều chỉnh hồi tố, chưa có bản chụp dữ liệu tại từng thời điểm dự báo.')
p('Diễn giải: Logistic Regression thể hiện association, không chứng minh causality; hệ số chịu ảnh hưởng của tương quan giữa feature và regularization. K-Means phụ thuộc khoảng cách, outlier và giả định hình dạng cụm; PCA hai chiều mất một phần thông tin. Kết quả dự báo không được hiểu là khuyến nghị đầu tư.')

# Trang 9
page(); heading('8 Kết luận chung')
p('Phần Machine Learning cho thấy các chỉ số tài chính trong bộ dữ liệu hiện tại chưa đủ để phân loại tốt xu hướng tăng hoặc không tăng của giá cổ phiếu kỳ tiếp theo. Financial Only chưa vượt phương pháp dự đoán đơn giản về Accuracy và F1. Do đó, mô hình có giá trị trong việc khám phá và đánh giá mối liên hệ, nhưng khả năng dự báo thực tế còn hạn chế.')
p('Sự kiện phi tài chính cung cấp thêm thông tin trong phiên bản sử dụng cờ có sự kiện, thể hiện ở Accuracy và AUC cao hơn. Tuy nhiên, mức lợi ích phụ thuộc cách biểu diễn event, không đồng nhất giữa các tiêu chí và chưa được kiểm chứng ổn định trên nhiều giai đoạn. Các hệ số sự kiện cần được đọc như liên hệ có điều kiện; đặc biệt thận trọng với loại chỉ xuất hiện ở rất ít quan sát.')
p('K-Means nhận diện hai profile khác nhau trên tổ hợp sáu chỉ số tài chính, còn PCA làm rõ cấu trúc đó trong không gian hai chiều giữ phần lớn phương sai. Kết quả bổ sung cho thống kê mô tả bằng cách xem xét đồng thời các biến, nhận diện sự tập trung quan sát theo ngân hàng và kiểm tra khả năng thay đổi cụm qua quý. Giá trị của phần việc là tạo cơ sở định lượng để đánh giá giới hạn dự báo và diễn giải cấu trúc tài chính đa biến, thay vì chỉ so sánh từng chỉ tiêu riêng lẻ.')
heading('Nguồn kết quả đối chiếu',2)
p('Nguồn nội bộ của đề tài: data_dictionary.md; outputs/reports/data_readiness_report.md; outputs/reports/ml_results.md; ba notebook 01_data_validation, 02_logistic_regression, 03_kmeans_pca đã thực thi.')
p('Các bảng được sử dụng: dataset_overview, target_distribution, model_missing, validation_issues, model_comparison, confusion_matrices, event_model_deltas, logistic_coefficients, event_frequency, k_selection, cluster_profiles, bank_cluster_distribution, cluster_transitions, pca_explained_variance và pca_loadings trong outputs/tables/. Các hình được lấy từ outputs/figures/.')
p('Quy ước trình bày: Accuracy, Precision, Recall, F1 và AUC trong bảng hiệu quả là tỷ lệ từ 0 đến 1. Các trung bình financial có đơn vị phần trăm; hệ số Logistic và PCA không có đơn vị phần trăm. Làm tròn phục vụ trình bày, không thay đổi output gốc.')
for para in doc.paragraphs[-3:]:
    para.alignment=WD_ALIGN_PARAGRAPH.LEFT

doc.save(OUT)
check=Document(OUT)
assert len(check.tables)==table_count and len(check.inline_shapes)==figure_count
assert table_count==8 and figure_count==5
for name,r in metrics.items():
    assert all(number(r[c]) in '\n'.join(cell.text for t in check.tables for row in t.rows for cell in row.cells) for c in ['Accuracy','Precision','Recall','F1','ROC-AUC'])
audit={'output':str(OUT),'tables':table_count,'figures':figure_count,'manual_page_breaks':0,'sources':{p.name:len(rows) for p in TABLES.glob('*.csv') for rows in [data[p.stem]]},'numeric_checks':'metrics, coefficients, profiles, PCA written directly from CSV; no model retraining'}
(QA/'content_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'file':str(OUT),'tables':table_count,'figures':figure_count},ensure_ascii=False))
