/**
 * Centralized API service — all backend calls go through here.
 * The Vite proxy rewrites /api → http://127.0.0.1:8000
 */

const BASE_URL = '/api';

// ─── Auth ────────────────────────────────────────────────────────────────────

/**
 * Login an assessor.
 * @param {string} accessorId
 * @param {string} password
 * @returns {Promise<{access_token: string, token_type: string, name: string}>}
 */
export async function loginUser(accessorId, password) {
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ accessor_id: accessorId, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Invalid credentials');
  }
  return res.json();
}

// ─── Setup ───────────────────────────────────────────────────────────────────

/**
 * Upload the global Terms & Conditions document.
 * @param {File} file
 * @param {string} token  Bearer token
 */
export async function uploadTC(file, token) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${BASE_URL}/upload/tc`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to upload T&C document');
  }
  return res.json();
}

// ─── Claims ──────────────────────────────────────────────────────────────────

/**
 * Submit a new claim for AI assessment.
 * @param {{ customerName: string, claimType: string, claimText?: string }} fields
 * @param {File} policyFile
 * @param {File|null} claimFile
 * @param {string} token  Bearer token
 */
export async function submitClaim(fields, policyFile, claimFile, token) {
  const formData = new FormData();
  formData.append('customer_name', fields.customerName);
  formData.append('claim_type', fields.claimType);
  formData.append('policy_file', policyFile);
  if (claimFile) formData.append('claim_file', claimFile);
  if (fields.claimText) formData.append('claim_text', fields.claimText);

  const res = await fetch(`${BASE_URL}/upload/submit`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to evaluate claim');
  }
  return res.json();
}

/**
 * Get the status / result of a specific claim by ID.
 * @param {number} claimId
 * @param {string} token  Bearer token
 */
export async function getClaimStatus(claimId, token) {
  const res = await fetch(`${BASE_URL}/upload/${claimId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Claim not found');
  }
  return res.json();
}
