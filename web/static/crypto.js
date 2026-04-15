const p = 23;
const g = 5;

function modExp(base, exp, mod) {
  let result = 1;
  base %= mod;

  while (exp > 0) {
    if (exp % 2 === 1) result = (result * base) % mod;
    exp = Math.floor(exp / 2);
    base = (base * base) % mod;
  }
  return result;
}

// ElGamal encryption (toy version)
function encrypt(pk, m) {
  const r = Math.floor(Math.random() * (p - 2)) + 1;

  const c1 = modExp(g, r, p);
  const c2 = (m * modExp(pk, r, p)) % p;

  return { c1, c2 };
}

// fake proof (you will replace later)
function generateProof(vote) {
  return { valid: vote === 0 || vote === 1 };
}