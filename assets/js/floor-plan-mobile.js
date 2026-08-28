(() => {
  const mobileQuery = window.matchMedia('(max-width: 700px)');

  const enhancePicker = (picker) => {
    if (picker.dataset.mobilePickerReady === 'true') return;

    const links = [...picker.querySelectorAll(':scope > a[href^="#"]')];
    if (!links.length) return;

    picker.dataset.mobilePickerReady = 'true';
    picker.dataset.mobileOpen = 'false';

    const button = document.createElement('button');
    button.className = 'mobile-floor-toggle';
    button.type = 'button';
    button.setAttribute('aria-expanded', 'false');
    button.innerHTML = '<span class="mobile-floor-label"></span><span class="mobile-floor-chevron" aria-hidden="true"></span>';

    const heading = picker.querySelector(':scope > strong');
    heading?.insertAdjacentElement('afterend', button);
    if (!heading) picker.prepend(button);

    const label = button.querySelector('.mobile-floor-label');
    const setCurrent = (link) => {
      links.forEach((item) => item.classList.toggle('is-current', item === link));
      label.textContent = `Chọn mặt bằng tầng · ${link.textContent.trim()}`;
    };
    const close = () => {
      picker.dataset.mobileOpen = 'false';
      button.setAttribute('aria-expanded', 'false');
    };
    const syncFromHash = () => {
      const current = links.find((link) => link.hash === window.location.hash) || links[0];
      setCurrent(current);
    };

    button.addEventListener('click', () => {
      const willOpen = picker.dataset.mobileOpen !== 'true';
      picker.dataset.mobileOpen = String(willOpen);
      button.setAttribute('aria-expanded', String(willOpen));
    });

    links.forEach((link) => {
      link.addEventListener('click', () => {
        setCurrent(link);
        close();
      });
    });

    window.addEventListener('hashchange', syncFromHash);
    mobileQuery.addEventListener('change', close);
    syncFromHash();
  };

  const enhanceAll = (root = document) => {
    root.querySelectorAll?.('.tower-floor-index').forEach(enhancePicker);
  };

  enhanceAll();

  document.querySelectorAll('[data-floor-plan-app]').forEach((app) => {
    new MutationObserver(() => enhanceAll(app)).observe(app, { childList: true });
  });
})();
