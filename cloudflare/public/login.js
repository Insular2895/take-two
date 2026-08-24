document.querySelector("#login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const error = document.querySelector("#login-error");
  error.textContent = "";
  const response = await fetch("/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: document.querySelector("#username").value,
      password: document.querySelector("#password").value,
    }),
  });
  if (response.ok) window.location.assign("/dashboard");
  else error.textContent = response.status === 429 ? "Trop de tentatives. Réessayez dans dix minutes." : "Identifiants invalides.";
});
