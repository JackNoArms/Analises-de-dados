/* Atlas Educação — dashboard offline-first, sem bibliotecas de gráficos.
 * As medidas são percentuais publicados pelo INEP; não agregue municípios.
 */
'use strict';
const $ = id => document.getElementById(id);
const fmt = value => Number(value).toLocaleString('pt-BR',{minimumFractionDigits:1,maximumFractionDigits:1}) + '%';
const int = value => Number(value).toLocaleString('pt-BR');
const normalize = v => String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('pt-BR');
const levels = ['Ensino fundamental','Anos iniciais','Anos finais','Ensino médio'];
const state = {geos:[],cities:[],manifest:null,step:levels[0],uf:'',region:'Todas',search:''};

function parseCSV(text) {
  const rows=[];let cell='',row=[],quoted=false;
  for(let i=0;i<text.length;i++){
    const c=text[i];
    if(c==='"'){
      if(quoted&&text[i+1]==='"'){cell+='"';i++;}
      else quoted=!quoted;
    } else if(c===','&&!quoted){row.push(cell);cell='';}
    else if((c==='\n'||c==='\r')&&!quoted){
      if(c==='\r'&&text[i+1]==='\n')i++;
      row.push(cell);if(row.some(v=>v.length))rows.push(row);row=[];cell='';
    } else cell+=c;
  }
  if(cell||row.length){row.push(cell);rows.push(row);}
  if(rows.length<2)throw new Error('CSV vazio ou inválido');
  const heads=rows.shift().map(x=>x.replace(/^\uFEFF/,''));
  return rows.map(vals=>Object.fromEntries(heads.map((name,i)=>[name,vals[i]??''])));
}
function record(type,stage){return state.geos.find(x=>x.nivel===type&&x.etapa===stage);}
function usableGeo(){
  return state.geos.filter(x=>x.nivel==='UF'&&x.etapa===state.step&&(state.region==='Todas'||x.regiao===state.region));
}
function usableCities(){
  return state.cities.filter(x=>x.etapa===state.step&&(state.region==='Todas'||x.regiao===state.region)&&(!state.uf||x.uf===state.uf));
}
function clear(element){element.replaceChildren();}
function add(tag,parent,cls='',value){
  const el=document.createElement(tag);if(cls)el.className=cls;
  if(value!==undefined)el.textContent=value;parent.append(el);return el;
}
function renderBars(container,rows,{reference=null,city=false}={}){
  clear(container);
  if(!rows.length){add('div',container,'chart-empty','Sem dados válidos para os filtros selecionados.');return;}
  const bars=add('div',container,'bars');
  rows.forEach(item=>{
    const percentage=Number(item.percentual_n1_n2);
    const tr=add('div',bars,'bar-row'+(state.uf&&item.uf===state.uf?' is-selected':''));
    const label=city?item.municipio:item.geografia;
    const name=add('span',tr,'bar-name',label);name.title=label;
    const track=add('div',tr,'bar-track');
    const fill=add('div',track,'bar-fill');fill.style.width=percentage+'%';
    if(reference!==null){const ref=add('div',track,'bar-ref');ref.style.setProperty('--ref',reference+'%');}
    const val=add('span',tr,'bar-value',fmt(percentage));
    tr.title=label+': '+fmt(percentage);
    val.setAttribute('aria-label',label+': '+fmt(percentage));
  });
}
function renderRegions(rows){
  const el=$('regionChart');clear(el);
  const reg=new Map();
  rows.forEach(x=>{const v=reg.get(x.regiao)||[];v.push(Number(x.percentual_n1_n2));reg.set(x.regiao,v);});
  const aggregate=[...reg.entries()].map(([name,values])=>({name,value:values.reduce((a,b)=>a+b,0)/values.length,ufCount:values.length})).sort((a,b)=>b.value-a.value);
  if(!aggregate.length){add('div',el,'chart-empty','Nenhuma região com valores válidos.');return;}
  aggregate.forEach(region=>{
    const line=add('div',el,'region-item');
    add('span',line,'',region.name);
    const track=add('div',line,'region-track');
    const fill=add('div',track,'region-fill');fill.style.width=region.value+'%';
    const label=add('strong',line,'',fmt(region.value));
    label.title='Média simples de '+region.ufCount+' UFs, não o indicador agregado da região';
  });
}
function render(){
  const national=record('Brasil',state.step);
  const ref=national?Number(national.percentual_n1_n2):null;
  const ufs=usableGeo().sort((a,b)=>Number(b.percentual_n1_n2)-Number(a.percentual_n1_n2));
  const cityRows=usableCities();
  const selected=ufs.find(x=>x.uf===state.uf);
  $('national').textContent=ref===null?'—':fmt(ref);
  $('stateValue').textContent=selected?fmt(selected.percentual_n1_n2):'—';
  $('stateLabel').textContent=selected?selected.geografia+' · indicador oficial da UF':'Selecione uma UF para comparar';
  $('cityCount').textContent=int(cityRows.length);
  $('cityLabel').textContent='Municípios com dados válidos na etapa selecionada';
  $('refTag').textContent=ref===null?'Sem referência':'┊ Brasil: '+fmt(ref);
  renderBars($('stateChart'),ufs,{reference:ref});
  renderRegions(ufs);
  const filtered=cityRows.filter(x=>normalize(x.municipio).includes(normalize(state.search)));
  const preview=(state.search?filtered.sort((a,b)=>a.municipio.localeCompare(b.municipio,'pt-BR')):filtered.sort((a,b)=>Number(b.percentual_n1_n2)-Number(a.percentual_n1_n2))).slice(0,12);
  renderBars($('cityChart'),preview,{city:true});
  $('citiesHeading').textContent=state.uf?('Municípios de '+(selected?selected.geografia:state.uf)):'Municípios em destaque';
  if(selected&&ref!==null){
    const diff=Number(selected.percentual_n1_n2)-ref;
    $('insightText').textContent=selected.geografia+' registra '+fmt(selected.percentual_n1_n2)+' em '+state.step.toLowerCase()+' — diferença de '+Math.abs(diff).toLocaleString('pt-BR',{maximumFractionDigits:1})+' ponto(s) percentual(is) '+(diff>=0?'acima':'abaixo')+' do Brasil ('+fmt(ref)+'). Esta comparação é descritiva, não causal.';
  }else if(ufs.length&&ref!==null){
    const high=ufs[0],low=ufs[ufs.length-1];
    $('insightText').textContent='No recorte '+state.step.toLowerCase()+', o valor nacional oficial é '+fmt(ref)+'. Entre as UFs exibidas, a faixa observada vai de '+fmt(low.percentual_n1_n2)+' ('+low.geografia+') a '+fmt(high.percentual_n1_n2)+' ('+high.geografia+'). Nenhum desses extremos determina qualidade pedagógica.';
  }else $('insightText').textContent='Altere os filtros para explorar observações disponíveis.';
  $('status').textContent=int(ufs.length)+' UFs · '+int(cityRows.length)+' municípios com observação válida · 2022';
}
function updateStateOptions(){
  const uf=$('uf');clear(uf);let all=state.geos.filter(x=>x.nivel==='UF'&&x.etapa===levels[0]);
  if(state.region!=='Todas')all=all.filter(x=>x.regiao===state.region);
  all.sort((a,b)=>a.geografia.localeCompare(b.geografia,'pt-BR'));
  let opt=add('option',uf,'','Todas as UFs');opt.value='';
  all.forEach(x=>{const item=add('option',uf,'',x.geografia);item.value=x.uf;});
  if(!all.some(x=>x.uf===state.uf))state.uf='';
  uf.value=state.uf;
}
function bind(){
  const etapa=$('etapa');clear(etapa);
  levels.forEach(level=>{const option=add('option',etapa,'',level);option.value=level;});
  etapa.value=state.step;
  const region=$('regiao');clear(region);
  ['Todas',...new Set(state.geos.filter(x=>x.nivel==='UF').map(x=>x.regiao))].forEach(name=>{
    const option=add('option',region,'',name==='Todas'?'Todas as regiões':name);option.value=name;
  });region.value=state.region;updateStateOptions();
  etapa.addEventListener('change',()=>{state.step=etapa.value;render();});
  region.addEventListener('change',()=>{state.region=region.value;updateStateOptions();render();});
  $('uf').addEventListener('change',()=>{state.uf=$('uf').value;render();});
  $('search').addEventListener('input',e=>{state.search=e.target.value;render();});
  $('reset').addEventListener('click',()=>{state.step=levels[0];state.uf='';state.region='Todas';state.search='';etapa.value=state.step;region.value=state.region;$('search').value='';updateStateOptions();render();});
  $('downloadCsv').addEventListener('click',()=>{
    const rows=usableCities().filter(x=>normalize(x.municipio).includes(normalize(state.search)));
    if(!rows.length){$('status').textContent='Não há dados para exportação neste recorte.';return;}
    const cols=['ano','uf','regiao','codigo_ibge','municipio','etapa','percentual_n1_n2'];
    const csv=[cols.join(','),...rows.map(r=>cols.map(key=>'"'+String(r[key]??'').replaceAll('"','""')+'"').join(','))].join('\r\n');
    const blob=new Blob(['\uFEFF'+csv],{type:'text/csv;charset=utf-8'});
    const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='inep_ied_2022_'+(state.uf||'brasil')+'.csv';document.body.append(a);a.click();a.remove();URL.revokeObjectURL(url);
  });
}
(async function init(){
  try{
    const paths=['../data/processed/geografias.csv','../data/processed/municipios.csv','../data/processed/manifest.json'];
    const res=await Promise.all(paths.map(url=>fetch(url,{cache:'no-store'})));
    if(res.some(x=>!x.ok))throw new Error('Arquivos processados não encontrados. Execute python -m src.inep_pipeline e inicie um servidor na raiz do projeto.');
    const [geo,city,manifest]=await Promise.all([res[0].text(),res[1].text(),res[2].json()]);
    if(manifest.ano!==2022)throw new Error('Manifesto de ano inesperado');
    state.geos=parseCSV(geo);state.cities=parseCSV(city);state.manifest=manifest;
    bind();render();
  }catch(error){$('status').textContent='Não foi possível carregar os dados: '+error.message; $('status').style.color='#f5b66a'; ['stateChart','cityChart','regionChart'].forEach(id=>add('div',$(id),'chart-empty','Indisponível. Verifique o pipeline e o servidor HTTP.'));}
})();
