// bg-generator.js: Generates a unique gradient background based on text content

document.addEventListener("DOMContentLoaded", function() {
    // 1. Get the text to hash (from hidden span in base.html)
    const rawSpan = document.getElementById('dq-content-raw');
    let text = rawSpan ? rawSpan.innerText.trim() : "";

    if (!text) {
        text = "DictumAndQuotesDefault" + Math.random(); // Fallback random if no text
    }

    // 2. Hash function (DJB2)
    let hash = 5381;
    for (let i = 0; i < text.length; i++) {
        // Force 32-bit integer arithmetic
        hash = ((hash << 5) + hash) + text.charCodeAt(i);
        hash = hash & hash; // Convert to 32bit integer
    }

    // 3. Generate 6 color components deterministically from the hash
    // We need 6 numbers between 0 and 255.
    // Let's use pseudo-random generator seeded by hash

    function Mulberry32(a) {
        return function() {
          var t = a += 0x6D2B79F5;
          t = Math.imul(t ^ (t >>> 15), t | 1);
          t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
          return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
        }
    }

    const rand = Mulberry32(hash); // Seeded random generator

    // Generate 6 color components with darker range for "meditative" feel
    let colors = [];
    for(let i=0; i<6; i++) {
        // Generate number between 10 and 80 (dark colors)
        colors.push(Math.floor(rand() * 70) + 10);
    }

    // Shuffle slightly based on random to allow variation on refresh (optional)
    // colors.sort(() => Math.random() - 0.5);

    const rgb1 = `rgb(${colors[0]}, ${colors[1]}, ${colors[2]})`;
    const rgb2 = `rgb(${colors[3]}, ${colors[4]}, ${colors[5]})`;

    console.log("DQ BG Generator:", text.substring(0, 20) + "...", hash, rgb1, rgb2);

    // 4. Apply to body
    // Using linear-gradient to right with standard syntax
    const bgString = `linear-gradient(90deg, ${rgb1} 0%, ${rgb2} 100%)`;
    document.body.style.background = bgString;

    // 5. Apply to image background container (if exists on index page)
    const imgBgContainer = document.querySelector('.image-col center > div');
    if (imgBgContainer) {
         // Use the first color of the gradient with opacity 0.7
         imgBgContainer.style.background = `rgba(${colors[0]}, ${colors[1]}, ${colors[2]}, 0.7)`;
    }
});

