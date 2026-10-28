# Đánh giá bộ dữ liệu bàn giao cho Quân và Nghi

Ngày kiểm tra: 03/10/2026. Phạm vi: tài liệu `Nhóm 5_PTDL (1).docx`, sáu bảng CSV trong `data/output`, năm bản Excel tương ứng, Data Dictionary, mã pipeline, cache tài chính và các file rà soát/thử nghiệm. Đây là đánh giá dữ liệu và phương pháp; không chỉnh sửa dataset.

**Kết luận:** phần thu thập và làm sạch tài chính, giá đã đủ tốt để bàn giao cho Nghi và để Quân bắt đầu làm mô hình. Chưa nên gọi toàn bộ bộ dữ liệu là bản cuối hoàn chỉnh cho thí nghiệm sự kiện. Hai việc cần chốt là rà soát bổ sung sự kiện trong phạm vi hữu hạn và thống nhất cách sử dụng CAR. Không có căn cứ phải làm lại toàn bộ pipeline hoặc sửa số liệu chỉ vì số đó khác thường.

## Kết quả kiểm tra trực tiếp

| Nội dung | Kết quả |
|---|---|
| Bảng 4 | 160 dòng × 56 cột; đúng 8 ngân hàng × 20 quý |
| Khóa các bảng quý | Không trùng `ma_nh + quy + nam`; mỗi ngân hàng đủ 20 quý |
| Giá ngày | 10.851 dòng; không trùng `ma_nh + ngay`; không thiếu biến số hoặc giá trị vô hạn |
| Độ phủ biến số | Không có ô thiếu trong các bảng đầu ra được kiểm tra |
| Ô mô tả sự kiện trống | 72 quý không ghi nhận sự kiện; bốn cột mô tả cùng trống đúng các quý này |
| Ghép bảng | Từng cột của Bảng 1, 2b, 3b khớp Bảng 4 theo khóa |
| CSV và Excel | Cả năm cặp có cùng kích thước và cùng giá trị |
| Data Dictionary | Có mục giải thích cho mọi cột của cả sáu bảng |
| Tính lại giá quý và nhãn | Khớp dữ liệu xuất; sai khác số liên tục chỉ do làm tròn bốn chữ số; nhãn khớp hoàn toàn |
| Tính lại tài chính từ cache | Khớp số liệu xuất trong sai số làm tròn |
| Tổng LNST 4 quý so với năm | Chênh lệch tuyệt đối tương đối lớn nhất khoảng 1,726%; không có trường hợp vượt 2% |
| Giá mở/đóng so với cao/thấp | Không phát hiện trường hợp nằm ngoài khoảng giá phiên |
| Biến sự kiện | `co_su_kien` khớp số đếm; tổng `sk_*` khớp `so_luong_su_kien` |
| Nhãn dự báo | 90 tăng, 70 không tăng; không có nhãn trống |

ACB thiếu năm ngày giá so với các mã khác, nhưng đều là 02–08/12/2020, ngoài phạm vi phân tích 2021–2025; có giá cuối quý trước để tính Q1/2021. Không cần bịa thêm phiên để các mã có cùng số dòng.

## Hai việc cần chốt

### Sự kiện còn bỏ sót và cần một lượt rà soát có giới hạn

Bảng 3a hiện có 121 sự kiện: 61 tăng vốn, 33 đổi lãnh đạo, 15 hợp tác, 4 chuyển đổi số, 2 chính sách NHNN và 6 khác. Chuyển đổi số không có quan sát nào ở năm 2021 và 2023. Đây chưa phải bằng chứng ngân hàng không có hoạt động chuyển đổi số trong những năm đó; nó phản ánh những gì bộ nguồn và quy tắc hiện tại ghi nhận được.

Đã có công sức rà soát thực sự: file thủ công ghi 63 dòng loại bỏ, 7 dòng sửa loại và 1 dòng bổ sung. Tuy vậy, còn một bộ ứng viên Vietstock: **75 dòng sau gộp**, còn cột `danh_gia` trống toàn bộ. Báo cáo thử nghiệm nói 80 tin mới trước gộp và dùng mốc 120 sự kiện cũ; dataset hiện tại có 121. Vì vậy số dự kiến đổi 21 quý từ 0 sang 1 trong báo cáo thử nghiệm là kết quả ở thời điểm thử nghiệm, cần tính lại nếu dùng cho bản cuối.

Một ví dụ bỏ sót được xác nhận: MBB Q1/2021 đang có `sk_hop_tac_trung_thau = 0`, nhưng MB và VNVC có ký kết hợp tác chiến lược ngày 03/02/2021. [Nguồn VNVC](https://vnvc.vn/hop-tac/ky-ket-hop-tac-chien-luoc-voi-ngan-hang-quan-doi-mb/), [nguồn MB](https://news.mbbank.com.vn/news/mb-ky-ket-hop-tac-chien-luoc-voi-he-thong-trung-tam-tiem-chung-vnvc-1640568810). Cần tìm ngày công bố sớm nhất có bằng chứng khi ghi sự kiện; ngày ký và ngày đăng không tự động là một.

Không nhập cả 75 ứng viên tự động. Trong đó có tiêu đề về phát biểu mong muốn số hóa thủ tục hành chính, giải thưởng chuyển đổi số, hoặc dự kiến tổ chức họp bầu nhân sự; các tin này chưa chắc là sự kiện mới theo quy tắc nhóm đang dùng.

Việc nên làm một lần: đánh dấu giữ/bỏ/trùng cho 75 ứng viên, bổ sung những tin được xác nhận, rà soát nhất quán ngày công bố và nhóm sự kiện, rồi chạy lại đầu ra và chốt phiên bản. Không cần mở rộng vô hạn sang mọi trang báo. Có thể bàn giao bản hiện tại để Nghi và Quân bắt đầu, nhưng trước khi Quân so sánh mô hình có/không có sự kiện thì cần chốt lượt này.

`co_su_kien = 0` nên được hiểu là **không ghi nhận sự kiện phù hợp trong nguồn và quy tắc thu thập**, không phải bảo đảm ngoài thực tế không có sự kiện. Một tin hợp tác công nghệ được gán duy nhất vào hợp tác thay vì đồng thời chuyển đổi số là lựa chọn mã hóa, miễn quy tắc nhất quán và được công bố.

### CAR cần phân biệt số của kỳ và thông tin đã biết tại thời điểm dự báo

Trong 160 dòng, chỉ 32 dòng CAR là số nguồn có theo kỳ hoặc tra thủ công; 128 dòng điền tiếp. Dataset không có số CAR thật của năm 2025. Giá trị CAR năm 2025 hiện phản ánh số trước đó, không nên được trình bày thành CAR đo được năm 2025.

File thủ công cũng đang trộn phạm vi: BID 2022 là riêng lẻ, BID 2023–2024 là hợp nhất; CTG 2022–2024 ghi `khong_ro`. Cột `loai_car` mới nằm trong file thủ công, chưa có trong Bảng 4. Đó là hạn chế so sánh cần nói rõ khi Nghi kiểm định CAR.

Vấn đề thời điểm: hướng dẫn trong Data Dictionary đề nghị Q4 dùng CAR của Q3, nhưng như vậy chưa đủ cho những số được lấy từ nguồn công bố rất muộn. Nguồn MBS đang dùng cho CTG 2023 và 2024 xuất bản **08/10/2025**, xác nhận CAR 9,3% và 9,6% ở trang 10. [Báo cáo MBS](https://mbs.com.vn/files/uploads/2025/10/CTG_UPDATE_20251008.pdf). Nguồn đó hỗ trợ đối chiếu lịch sử, nhưng tự nó không chứng minh thị trường đã biết những số này vào mốc dự báo năm 2024. CTG Q1/2023 đang dùng CAR 8,9%, trong khi file thủ công ghi nguồn KBSV ngày 25/09/2023; lượt kiểm tra này không tải được PDF KBSV để xác minh độc lập.

**Phương án chốt ít công nhất:** giữ CAR trong bộ thống kê với ghi chú phạm vi/nguồn; Quân loại CAR khỏi mô hình dự báo chính. Nếu cần mô hình có CAR, phải bổ sung ngày công bố có bằng chứng và ghép giá trị theo ngày thực sự đã biết. Không chỉ lùi một quý rồi khẳng định đã loại hết rò rỉ.

Với Nghi, không coi 128 dòng điền tiếp là 128 lần đo độc lập. Phân tích CAR nên dùng các số có theo kỳ, ghi rõ năm/phạm vi, và kiểm tra độ nhạy khi loại các số riêng lẻ hoặc chưa rõ phạm vi.

## Các giá trị khác thường không đồng nghĩa dữ liệu sai

- `du_phong_cho_vay` âm ở 160 dòng: đúng quy ước khoản trừ khỏi dư nợ. Không đổi dấu tùy ý.
- `chi_phi_du_phong` âm ở 5 dòng: có thể phản ánh hoàn nhập; cần đối chiếu khi diễn giải, không thay bằng 0.
- STB Q4/2025 có LNST khoảng **−2.752,462 tỷ đồng** và chi phí dự phòng **9.232,152 tỷ đồng**. Số liệu khớp cache nguồn; đối chiếu tổng năm không cho thấy lỗi cộng lũy kế. Điều này chưa thay thế việc xác minh với BCTC gốc nếu muốn giải thích nguyên nhân kinh doanh, nhưng không có căn cứ xóa dòng chỉ vì lỗ.
- VPB Q1/2022 có ROA năm hóa khoảng 6,418%; NIM VPB và LDR một số quý cao hơn ngưỡng cảnh báo. Ngưỡng do pipeline đặt ra là cờ rà soát, không phải tiêu chuẩn để ép dữ liệu về một khoảng.
- `ldr` được tính bằng dư nợ cho vay khách hàng / tiền gửi khách hàng. Không diễn giải giá trị trên 100% thành vi phạm giới hạn pháp lý; đây là tỷ số theo công thức dataset, chưa phải phép tính quản lý của NHNN.
- `no_xau` là ước tính từ NPL × dư nợ, không phải thêm một số công bố độc lập. ROA/ROE/NIM là năm hóa từ một quý, không đồng nhất với chỉ số TTM.

## Hướng dẫn sử dụng nên kèm theo bàn giao

Cho Nghi: đọc `mo_ta_du_lieu.md` và Data Dictionary; dùng đúng đơn vị và phương pháp chỉ số; lọc giá ngày về 2021–2025 khi trình bày phạm vi đề tài; phân biệt CAR đo được với CAR điền tiếp. Cách xử lý các quý lặp lại cùng ngân hàng trong kiểm định thuộc phần phương pháp thống kê của Nghi.

Cho Quân: 56 cột là dữ liệu bàn giao tổng hợp, không phải 56 biến đầu vào. Chọn một tập nhỏ từ ROA, ROE, NIM, NPL, LDR và các nhóm sự kiện, chuẩn hóa trong tập huấn luyện và chia theo thời gian, giữ các ngân hàng của cùng quý ở cùng phía train/test. Không đưa `ty_suat_sinh_loi_quy_sau` hay `xu_huong_quy_sau` vào đầu vào. Không dùng đồng thời toàn bộ tổng số sự kiện, cờ có sự kiện và mọi cột nhóm mà không kiểm tra quan hệ phụ thuộc. Đây là việc lựa chọn biến của Quân, không phải lý do xóa các cột hữu ích khỏi dataset.

Nhãn đã được căn từ cuối quý +45 ngày đến mốc tương ứng quý tiếp theo, đúng định nghĩa trong đề xuất. Tuy nhiên ngày VNDirect nhập lần đầu chỉ là một dấu hiệu về độ trễ. Cache có `modifiedDate` sau mốc dự báo ở nhiều kỳ; không chứng minh số liệu đã thay đổi về giá trị, nhưng cũng không đủ để khẳng định dữ liệu là bản nguyên trạng mà thị trường biết khi đó. Data Dictionary đã có ghi hạn chế bản BCTC sau cùng; nên giữ ghi chú này trong báo cáo ML, không cần xây lại kho dữ liệu lịch sử cho phạm vi bài môn học.

## Điều kiện để ngừng sửa và chốt

1. Hoàn tất lượt rà soát 75 ứng viên sự kiện đã có, ghi lại quyết định và tính lại số liệu đầu ra.
2. Thống nhất CAR chỉ dùng mô tả/kiểm định có điều kiện và không dùng trong mô hình chính, hoặc bổ sung dữ liệu ngày công bố nếu quyết định dùng.
3. Xuất lại CSV và Excel cùng lần, ghi phiên bản/ngày chốt; gửi kèm Bảng 4, các bảng thành phần, Data Dictionary và lưu ý sử dụng.

Sau đó chỉ sửa nếu phát hiện lỗi nguồn, công thức, mã ngân hàng, ngày hoặc phân loại cụ thể có bằng chứng. Không sửa vì mô hình đạt accuracy thấp, kiểm định không có ý nghĩa, phân cụm chưa đẹp hoặc xuất hiện một giá trị khác thường. Những kết quả đó không tự chứng minh phần thu thập/làm sạch có lỗi.

Các phép kiểm tra trên xác nhận tính đầy đủ cấu trúc, nhất quán và khả năng tính lại từ cache. Không phải xác minh từng ô tài chính với từng PDF gốc hoặc đọc toàn văn tất cả bài báo.
