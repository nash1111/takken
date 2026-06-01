
const ALL = Array.isArray(window.TAKKEN_QUESTIONS) ? window.TAKKEN_QUESTIONS : [];
const params = new URLSearchParams(location.search);
const reviewIds = (params.get('review') || '').split(',').map(x=>parseInt(x,10)).filter(Number.isFinite);
let deck = [];
let pos = 0;
let wrongIds = [];
let answers = [];
let autoNextTimer = null;
const AUTO_NEXT_MS = 500;
function clearAutoNext(){ if(autoNextTimer){ clearTimeout(autoNextTimer); autoNextTimer=null; } }
function shuffle(a){for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]]}return a}
function makeDeck(){
  if(reviewIds.length){deck = reviewIds.map(id=>ALL[id]).filter(Boolean)}
  else {deck = shuffle([...ALL]).slice(0,10)}
  pos=0; wrongIds=[]; answers=[];
}
function esc(s){return String(s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function render(){
  clearAutoNext();
  const app=document.getElementById('quizApp');
  if(!deck.length){app.innerHTML='<div class="card"><h2>問題を読み込めませんでした</h2><p>通信環境やブラウザ設定の影響で問題データが空になっています。再読み込みするか、二択フリップ・今日の問題から学習できます。</p><div class="flip-controls"><button class="btn" onclick="location.reload()">再読み込み</button><a class="ghost-btn" href="/flashcards/">二択フリップ</a><a class="ghost-btn" href="/today/">今日の問題</a></div></div>';return}
  if(pos>=deck.length){renderDone(app);return}
  const q=deck[pos];
  const choices=(q.choices && q.choices.length>=2) ? q.choices.slice(0,2) : ['誤り','正しい'];
  const percent=Math.round((pos/deck.length)*100);
  app.innerHTML=`<div class="flip-shell quiz-shell"><div class="flip-progress"><span>${reviewIds.length?'復習':'10問チャレンジ'}</span><b>${pos+1} / ${deck.length}</b></div><div class="quiz-progress-meter" aria-label="進捗 ${pos+1} / ${deck.length}"><span style="width:${percent}%"></span></div><p class="quiz-progress-copy">あと${deck.length-pos}問。回答すると自動で次へ進みます。</p><article id="flipCard" class="flip-card quiz-card" aria-label="左右フリップで回答"><span class="flip-theme">${esc(q.theme)}</span><h2 class="flip-title">${esc(q.title)}</h2><div class="flip-question">${esc(q.quiz)}</div><div class="flip-hint"><div class="flip-answer wrong-side"><span>左にフリック</span><b>${esc(choices[0])}</b></div><div class="flip-answer right-side"><span>右にフリック</span><b>${esc(choices[1])}</b></div></div><p class="flip-instruction">画面を左右にスワイプ、または下のボタン/←→キーで回答</p></article><div id="result" class="quiz-result-overlay" aria-live="polite"></div><div class="flip-controls quiz-choice-controls"><button class="ghost-btn" id="leftBtn">← ${esc(choices[0])}</button><button class="ghost-btn" id="rightBtn">${esc(choices[1])} →</button></div></div>`;
  bindCard(q, choices);
}
function bindCard(q, choices){
  const card=document.getElementById('flipCard');
  const left=document.getElementById('leftBtn');
  const right=document.getElementById('rightBtn');
  let startX=0,startY=0,drag=false,done=false;
  function choose(idx){
    if(done)return; done=true;
    const picked=choices[idx];
    const ok= picked === q.answer;
    if(!ok) wrongIds.push(q.id);
    answers.push({id:q.id, ok});
    card.classList.add(idx===0?'swipe-left':'swipe-right');
    setTimeout(()=>showResult(q,picked,ok),220);
  }
  card.addEventListener('pointerdown',e=>{startX=e.clientX;startY=e.clientY;drag=true;card.setPointerCapture?.(e.pointerId)});
  card.addEventListener('pointerup',e=>{if(!drag)return;drag=false;const dx=e.clientX-startX,dy=e.clientY-startY;if(Math.abs(dx)>60 && Math.abs(dx)>Math.abs(dy)*1.2) choose(dx>0?1:0)});
  left.onclick=()=>choose(0); right.onclick=()=>choose(1);
  document.onkeydown=e=>{if(e.key==='ArrowLeft')choose(0); if(e.key==='ArrowRight')choose(1)};
}
function showResult(q,picked,ok){
  const res=document.getElementById('result');
  const card=document.getElementById('flipCard');
  const left=document.getElementById('leftBtn');
  const right=document.getElementById('rightBtn');
  if(card){
    card.classList.remove('swipe-left','swipe-right');
    card.classList.add(ok?'right':'wrong','answered');
  }
  if(left) left.disabled=true;
  if(right) right.disabled=true;
  res.classList.add('show');
  const nextLabel = pos+1>=deck.length ? '結果へ' : '次のカードへ';
  res.innerHTML=`<div class="quiz-result-panel"><h2 class="${ok?'score-good':'score-bad'}">${ok?'正解':'不正解'}</h2><p class="quiz-answer-line">回答: <b>${esc(picked)}</b> / 正解: <b>${esc(q.answer)}</b></p><p class="quiz-rule-line">${esc(q.rule)}</p><p class="quiz-trap-line"><b>注意:</b> ${esc(q.trap)}</p><p class="next-countdown">0.5秒後に${nextLabel}</p></div>`;
  const goNext=()=>{ clearAutoNext(); pos++; render(); };
  res.onclick=goNext;
  autoNextTimer=setTimeout(goNext, AUTO_NEXT_MS);
}
function renderDone(app){
  const ok=answers.filter(a=>a.ok).length;
  const review = wrongIds.length ? `${location.origin}/quiz/?review=${wrongIds.join(',')}` : '';
  const rate=Math.round((ok/deck.length)*100);
  app.innerHTML=`<section class="card quiz-done"><p class="small">10問完走</p><h1>結果: ${ok} / ${deck.length} 正解</h1><div class="quiz-score-band"><span><b>${rate}%</b>正答率</span><span><b>${wrongIds.length}</b>復習候補</span></div><p>${wrongIds.length ? '不正解だけをまとめた復習リンクを作りました。共有・保存して後で解き直せます。' : '全問正解です。別の10問にも挑戦できます。'}</p><div class="review-box ${wrongIds.length?'show':''}"><label for="shareUrl"><b>復習シェアリンク</b></label><input id="shareUrl" class="share-url" readonly value="${esc(review)}"><div class="flip-controls"><button class="btn" id="copyBtn">リンクをコピー</button><a class="ghost-btn" href="${esc(review)}">この不正解だけ復習</a></div></div><div class="quiz-next-routes"><a class="card" href="/quiz/" id="againLink"><h3>もう10問解く</h3><p>新しいランダム10問で完走を続ける。</p></a><a class="card" href="/topics/hikkake/"><h3>苦手分野へ</h3><p>ひっかけ問題で落としやすい表現を確認。</p></a><a class="card" href="/flashcards/"><h3>フリップ連続回答</h3><p>テンポよく追加演習してPVと学習量を伸ばす。</p></a></div><div class="flip-controls"><button class="btn" id="againBtn">この場でもう10問</button><a class="ghost-btn" href="/today/">今日の問題</a></div></section>`;
  document.getElementById('againBtn').onclick=()=>{history.replaceState(null,'','/quiz/'); makeDeck(); render()};
  const copy=document.getElementById('copyBtn');
  if(copy) copy.onclick=async()=>{const input=document.getElementById('shareUrl'); input.select(); try{await navigator.clipboard.writeText(input.value); copy.textContent='コピーしました'}catch(e){document.execCommand('copy'); copy.textContent='コピーしました'}};
}
makeDeck(); render();
