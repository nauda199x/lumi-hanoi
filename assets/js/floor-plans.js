(()=>{
  const bind=(rootSelector,buttonSelector,cardSelector,buttonKey,cardKey)=>{
    const root=document.querySelector(rootSelector); if(!root)return;
    const buttons=[...root.querySelectorAll(buttonSelector)];
    const cards=[...document.querySelectorAll(cardSelector)];
    buttons.forEach(button=>button.addEventListener('click',()=>{
      const value=button.dataset[buttonKey];
      buttons.forEach(item=>{const active=item===button;item.classList.toggle('is-active',active);item.setAttribute('aria-pressed',String(active));});
      cards.forEach(card=>{card.hidden=!(value==='all'||card.dataset[cardKey]===value);});
    }));
  };
  bind('[data-tower-filters]','[data-tower-filter]','[data-tower-card]','towerFilter','phase');
  bind('[data-floor-filters]','[data-floor-filter]','[data-plan]','floorFilter','floor');
})();
