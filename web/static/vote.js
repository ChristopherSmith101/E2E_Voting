let token = null;   // <-- stored once
let pk = null;      // <-- stored once

// -----------------------------
// Load public key once
// -----------------------------
async function loadPublicKey() {
  const res = await fetch("/api/public_key");
  const data = await res.json();
  pk = data.pk;
}

// -----------------------------
// Get token ONCE per session
// -----------------------------
async function initToken() {
  const res = await fetch("/api/token", {
    method: "POST"
  });

  const data = await res.json();
  token = data.token;
}

// -----------------------------
// Initialization (run once)
// -----------------------------
async function init() {
  await loadPublicKey();
  await initToken();
  console.log("Client initialized");
}

// Run immediately when page loads
init();


// -----------------------------
// Main voting function
// -----------------------------
async function castVote(vote) {
  const status = document.getElementById("status");

  status.innerText = "Preparing ballot...";

  if (!token || !pk) {
    status.innerText = "System not ready yet...";
    return;
  }

  const ciphertext = encrypt(pk, vote);
  const proof = generateProof(vote);

  const ballot = {
    ciphertext,
    proof,
    token
  };

  status.innerText = "Submitting vote...";

  try {
    const res = await fetch("/api/vote", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(ballot)
    });

    const data = await res.json();

    if (data.status === "accepted") {
      const receipt = data.receipt;

      localStorage.setItem("vote_receipt", receipt);

      status.innerText = "Vote accepted!";
      alert("Vote cast! Save this receipt: " + receipt);
    } else {
      status.innerText = "Vote rejected.";
    }

  } catch (err) {
    console.error(err);
    status.innerText = "Error submitting vote.";
  }
}