(()=>{
  const button=document.querySelector('[data-nav-toggle]');
  const nav=document.querySelector('[data-nav-links]');
  if(button&&nav){
    button.addEventListener('click',()=>{
      const open=nav.getAttribute('data-open')==='true';
      nav.setAttribute('data-open',String(!open));
      button.setAttribute('aria-expanded',String(!open));
    });
    nav.querySelectorAll('a').forEach(link=>link.addEventListener('click',()=>{
      nav.setAttribute('data-open','false');
      button.setAttribute('aria-expanded','false');
    }));
  }
  document.querySelectorAll('[data-year]').forEach(el=>{el.textContent=new Date().getFullYear();});
})();
