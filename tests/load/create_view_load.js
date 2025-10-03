// tests/load/create_view_load.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '30s', target: 10 },  // Ramp up to 10 users
    { duration: '1m', target: 20 },   // Stay at 20 users
    { duration: '30s', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
    errors: ['rate<0.1'],              // Error rate under 10%
  },
};

const BASE_URL = 'http://localhost:8000';

// Setup: Login and get token
export function setup() {
  const loginRes = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify({
    email: 'alice@example.com',
    password: 'password123',
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  return { token: loginRes.json('access_token') };
}

export default function (data) {
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${data.token}`,
  };
  
  // Create story
  const createPayload = JSON.stringify({
    text: `Load test story ${__VU}-${__ITER}`,
    visibility: 'public',
  });
  
  const createRes = http.post(
    `${BASE_URL}/api/v1/stories`,
    createPayload,
    { headers }
  );
  
  const createSuccess = check(createRes, {
    'story created': (r) => r.status === 201 || r.status === 429,
    'has story id': (r) => r.status === 429 || r.json('id') !== undefined,
  });
  
  errorRate.add(!createSuccess);
  
  if (createRes.status === 201) {
    const storyId = createRes.json('id');
    
    // View the story
    const viewRes = http.post(
      `${BASE_URL}/api/v1/stories/${storyId}/view`,
      null,
      { headers }
    );
    
    const viewSuccess = check(viewRes, {
      'story viewed': (r) => r.status === 200,
      'has view data': (r) => r.json('is_new_view') !== undefined,
    });
    
    errorRate.add(!viewSuccess);
  }
  
  sleep(1);
}

export function teardown(data) {
  console.log('Load test completed');
}
