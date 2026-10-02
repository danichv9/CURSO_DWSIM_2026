'use strict';
const M=window.SYNGAS_MODEL;
const names={C:['Carbono','% masa · base seca'],H:['Hidrógeno','% masa · base seca'],O:['Oxígeno','% masa · base seca'],Moisture:['Humedad','% · humedad total'],Ash:['Cenizas','% masa · base seca'],FC:['Carbono fijo','% masa · base seca'],VM:['Materia volátil','% masa · base seca'],ER:['Relación de equivalencia','adimensional'],T:['Temperatura','K'],SB:['Vapor / biomasa','kg/kg']};
const outputNames={H2:'Hidrógeno',CO:'Monóxido de carbono',CO2:'Dióxido de carbono',CH4:'Metano',LHV:'Poder calorífico inferior'};
const symbols={H2:'H₂',CO:'CO',CO2:'CO₂',CH4:'CH₄'};
const fmt=(x,n=2)=>new Intl.NumberFormat('es',{maximumFractionDigits:n,minimumFractionDigits:n}).format(x);
let last=null,exampleIndex=0;
function predict(x){
 const z=x.map((v,i)=>(v-M.xMin[i])/(M.xMax[i]-M.xMin[i]));
 const [w,b,v,c]=M.weights;
 const h=b.map((bias,j)=>Math.tanh(bias+z.reduce((s,a,i)=>s+a*w[i][j],0)));
 return c.map((bias,k)=>(bias+h.reduce((s,a,j)=>s+a*v[j][k],0))*(M.yMax[k]-M.yMin[k])+M.yMin[k]);
}
window.predictSyngas=predict;
M.inputs.forEach((key,i)=>{
 const label=document.createElement('label');label.htmlFor=key;
 label.innerHTML=`<strong>${key==='Moisture'?'M':key==='Ash'?'A':key} · ${names[key][0]}</strong>${names[key][1]}<input id="${key}" name="${key}" type="number" step="any" required min="0" aria-describedby="range-${key}"><span class="range" id="range-${key}">Entrenado: ${fmt(M.xMin[i])}–${fmt(M.xMax[i])}</span>`;
 document.querySelector(i<7?'#biomass-fields':'#process-fields').append(label);
});
function loadExample(){const row=M.examples[exampleIndex++%M.examples.length];M.inputs.forEach(k=>document.getElementById(k).value=row[k].toFixed(6));markDirty();}
function markDirty(){if(last){document.getElementById('freshness').textContent='Entradas modificadas: vuelve a predecir';document.getElementById('status').textContent='Recalcular';document.getElementById('download').disabled=true;}}
document.getElementById('example').addEventListener('click',loadExample);
document.getElementById('prediction-form').addEventListener('input',markDirty);
document.getElementById('prediction-form').addEventListener('submit',event=>{
 event.preventDefault();const error=document.getElementById('form-error');error.textContent='';
 const x=M.inputs.map(k=>Number(document.getElementById(k).value));
 if(x.some(v=>!Number.isFinite(v)||v<0)||x[8]<=0){error.textContent='Introduce valores finitos y no negativos. La temperatura absoluta debe ser mayor que cero.';return;}
 if(x.slice(0,7).some(v=>v>100)){error.textContent='Los porcentajes de cada entrada deben estar entre 0 y 100.';return;}
 const y=predict(x);if(y.some(v=>!Number.isFinite(v))){error.textContent='No se pudo calcular: revisa las entradas.';return;}
 const outside=M.inputs.filter((_,i)=>x[i]<M.xMin[i]||x[i]>M.xMax[i]);
 const warnings=[];
 if(outside.length)warnings.push(`Fuera del rango de entrenamiento: ${outside.join(', ')}. Es una extrapolación; interpreta el resultado con especial cautela.`);
 if(y.some(v=>v<0)||y.slice(0,4).some(v=>v>100)||y.slice(0,4).reduce((a,b)=>a+b,0)>100)warnings.push('La red produjo valores físicamente inconsistentes. Se muestran sin recortar ni normalizar.');
 document.getElementById('warnings').textContent=warnings.join(' ');
 document.getElementById('empty').hidden=true;document.getElementById('prediction').hidden=false;
 document.getElementById('status').textContent=outside.length?'Extrapolación':'Predicción calculada';
 document.getElementById('lhv').textContent=fmt(y[4]);
 document.getElementById('gas-bars').innerHTML=y.slice(0,4).map((value,i)=>`<div class="gas-row"><div class="gas-label"><span><strong>${symbols[M.outputs[i]]}</strong><small>${outputNames[M.outputs[i]]}</small></span><strong>${fmt(value)} % vol.</strong></div><div class="bar-track"><div class="bar-fill" style="width:${Math.max(0,Math.min(100,value))}%;background:${['#237f62','#83a665','#b2bda6','#c99a4d'][i]}"></div></div></div>`).join('');
 document.getElementById('ratio').textContent=y[1]>0?fmt(y[0]/y[1]):'No definida';
 document.getElementById('freshness').textContent='Resultados de las entradas actuales';document.getElementById('download').disabled=false;
 last={inputs:Object.fromEntries(M.inputs.map((k,i)=>[k,x[i]])),predictions:Object.fromEntries(M.outputs.map((k,i)=>[k,y[i]])),units:{inputs:Object.fromEntries(M.inputs.map(k=>[k,names[k][1]])),outputs:{H2:'vol.% (base libre de N2)',CO:'vol.% (base libre de N2)',CO2:'vol.% (base libre de N2)',CH4:'vol.% (base libre de N2)',LHV:'MJ/Nm³'}},warnings,model:{architecture:'10-10-5 tanh/linear',datasetSha256:M.sha256},calculatedAt:new Date().toISOString()};
});
document.getElementById('download').addEventListener('click',()=>{if(!last)return;const url=URL.createObjectURL(new Blob([JSON.stringify(last,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='experimento-syngas.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
const labels={train:'Entrenamiento · Hoja1',validation:'Validación · Hoja1',test:'Prueba · Hoja1',external:'Validación externa · Hoja2'};
document.getElementById('split').innerHTML=Object.entries(M.counts).map(([k,v])=>`<div>${labels[k]}<strong>${v} <small>muestras</small></strong></div>`).join('');
document.getElementById('metrics').innerHTML=M.outputs.map(k=>`<tr><td>${symbols[k]||k}</td>${['test','external'].map(set=>['mae','rmse','r'].map(metric=>`<td>${fmt(M.metrics[set][k][metric],3)}</td>`).join('')).join('')}</tr>`).join('');
document.getElementById('training-detail').textContent=`${M.epochs} épocas ejecutadas · Adam · lote 16 · paciencia 30 · semilla 42. Arquitectura del cuaderno; modelo reentrenado con los datos adjuntos, no pesos recuperados de su ejecución original.`;
loadExample();
