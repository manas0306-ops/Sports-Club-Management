const one=(q,el=document)=>el.querySelector(q);
const all=(q,el=document)=>Array.from(el.querySelectorAll(q));
const currency=n=>new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR'}).format(n/100);
const localDay=()=>new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Kolkata',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
function notify(msg){const box=one('#status');box.textContent=msg;box.hidden=false;clearTimeout(box.timer);box.timer=setTimeout(()=>box.hidden=true,6500)}
document.addEventListener('submit',async e=>{
 const form=e.target,action=form.dataset.action;if(!action)return;e.preventDefault();
 const data=Object.fromEntries(new FormData(form));
 if(one('[data-cart]',form))data.cart=all('[data-sku]',form).filter(i=>Number(i.value)>0).map(i=>({id:Number(i.dataset.sku),qty:Number(i.value)}));
 if(action==='book'&&!data.start){notify('Choose an available court time first.');return}
 if(action==='archive'&&!confirm('Archive this account and end its sessions?'))return;
 const btn=e.submitter;if(btn)btn.disabled=true;
 try{const r=await fetch('/api/'+action,{method:'POST',headers:{'Content-Type':'application/json','X-Club-Request':'1'},body:JSON.stringify(data)});const v=await r.json();if(!r.ok)throw Error(typeof v.detail==='string'?v.detail:'Check the form and try again.');
 if(action==='lead'){form.reset();notify('Request received. The front desk will follow up.');return}
 if(v.redirect)location.assign(v.redirect);else if(v.receipt)location.assign('/receipt/'+v.receipt);else{sessionStorage.setItem('club-message',v.message||'Changes saved.');location.reload()}
 }catch(err){notify(err.message)}finally{if(btn)btn.disabled=false}
});
for(const button of all('[data-login]'))button.onclick=()=>{one('form[data-action=login] [name=email]').value=button.dataset.login;one('form[data-action=login] [name=password]').value='password123'};
for(const cart of all('[data-cart]')){
 const form=cart.closest('form');function estimate(){const tier=one('[data-member]',form)?.selectedOptions[0].dataset.tier||one('input[data-tier]',form)?.dataset.tier||'Free';const pct={Gold:15,Silver:10,Junior:5,Free:0}[tier];let total=0;all('[data-sku]',cart).forEach(i=>{const gross=i.value*i.dataset.price;total+=gross-Math.round(gross*pct/100)});one('[data-estimate]',cart).textContent=currency(total)+' · '+tier+' · '+pct+'% discount'}form.addEventListener('input',estimate);estimate()
}
const search=one('[data-search]');if(search)search.oninput=()=>all('[data-directory] p').forEach(p=>p.hidden=!p.textContent.toLowerCase().includes(search.value.toLowerCase()));
for(const board of all('.board')){
 const day=one('[data-day]',board),week=one('[data-week]',board),dest=one('[data-slots]',board),form=one('form',board);day.value=localDay();let generation=0;
 function choose(c,s,b){if(!form){location.assign('/login');return}all('.slots .active',board).forEach(x=>x.classList.remove('active'));b.classList.add('active');form.elements.court_id.value=c.id;form.elements.start.value=s.start;form.dataset.base=c.price;form.dataset.kind=s.kind;form.dataset.label=c.name+' · '+s.start.replace('T',' ')+' · '+s.kind;quote()}
 function quote(){if(!form?.dataset.label)return;const profile=one('[data-member]',form)?.selectedOptions[0].dataset||document.body.dataset;const tier=profile.expiry&&profile.expiry<form.elements.start.value.slice(0,10)?'Free':profile.tier||'Free';const pct=form.dataset.kind==='Social'?100:({Gold:100,Silver:50,Junior:30}[tier]||0);one('[data-chosen]',form).textContent=form.dataset.label+' · '+currency(form.dataset.base*(100-pct)/100)}
 if(form)form.addEventListener('change',quote);
 async function render(){const seq=++generation;if(form){form.elements.start.value='';form.dataset.label='';one('[data-chosen]',form).textContent='Select an available time above.'}
 try{const query=new URLSearchParams({day:day.value,sport:one('[data-sport]',board).value,kind:one('[data-kind]',board).value});const r=await fetch('/api/availability?'+query);const rows=await r.json();if(seq!==generation)return;if(!r.ok)throw Error(rows.detail);dest.replaceChildren();
 for(const c of rows){const row=document.createElement('div');row.className='slotrow';const title=document.createElement('strong');title.textContent=c.name+' · '+c.kind;row.append(title);const times=document.createElement('div');times.className='slots';for(const s of c.slots){const b=document.createElement('button');b.textContent=s.start.slice(11)+(s.kind==='Social'?' · '+s.left+'/8':'');b.disabled=!s.left;b.title=s.kind+' · '+(s.left?'Available':'Unavailable');b.onclick=()=>choose(c,s,b);times.append(b)}row.append(times);dest.append(row)}if(!rows.length)dest.textContent='No courts match these filters.';all('button',week).forEach(b=>b.classList.toggle('active',b.dataset.date===day.value))
 }catch(err){dest.textContent=err.message}}
 const base=new Date(day.value+'T12:00:00Z');for(let n=0;n<7;n++){const t=new Date(base.getTime()+n*86400000);const b=document.createElement('button');b.dataset.date=t.toISOString().slice(0,10);b.textContent=t.toLocaleDateString('en-GB',{weekday:'short',day:'numeric',timeZone:'UTC'});b.onclick=()=>{day.value=b.dataset.date;render()};week.append(b)}all('.filters input,.filters select',board).forEach(i=>i.onchange=render);render();setInterval(()=>{if(!document.hidden&&!form?.elements.start.value)render()},20000)
}
const kitchen=one('#kitchen');if(kitchen)setInterval(async()=>{if(document.hidden)return;try{const r=await fetch(location.href);if(!r.ok)return;const page=new DOMParser().parseFromString(await r.text(),'text/html');const next=one('#kitchen',page);if(next)kitchen.replaceChildren(...next.childNodes)}catch{}},10000);
window.addEventListener('DOMContentLoaded',()=>{window.lucide?.createIcons();const graph=one('#revenue');if(graph&&window.Chart){const vals=JSON.parse(graph.dataset.values);new Chart(graph,{type:'bar',data:{labels:Object.keys(vals),datasets:[{label:'Net revenue (₹)',data:Object.values(vals).map(x=>x/100),backgroundColor:'#478d71',borderRadius:4}]},options:{maintainAspectRatio:false,plugins:{legend:{display:false}}}})}});
const saved=sessionStorage.getItem('club-message');if(saved){notify(saved);sessionStorage.removeItem('club-message')}if(location.search.includes('registered=1'))notify('Membership created. Sign in with your email.');

const physioDay=one('[data-physio-day]');
if(physioDay){
 const form=physioDay.closest('form'),list=one('[data-physio-slots]',form);let request=0;
 async function updatePhysio(){
  const version=++request;list.replaceChildren();
  try{
   const q=new URLSearchParams({day:physioDay.value,staff_id:form.elements.staff_id.value});
   const response=await fetch('/api/physio/slots?'+q);const times=await response.json();
   if(version!==request)return;if(!response.ok)throw Error(times.detail);
   for(const t of times)list.add(new Option(t.slice(11),t));
   if(!times.length)list.add(new Option('No slots available',''));
  }catch(error){notify(error.message)}
 }
 form.elements.staff_id.onchange=updatePhysio;physioDay.onchange=updatePhysio;updatePhysio();
}
