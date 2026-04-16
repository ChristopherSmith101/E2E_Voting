let token = null;
let pk = null;
let hasVoted = false;

// -----------------------------
// Load public key once
// -----------------------------
async function loadPublicKey() {
  const res = await fetch("/api/public_key");
  const data = await res.json();
  pk = data.pk;
}

async function loadStatus() {
  const res = await fetch("/api/status");
  const data = await res.json();
  hasVoted = data.has_voted;
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
  await loadStatus();

  if (hasVoted) {
    document.getElementById("status").innerText = "You have already voted.";
    return; // IMPORTANT: stop initialization if already voted
  }

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

  if (hasVoted) {
    status.innerText = "Vote rejected (already voted).";
    return;
  }

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