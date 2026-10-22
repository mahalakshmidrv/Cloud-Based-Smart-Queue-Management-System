document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("form[data-confirm]").forEach(form => {
    form.addEventListener("submit", event => {
      const message = form.getAttribute("data-confirm") || "Continue?";
      if (!window.confirm(message)) event.preventDefault();
    });
  });

  // Refresh a ticket's position every 10 seconds while its ticket page is open.
  if (window.ticketId) {
    const updateTicket = async () => {
      try {
        const response = await fetch("/api/queue", {cache: "no-store"});
        if (!response.ok) return;
        const data = await response.json();
        const row = data.queue.find(item => item.ticket_no);
        const current = data.queue;
        // Queue endpoint intentionally provides only active tickets. The page reload button
        // remains available for final status changes, while the estimate can update live.
        const ticketElement = document.querySelector(".large-ticket-number");
        if (!ticketElement) return;
        const ticketNo = ticketElement.textContent.trim();
        const position = current.findIndex(item => item.ticket_no === ticketNo);
        const ahead = document.getElementById("ahead-count");
        const wait = document.getElementById("wait-time");
        if (position >= 0) {
          if (ahead) ahead.textContent = Math.max(0, position - (current[0]?.status === "Serving" ? 1 : 0));
          if (wait) wait.textContent = "~" + Math.max(0, position) * (window.ticketServiceMinutes || 5) + " min";
        }
      } catch (_) { /* Keep the ticket page usable if the network is temporarily unavailable. */ }
    };
    setInterval(updateTicket, 10000);
  }
});
