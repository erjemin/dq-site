// Rating Mail.ru counter
var _tmr = window._tmr || (window._tmr = []);
_tmr.push({id: "3744288", type: "pageView", start: (new Date()).getTime()});
(function (d, w, id) {
  if (d.getElementById(id)) return;
  var ts = d.createElement("script");
  ts.type = "text/javascript";
  ts.async = true;
  ts.id = id;
  ts.src = "https://top-fwz1.mail.ru/js/code.js";
  var f = function () {
    var s = d.getElementsByTagName("script")[0];
    s.parentNode.insertBefore(ts, s);
  };
  if (w.opera == "[object Opera]") {
    d.addEventListener("DOMContentLoaded", f, false);
  } else {
    f();
  }
})(document, window, "tmr-code");
// Yandex.Metrika counter
(function(m,e,t,r,i,k,a){
  m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
  m[i].l=1*new Date();
  for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
  k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)
})(window, document,'script','https://mc.yandex.ru/metrika/tag.js?id=106953063', 'ym');
ym(106953063, 'init', {ssr:true, webvisor:true, clickmap:true, ecommerce:"dataLayer", referrer: document.referrer, url: location.href, accurateTrackBounce:true, trackLinks:true});
// Google Analytics (GA4) counter
(function() {
  var gaScript = document.createElement('script');
  gaScript.async = true;
  gaScript.src = 'https://www.googletagmanager.com/gtag/js?id=G-WTJM8J9YL5';
  document.head.appendChild(gaScript);

  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  // Делаем функцию глобально доступной, если понадобится вызывать её из других скриптов
  window.gtag = gtag;
  gtag('js', new Date());
  gtag('config', 'G-WTJM8J9YL5');
})();
