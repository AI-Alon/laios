// ===== LAIOS Production Website Scripts =====

document.addEventListener("DOMContentLoaded", () => {
  // --- Navigation scroll effect ---
  const nav = document.getElementById("nav");
  const handleScroll = () => {
    nav.classList.toggle("scrolled", window.scrollY > 50);
  };
  window.addEventListener("scroll", handleScroll, { passive: true });
  handleScroll();

  // --- Mobile navigation toggle ---
  const navToggle = document.getElementById("navToggle");
  const navLinks = document.getElementById("navLinks");

  navToggle.addEventListener("click", () => {
    navToggle.classList.toggle("active");
    navLinks.classList.toggle("open");
  });

  // Close mobile nav on link click
  navLinks.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      navToggle.classList.remove("active");
      navLinks.classList.remove("open");
    });
  });

  // --- Terminal typing animation ---
  const commands = [
    {
      cmd: "laios chat",
      output:
        'LAIOS v1.0.0 | Model: gemma3:4b | Trust: balanced\nSession started. Type your goal.\n\n> "Analyze this codebase and suggest improvements"\nReasoning... Planning... Executing...\nFound 12 improvement opportunities across 8 files.',
    },
    {
      cmd: "laios run \"find all security vulnerabilities\"",
      output:
        "Goal parsed: security audit\nPlan: 4 tasks in execution DAG\nScanning... 47 files analyzed\nReport: 2 issues found, 0 critical. Details saved.",
    },
    {
      cmd: "laios serve --port 8000",
      output:
        "Starting LAIOS API server...\nREST API:    http://localhost:8000/api\nWebSocket:   ws://localhost:8000/ws\nWeb UI:      http://localhost:8000\nServer ready. Accepting connections.",
    },
  ];

  const typedCommand = document.getElementById("typedCommand");
  const terminalOutput = document.getElementById("terminalOutput");
  let cmdIndex = 0;

  function typeCommand(text, callback) {
    let i = 0;
    typedCommand.textContent = "";
    terminalOutput.textContent = "";

    function typeChar() {
      if (i < text.length) {
        typedCommand.textContent += text[i];
        i++;
        setTimeout(typeChar, 40 + Math.random() * 40);
      } else {
        callback();
      }
    }
    typeChar();
  }

  function showOutput(text, callback) {
    let i = 0;
    const lines = text.split("\n");
    terminalOutput.textContent = "";

    function showLine() {
      if (i < lines.length) {
        terminalOutput.textContent +=
          (i > 0 ? "\n" : "") + lines[i];
        i++;
        setTimeout(showLine, 120 + Math.random() * 80);
      } else {
        callback();
      }
    }
    showLine();
  }

  function runTerminalLoop() {
    const current = commands[cmdIndex];
    typeCommand(current.cmd, () => {
      setTimeout(() => {
        showOutput(current.output, () => {
          cmdIndex = (cmdIndex + 1) % commands.length;
          setTimeout(runTerminalLoop, 3000);
        });
      }, 400);
    });
  }

  runTerminalLoop();

  // --- Copy buttons ---
  document.querySelectorAll(".copy-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-target");
      const code = document.getElementById(targetId);
      if (!code) return;

      navigator.clipboard
        .writeText(code.textContent)
        .then(() => {
          btn.classList.add("copied");
          btn.innerHTML =
            '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>';
          setTimeout(() => {
            btn.classList.remove("copied");
            btn.innerHTML =
              '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>';
          }, 2000);
        })
        .catch(() => {
          // Fallback for older browsers
          const textarea = document.createElement("textarea");
          textarea.value = code.textContent;
          textarea.style.position = "fixed";
          textarea.style.opacity = "0";
          document.body.appendChild(textarea);
          textarea.select();
          document.execCommand("copy");
          document.body.removeChild(textarea);
          btn.classList.add("copied");
          setTimeout(() => btn.classList.remove("copied"), 2000);
        });
    });
  });

  // --- Scroll animations (Intersection Observer) ---
  const animatedElements = document.querySelectorAll(
    ".feature-card, .pipeline-step, .tool-category, .provider-card, .step-card, .usecase-card, .trust-card"
  );

  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1, rootMargin: "0px 0px -40px 0px" }
    );

    animatedElements.forEach((el, index) => {
      el.style.transitionDelay = `${(index % 3) * 0.1}s`;
      observer.observe(el);
    });
  } else {
    // Fallback: show everything
    animatedElements.forEach((el) => el.classList.add("visible"));
  }

  // --- Smooth scroll for anchor links ---
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", (e) => {
      const href = anchor.getAttribute("href");
      if (href === "#") return;

      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        const offset = 80;
        const top =
          target.getBoundingClientRect().top + window.scrollY - offset;
        window.scrollTo({ top, behavior: "smooth" });
      }
    });
  });
});
