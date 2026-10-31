(() => {
  const csrfMeta = document.querySelector('meta[name="csrf-token"]');
  const path = window.location.pathname.replace(/\/+$/, "") || "/";
  const authPage = document.body.dataset.page === "auth";
  let csrfToken = "";

  async function getStatus() {
    const response = await fetch("/api/auth/status", { credentials: "same-origin" });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not connect to the PDF Tools server.");
    csrfToken = data.csrf_token;
    csrfMeta.content = csrfToken;
    return data;
  }

  function showAuth(status) {
    const setup = status.needs_setup;
    const register = path === "/register" && !setup;
    const screen = document.querySelector("#auth-screen");
    if (screen) screen.hidden = false;
    const mode = setup ? "setup" : register ? "register" : "login";
    const config = {
      setup: ["One-time setup", "Create your administrator", "Set up the administrator account for this service.", "Create administrator"],
      register: ["Authorized access", "Create your account", "Enter the one-time invitation from your administrator.", "Create account"],
      login: ["Welcome back", "Sign in to PDF Tools", "Enter your account details to continue to your workspace.", "Sign in"],
    }[mode];

    document.querySelector("#auth-eyebrow").textContent = config[0];
    document.querySelector("#auth-title").textContent = config[1];
    document.querySelector("#auth-description").textContent = config[2];
    const invitation = document.querySelector("#invitation-field");
    invitation.hidden = mode !== "register";
    document.querySelector("#invitation").required = mode === "register";
    const password = document.querySelector("#password");
    password.autocomplete = mode === "login" ? "current-password" : "new-password";
    const submit = document.querySelector("#auth-submit");
    submit.replaceChildren(document.createTextNode(config[3]), document.createTextNode(" →"));
    const links = document.querySelector("#auth-links");
    links.replaceChildren();
    if (mode === "login") {
      links.append("Have an invitation? ", makeLink("/register", "Create an account"));
    } else if (mode === "register") {
      links.append(makeLink("/login", "Return to sign in"));
    }

    const form = document.querySelector("#auth-form");
    form.onsubmit = async (event) => {
      event.preventDefault();
      const error = document.querySelector("#auth-error");
      const button = document.querySelector("#auth-submit");
      error.hidden = true;
      button.disabled = true;
      try {
        const payload = {
          username: document.querySelector("#username").value,
          password: password.value,
        };
        if (mode === "register") payload.invitation = document.querySelector("#invitation").value;
        const response = await fetch(`/api/auth/${mode}`, {
          method: "POST",
          credentials: "same-origin",
          headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken },
          body: JSON.stringify(payload),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "Sign-in failed.");
        window.location.assign("/");
      } catch (requestError) {
        error.textContent = requestError instanceof TypeError
          ? "Could not reach the PDF Tools server. Please try again."
          : requestError.message;
        error.hidden = false;
      } finally {
        button.disabled = false;
      }
    };
  }

  function makeLink(href, text) {
    const link = document.createElement("a");
    link.href = href;
    link.textContent = text;
    return link;
  }

  function loadWorkspace(user) {
    document.body.dataset.username = user.username;
    document.body.dataset.role = user.role;
    document.querySelector("#profile-username").textContent = user.username;
    document.querySelector("#profile-role").textContent = `${user.role[0].toUpperCase()}${user.role.slice(1)} account`;
    document.querySelector("#profile-avatar").textContent = user.username.slice(0, 1).toUpperCase();
    document.querySelector("#open-admin").hidden = user.role !== "admin";
    document.querySelector("#app-shell").hidden = false;

    document.querySelector("#logout").addEventListener("click", async () => {
      try {
        const response = await fetch("/api/auth/logout", {
          method: "POST",
          credentials: "same-origin",
          headers: { "X-CSRF-Token": csrfToken },
        });
        if (!response.ok) throw new Error("Could not sign out. Please try again.");
        window.location.assign("/login");
      } catch (error) {
        window.alert(error instanceof TypeError
          ? "Could not reach the PDF Tools server. Please try again."
          : error.message);
      }
    });

    const script = document.createElement("script");
    script.src = "/static/site.js";
    script.onerror = () => {
      document.querySelector("#app-shell").hidden = true;
      showConnectionError("The PDF Tools interface could not be loaded.");
    };
    document.body.append(script);
  }

  function showConnectionError(message) {
    const screen = document.querySelector("#auth-screen");
    if (screen) screen.hidden = false;
    const error = document.querySelector("#auth-error");
    if (!error) return;
    error.textContent = message;
    error.hidden = false;
  }

  getStatus().then((status) => {
    if (authPage) {
      if (status.user && !status.needs_setup) {
        window.location.replace("/");
        return;
      }
      showAuth(status);
    } else if (!status.user) {
      showAuth(status);
    } else {
      loadWorkspace(status.user);
    }
  }).catch((error) => showConnectionError(
    error instanceof TypeError
      ? "Could not reach the PDF Tools server. Check the deployment and try again."
      : error.message
  ));
})();
