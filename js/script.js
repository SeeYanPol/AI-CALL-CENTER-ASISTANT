window.onload = function() {
  setTimeout(() => {
    document.querySelector(".intro-screen").classList.add("hidden");
    document.querySelector(".menu").classList.remove("hidden");
  }, 2500); // after 2.5 seconds, show menu
};

document.getElementById("startBtn").onclick = () => {
  window.location.href = "call.html";
};
document.getElementById("continueBtn").onclick = () => {
  alert("No saved call to continue yet!");
};
document.getElementById("exitBtn").onclick = () => {
  window.close();
};

document.querySelector('.intro').addEventListener('click', () => {
  // action mo dito
});

// Wait a bit before showing "Tap to continue"
const pressAny = document.getElementById("pressAny");

setTimeout(() => {
  pressAny.classList.remove("hidden");
  pressAny.classList.add("show");
}, 2000); // lalabas after 2 seconds

// Kapag tinap ang "Tap to continue"
pressAny.addEventListener("click", () => {
  // fade out animation
  document.body.style.transition = "opacity 1s ease";
  document.body.style.opacity = "0";

  // lilipat sa next page
  setTimeout(() => {
    window.location.href = "call.html"; // 👈 replace mo kung iba file name mo
  }, 1000);
});

if ('exitBtn' in document) {
    document.getElementById("exitBtn").onclick = () => 
        window.close(returnValue = 'call.html');
    }