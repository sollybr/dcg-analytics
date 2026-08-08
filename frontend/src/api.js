export async function fetchAnalytics() {
  const response = await fetch('/api/analytics/');
  if (!response.ok) {
    throw new Error(`Analytics API returned ${response.status}`);
  }
  return response.json();
}

export async function fetchCardsByName(name) {
  const encodedName = encodeURIComponent(name);
  const response = await fetch(`/api/cards/?name=${encodedName}`);
  if (!response.ok) {
    throw new Error(`Cards API returned ${response.status}`);
  }
  return response.json();
}

export async function fetchCardsByType(type, page = 1) {
  const encodedType = encodeURIComponent(type);
  const response = await fetch(`/api/cards-by-type/?type=${encodedType}&page=${page}`);
  
  if (!response.ok) {
    throw new Error(`Cards by Type API returned ${response.status}`);
  }
  
  return response.json();
}