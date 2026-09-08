<div class="ld-page" data-detail-content {{content_hidden}}>
  <div class="ld-topline">
    <a class="ld-back" data-detail-back href="{{category_url}}"><span aria-hidden="true">←</span> <span data-detail-category>{{category}}</span></a>
    <div class="ld-actions" data-detail-actions hidden>
      <button class="ld-action" type="button" data-detail-share><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M12 16V3m-5 5 5-5 5 5M5 13v7h14v-7"/></svg>Chia sẻ</button>
      <button class="ld-action" type="button" data-detail-save aria-pressed="false" title="Lưu tin trên thiết bị này"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M6 3h12v18l-6-4-6 4z"/></svg><span data-save-label>Lưu tin</span></button>
    </div>
  </div>
  <header class="ld-heading">
    <div class="ld-meta"><span class="ld-badge" data-detail-type>{{action}}</span><span data-detail-code>{{code}}</span><span data-detail-date-wrap {{date_hidden}}>Đăng ngày <time data-detail-date datetime="{{posted}}">{{posted_label}}</time></span></div>
    <h1 class="ld-title" data-detail-title>{{title}}</h1>
    <p class="ld-address"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z"/><circle cx="12" cy="10" r="2.5"/></svg><span>Lumi Hanoi · <span data-detail-phase>{{phase}}</span> · Tòa <span data-detail-tower>{{tower}}</span><span class="ld-address-area"> — Tây Mỗ, Hà Nội</span></span></p>
  </header>
  <div class="ld-status" data-live-status role="status" hidden></div>
  <div class="ld-layout">
    <div class="ld-main">
      <section class="ld-gallery" data-detail-gallery aria-label="Hình ảnh tin đăng">{{gallery}}</section>
      <div class="ld-mobile-price"><span>Giá <span data-detail-price-label>{{price_label}}</span></span><strong data-detail-price>{{price}}</strong><small data-detail-price-per-sqm>{{price_per_sqm}}</small></div>
      <dl class="ld-facts" aria-label="Thông tin chính">
        <div><dt>Diện tích</dt><dd data-detail-area>{{area}}</dd></div>
        <div><dt>Loại căn</dt><dd data-detail-unit>{{unit}}</dd></div>
        <div><dt>Tòa</dt><dd data-detail-tower>{{tower}}</dd></div>
        <div><dt>Tầng</dt><dd data-detail-floor>{{floor}}</dd></div>
      </dl>
      <nav class="ld-sections" aria-label="Nội dung tin đăng"><a href="#mo-ta">Mô tả</a><a href="#dac-diem">Đặc điểm</a><a href="#vi-tri">Vị trí & mặt bằng</a><a href="#lien-he">Liên hệ</a></nav>
      <section class="ld-section" id="mo-ta" aria-labelledby="ld-description-title">
        <h2 id="ld-description-title">Thông tin mô tả</h2>
        <div class="ld-description" id="ld-description" data-detail-description>{{description}}</div>
        <button class="ld-text-button" type="button" data-detail-readmore aria-expanded="false" aria-controls="ld-description" hidden>Xem đầy đủ mô tả <span aria-hidden="true">↓</span></button>
      </section>
      <section class="ld-section" id="dac-diem" aria-labelledby="ld-features-title">
        <h2 id="ld-features-title">Đặc điểm bất động sản</h2>
        <dl class="ld-features">
          <div><dt>Mức giá</dt><dd data-detail-price>{{price}}</dd></div><div><dt>Diện tích</dt><dd data-detail-area>{{area}}</dd></div>
          <div><dt>Loại căn</dt><dd data-detail-unit>{{unit}}</dd></div><div><dt>Tầng</dt><dd data-detail-floor>{{floor}}</dd></div>
          <div><dt>Phân khu</dt><dd data-detail-phase>{{phase}}</dd></div><div><dt>Tòa</dt><dd data-detail-tower>{{tower}}</dd></div>
          <div class="ld-feature-wide"><dt>Nội thất</dt><dd data-detail-furnishing>{{furnishing}}</dd></div>
          <div class="ld-feature-wide"><dt>Mã tin</dt><dd data-detail-code>{{code}}</dd></div>
        </dl>
      </section>
      <section class="ld-section" id="vi-tri" aria-labelledby="ld-location-title">
        <h2 id="ld-location-title">Vị trí & mặt bằng</h2>
        <div class="ld-location-card"><div><span class="ld-label">Lumi Hanoi</span><h3>Tòa <span data-detail-tower>{{tower}}</span> · <span data-detail-phase>{{phase}}</span></h3><p>Đại lộ Thăng Long, Tây Mỗ, Hà Nội</p></div><a class="ld-button ld-button-outline" href="https://www.google.com/maps/search/?api=1&query=Lumi+Hanoi" target="_blank" rel="noopener">Mở bản đồ <span aria-hidden="true">↗</span></a></div>
        <nav class="ld-links" aria-label="Tra cứu căn hộ"><a data-detail-floorplan href="{{floorplan_url}}"><span>Mặt bằng tòa <b data-detail-tower>{{tower}}</b></span><span aria-hidden="true">↗</span></a><a data-detail-same-tower href="{{same_tower_url}}"><span>Tin <span data-detail-price-label>{{price_label}}</span> cùng tòa</span><span aria-hidden="true">→</span></a><a data-detail-same-unit href="{{same_unit_url}}"><span>Xem thêm căn <b data-detail-unit>{{unit}}</b></span><span aria-hidden="true">→</span></a><a data-detail-unit-guide href="{{unit_url}}" {{unit_guide_hidden}}><span>Tìm hiểu căn <b data-detail-unit>{{unit}}</b> Lumi Hanoi</span><span aria-hidden="true">↗</span></a></nav>
      </section>
      <p class="ld-disclaimer">Thông tin do người đăng cung cấp. Vui lòng kiểm tra hiện trạng căn và hồ sơ trước khi giao dịch.</p>
    </div>
    <aside class="ld-aside" id="lien-he" aria-label="Giá và liên hệ người đăng">
      <div class="ld-panel">
        <div class="ld-price-block"><span class="ld-label">Giá <span data-detail-price-label>{{price_label}}</span></span><strong class="ld-price" data-detail-price>{{price}}</strong><span class="ld-price-per-sqm" data-detail-price-per-sqm>{{price_per_sqm}}</span><div class="ld-panel-facts"><span data-detail-area>{{area}}</span><span data-detail-unit>{{unit}}</span><span>Tòa <b data-detail-tower>{{tower}}</b></span></div></div>
        <div class="ld-panel-body">
          <div class="ld-poster"><span class="ld-avatar" data-detail-avatar aria-hidden="true">{{initials}}</span><div><span class="ld-label">Người đăng tin</span><strong data-detail-poster>{{poster}}</strong></div></div>
          <div class="ld-contact"><a class="ld-button ld-button-primary" data-detail-phone href="{{phone_url}}" {{phone_hidden}}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="m7 3 3 5-2 2a15 15 0 0 0 6 6l2-2 5 3c-1 4-3 5-6 3A24 24 0 0 1 4 9C2 6 3 4 7 3Z"/></svg><span><small>Gọi người đăng</small><b data-phone-label>{{phone}}</b></span></a><a class="ld-button ld-button-outline" data-detail-zalo href="{{zalo_url}}" target="_blank" rel="noopener" {{phone_hidden}}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M21 11a9 9 0 0 1-9 9H3l2-5a9 9 0 1 1 16-4Z"/><path d="M8 10h8m-8 4h5"/></svg>Nhắn Zalo</a></div>
          <p class="ld-contact-empty" data-contact-empty {{contact_empty_hidden}}>Người đăng chưa cung cấp số liên hệ.</p>
          <p class="ld-contact-note">Liên hệ để xác nhận tình trạng căn và hẹn lịch xem.</p>
          <details class="ld-report" data-report-box {{report_hidden}}><summary>Báo tin sai hoặc đã giao dịch</summary><form data-report-form><label for="report-reason">Lý do</label><select id="report-reason" name="reason" required><option value="already_done">Đã bán / đã cho thuê</option><option value="wrong_info">Thông tin không đúng</option><option value="cannot_contact">Không liên hệ được</option><option value="other">Lý do khác</option></select><label for="report-details">Ghi chú</label><textarea id="report-details" name="details" rows="3" maxlength="600"></textarea><button class="ld-button ld-button-outline" type="submit">Gửi báo cáo</button><p data-report-status role="status"></p></form></details>
        </div>
      </div>
    </aside>
  </div>
  <div class="ld-mobile-contact" data-detail-mobile-contact {{phone_hidden}}><div class="ld-dock-price"><span>Giá <span data-detail-price-label>{{price_label}}</span></span><strong data-detail-price>{{price}}</strong></div><a class="ld-button ld-button-outline" data-detail-zalo href="{{zalo_url}}" target="_blank" rel="noopener" {{phone_hidden}}>Zalo</a><a class="ld-button ld-button-primary" data-detail-phone data-phone-compact href="{{phone_url}}" aria-label="Gọi người đăng" {{phone_hidden}}>Gọi ngay</a></div>
  <p class="ld-toast" data-detail-toast role="status" hidden></p>
  <div class="ld-share-fallback" data-share-fallback hidden><label for="listing-share-link">Sao chép đường dẫn tin đăng</label><input id="listing-share-link" readonly data-share-link><button class="ld-text-button" type="button" data-share-close>Đóng</button></div>
</div>
