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
async function castVote(vote, isDummy = false) {
  const status = document.getElementById("status");

  const voteType = isDummy ? "dummy" : "real";
  status.innerHTML = `Preparing ${voteType} ballot...`;
  status.className = "info";

  if (hasVoted) {
    status.innerHTML = "Vote rejected (already voted).";
    status.className = "error";
    return;
  }

  if (!token || !pk) {
    status.innerHTML = "System not ready yet...";
    status.className = "error";
    return;
  }

  const ciphertext = encrypt(pk, vote);
  const proof = generateProof(vote);

  const ballot = {
    ciphertext,
    proof,
    token,
    is_dummy: isDummy
  };

  status.innerHTML = isDummy ? "Submitting dummy ballot..." : "Submitting real vote...";
  status.className = "info";

  try {
    const res = await fetch("/api/vote", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(ballot)
    });

    const data = await res.json();

    if (data.status === "accepted") {
      const receipt = data.receipt;
      const ballot_hash = data.ballot_hash;

      localStorage.setItem("vote_receipt", receipt);
      localStorage.setItem("ballot_hash", ballot_hash);

      const voteLabel = isDummy ? "dummy" : "real";
      status.innerHTML = `✓ ${voteLabel.charAt(0).toUpperCase() + voteLabel.slice(1)} ballot cast!<br><br>Save this receipt:<br><code>${receipt}</code><br><br>Ballot Hash:<br><code>${ballot_hash}</code>`;
      status.className = "success";
    } else {
      status.innerHTML = "Ballot rejected.";
      status.className = "error";
    }

  } catch (err) {
    console.error(err);
    status.innerHTML = "Error submitting ballot.";
    status.className = "error";
  }
}