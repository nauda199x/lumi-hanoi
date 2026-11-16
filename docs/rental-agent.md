# Tiếp nhận khách thuê Lumi

- Trang khách: `/tim-can-thue-lumi/`. Trang vận hành: `/admin/khach-thue/`, dùng quyền quản trị marketplace hiện có.
- Nguồn căn: tin thuê công khai đã duyệt, còn hiệu lực, gắn số liên hệ của Đức. Giá và tình trạng phải xác nhận trước khi hẹn.
- Kênh: gắn `utm_source`, `utm_medium`, `utm_campaign` khi chia sẻ. Ví dụ `/tim-can-thue-lumi/?loai=2PN&utm_source=facebook&utm_medium=organic_social&utm_campaign=lumi_2pn`. Khi rao một căn, có thể thêm `can` là slug của tin.
- Sự kiện GA4: `rental_agent_search`, `rental_agent_zalo_click`, `generate_lead` với `lead_surface=lumi_rental_agent`. Đếm lead ở lần ghi thành công đầu tiên. Trạng thái đã liên hệ, đã hẹn, đã xem và đã thuê được cập nhật trong hộp khách thuê.
- Kiểm tra: `node --test scripts/qa_rental_agent.mjs`. Endpoint `lumi-rental-agent` tự kiểm tra khóa công khai của site và chỉ cho phép các origin của lumi-hanoi.com. Khóa máy chủ và số liên hệ khách không nằm trong frontend công khai.
- Với môi trường mới, áp dụng `supabase/rental-agent.sql`, rồi triển khai `supabase/functions/lumi-rental-agent`. Cấu hình `LUMI_RENTAL_AI_KEY` để bật mô hình trích xuất tùy chọn, mặc định `gpt-4o-mini` (đổi qua `LUMI_RENTAL_AI_MODEL`). Có giới hạn 250 lượt AI/ngày và fallback đọc từ khóa Việt/Anh. Dịch vụ chỉ gửi đoạn mô tả đã che số liên hệ và email cho mô hình.
- `LUMI_RENTAL_ALERT_URL` là webhook tùy chọn nhận JSON `{"text":"…"}`. Webhook chỉ nhận loại căn, ngân sách và link quản trị. Hộp khách thuê luôn lưu yêu cầu trước khi thử gửi thông báo. Cron xóa lead sau 90 ngày.
