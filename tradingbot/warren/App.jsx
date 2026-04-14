import React, { useState } from 'react';
import BuffettNewsletterSignup from './newsletter_frontend';

function App() {
  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #f5f5f5 0%, #ffffff 100%)',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <BuffettNewsletterSignup />
    </div>
  );
}

export default App;
