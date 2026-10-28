"""Tạo notebook có thuyết minh; execute bằng nbclient với Python project."""
import sys
import os
import json
import nbformat as nbf
from nbclient import NotebookClient
from utils import ROOT

def build():
    jupyter=ROOT/'.venv/share/jupyter'
    kernel=jupyter/'kernels/banking-ml'; kernel.mkdir(parents=True,exist_ok=True)
    (kernel/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],'display_name':'Banking ML (.venv)','language':'python'}),encoding='utf-8')
    os.environ['JUPYTER_PATH']=str(jupyter)+os.pathsep+os.environ.get('JUPYTER_PATH','')
    os.environ['IPYTHONDIR']=str(ROOT/'.cache/ipython')
    os.environ['JUPYTER_RUNTIME_DIR']=str(ROOT/'.cache/jupyter-runtime')
    folder=ROOT/'notebooks'; folder.mkdir(exist_ok=True)
    setup="from pathlib import Path\nimport sys\nroot = Path.cwd()\nif not (root / 'src').exists():\n    root = root.parent\nsys.path.insert(0, str(root / 'src'))\nfrom utils import *\nfrom IPython.display import display, Image, Markdown\n"
    specs=[
        ('01_data_validation', 'Kiểm tra chất lượng dữ liệu', [
            ('Objective', 'Đọc dictionary và mọi bảng trước khi huấn luyện. Không sửa dữ liệu gốc. Mẫu là một ngân hàng × quý.'),
            ('Load Data', 'File được tìm theo tên gốc hoặc hậu tố; schema được kiểm tra trực tiếp.'),
            ('code', "display(Markdown(locate('data_dictionary', 'md').read_text(encoding='utf-8-sig')))\nfrom data_validation import run\nd, status = run()\nprint(status)"),
            ('Validate Data', 'Kiểm tra khóa, missing, consistency, sự kiện và nhãn tính từ giá ngày. Dòng CSV bao gồm header.'),
            ('code', "for name in ['dataset_overview','model_missing','target_distribution','event_frequency','validation_issues']:\n    print(name)\n    display(pd.read_csv(TABLES / f'{name}.csv'))"),
            ('Preprocessing và leakage', 'CAR Q4 dự báo lấy Q3 cùng năm theo dictionary. Các cột nhãn, lợi suất tương lai, nguồn và chỉ số đối chiếu bị cấm làm feature. Không điền NaN bằng 0.'),
            ('Interpretation và Conclusion', 'Chỉ READY khi không có lỗi nghiêm trọng. Các hạn chế công bố BCTC và nguồn CAR vẫn phải trình bày.'),
            ('code', "display(Markdown((REPORTS / 'data_readiness_report.md').read_text(encoding='utf-8')))"),
        ]),
        ('02_logistic_regression','Dự báo xu hướng bằng Logistic Regression',[
            ('Objective','So sánh financial only với event tổng quát và event categories. Không chọn tham số trên Test.'),
            ('Load Data và Validate Data','Đọc lại dữ liệu và kiểm tra trước khi fit.'),
            ('code',"from data_validation import run as validate\nd, status = validate()\nassert status == 'READY FOR ML'"),
            ('Preprocessing','Train 2021–2024 (128 mẫu), Test 2025 (32 mẫu). Pipeline scaler chỉ fit Train; event giữ đơn vị cờ/đếm. CAR dự báo xử lý theo dictionary trong bản sao.'),
            ('Model','Dummy most_frequent và Logistic mặc định L2, C=1, max_iter=1000, random_state=42. Model 2A giữ co_su_kien; Model 2B giữ mọi loại và cảnh báo event hiếm.'),
            ('code',"from logistic_model import run\nperformance, coefficients = run(d)\ndisplay(performance)\ndisplay(coefficients)"),
            ('Evaluation và Visualization','Đánh giá cả Accuracy, Precision, Recall, F1, ROC-AUC và confusion matrix; cùng ngưỡng 0.5.'),
            ('code',"for name in ['target_distribution','confusion_matrices','roc_curves','logistic_coefficients']:\n    display(Image(filename=str(FIGURES / f'{name}.png')))"),
            ('Interpretation và Conclusion','Hệ số biểu thị association, không suy luận nhân quả. Event không được scale như financial nên không so trực tiếp hệ số giữa hai nhóm. Với Test nhỏ, chênh lệch nhỏ chưa đủ khẳng định cải thiện ổn định.'),
        ]),
        ('03_kmeans_pca','Phân cụm ngân hàng-quý và PCA',[
            ('Objective','Phân cụm 160 quan sát ngân hàng-quý dựa trên 6 financial. Đây là mô tả toàn kỳ, không phải dự báo.'),
            ('Load Data và Validate Data','Chỉ tiếp tục sau kiểm tra đạt READY.'),
            ('code',"from data_validation import run as validate\nd, status = validate()\nassert status == 'READY FOR ML'"),
            ('Preprocessing','Chuẩn hóa toàn bộ 160 mẫu cho phân cụm mô tả; CAR gốc giữ nguyên. Không thêm target/event vào K-Means.'),
            ('Model','K=2..6; random_state=42, n_init=auto. Chọn silhouette lớn nhất, đối chiếu inertia và khả năng diễn giải profile. PCA dùng đúng ma trận standardized của K-Means.'),
            ('code',"from clustering import run\nscores, k, profile, variance, loadings, bank = run(d)\nprint('Chosen K:', k)\nfor table in [scores, profile, variance, loadings, bank]:\n    display(table)"),
            ('Evaluation và Visualization','Điểm PCA là ngân hàng-quý; màu là cụm. Hình 2D chỉ giữ một phần phương sai.'),
            ('code',"for name in ['k_selection','cluster_distribution','pca_scatter']:\n    display(Image(filename=str(FIGURES / f'{name}.png')))"),
            ('Interpretation và Conclusion','Đặt tên bằng các độ lệch tương đối lớn nhất sau khi tính profile; không gán nhãn tốt/xấu. Loadings là pca.components_; dấu PC tùy quy ước. Xem bảng ngân hàng, thời gian và chuyển cụm để phân tích sâu.'),
        ])]
    for filename,title,sections in specs:
        notebook=nbf.v4.new_notebook()
        notebook.cells=[nbf.v4.new_markdown_cell(f'# {title}'),nbf.v4.new_code_cell(setup)]
        for heading,body in sections:
            notebook.cells.append(nbf.v4.new_code_cell(body) if heading=='code' else nbf.v4.new_markdown_cell(f'## {heading}\n\n{body}'))
        notebook.metadata.kernelspec={'display_name':'Banking ML (.venv)','language':'python','name':'banking-ml'}
        path=folder/f'{filename}.ipynb'
        nbf.write(notebook,path)
        client=NotebookClient(notebook,timeout=180,resources={'metadata':{'path':str(ROOT)}},kernel_name='banking-ml')
        client.execute()
        nbf.write(notebook,path)
        print('Executed:',path.name)

if __name__=='__main__':
    build()
