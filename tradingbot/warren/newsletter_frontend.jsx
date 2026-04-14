import React, { useState } from 'react';

export default function BuffettNewsletterSignup() {
  const [step, setStep] = useState('choice'); // choice, form, confirmation
  const [tier, setTier] = useState(null); // 'free' or 'premium'
  const [market, setMarket] = useState(null); // 'us' or 'eu'
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleTierSelect = (selectedTier) => {
    setTier(selectedTier);
    setStep('form');
    setMessage('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const response = await fetch('/api/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          name,
          tier,
          market
        })
      });

      const data = await response.json();

      if (response.ok) {
        setMessage(`✓ Confirmation email sent to ${email}`);
        setStep('confirmation');
        setEmail('');
        setName('');
      } else {
        setMessage(data.error || 'Signup failed. Please try again.');
      }
    } catch (err) {
      setMessage('Network error. Please try again.');
    }

    setLoading(false);
  };

  const reset = () => {
    setStep('choice');
    setTier(null);
    setMarket(null);
    setEmail('');
    setName('');
    setMessage('');
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, var(--color-background-tertiary) 0%, var(--color-background-secondary) 100%)',
      padding: '2rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '600px'
      }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <h1 style={{
            fontSize: '32px',
            fontWeight: 500,
            margin: '0 0 0.5rem 0',
            color: 'var(--color-text-primary)'
          }}>
            Warren Buffett Newsletter
          </h1>
          <p style={{
            fontSize: '16px',
            color: 'var(--color-text-secondary)',
            margin: 0
          }}>
            Quality over quantity. Less is more.
          </p>
        </div>

        {/* Step 1: Choose tier */}
        {step === 'choice' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <p style={{
              textAlign: 'center',
              fontSize: '15px',
              color: 'var(--color-text-secondary)',
              margin: '0 0 1.5rem 0'
            }}>
              Select your plan:
            </p>

            {/* Free Plan */}
            <div
              onClick={() => handleTierSelect('free')}
              style={{
                background: 'var(--color-background-primary)',
                border: '2px solid var(--color-border-tertiary)',
                borderRadius: 'var(--border-radius-lg)',
                padding: '2rem 1.5rem',
                cursor: 'pointer',
                transition: 'all 0.2s',
                textAlign: 'center'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-border-secondary)';
                e.currentTarget.style.background = 'var(--color-background-secondary)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-border-tertiary)';
                e.currentTarget.style.background = 'var(--color-background-primary)';
              }}
            >
              <h3 style={{
                fontSize: '20px',
                fontWeight: 500,
                margin: '0 0 0.5rem 0',
                color: 'var(--color-text-primary)'
              }}>
                Free
              </h3>
              <p style={{
                fontSize: '13px',
                color: 'var(--color-text-secondary)',
                margin: '0 0 1rem 0'
              }}>
                Top 5 screened stocks
              </p>
              <p style={{
                fontSize: '24px',
                fontWeight: 500,
                color: 'var(--color-text-info)',
                margin: 0
              }}>
                €0/month
              </p>
            </div>

            {/* Premium Plan */}
            <div
              onClick={() => handleTierSelect('premium')}
              style={{
                background: 'var(--color-background-info)',
                border: '2px solid var(--color-border-info)',
                borderRadius: 'var(--border-radius-lg)',
                padding: '2rem 1.5rem',
                cursor: 'pointer',
                transition: 'all 0.2s',
                textAlign: 'center'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
              }}
            >
              <h3 style={{
                fontSize: '20px',
                fontWeight: 500,
                margin: '0 0 0.5rem 0',
                color: 'var(--color-text-info)'
              }}>
                Premium
              </h3>
              <p style={{
                fontSize: '13px',
                color: 'var(--color-text-info)',
                margin: '0 0 1rem 0',
                opacity: 0.9
              }}>
                Full analysis + premium insights
              </p>
              <p style={{
                fontSize: '24px',
                fontWeight: 500,
                color: 'var(--color-text-info)',
                margin: 0
              }}>
                €9.99/month
              </p>
            </div>
          </div>
        )}

        {/* Step 2: Fill form */}
        {step === 'form' && tier && (
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {/* Market selection */}
            <div>
              <label style={{
                display: 'block',
                fontSize: '14px',
                fontWeight: 500,
                marginBottom: '0.75rem',
                color: 'var(--color-text-primary)'
              }}>
                Market
              </label>
              <select
                value={market || ''}
                onChange={(e) => setMarket(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  fontSize: '15px',
                  borderRadius: 'var(--border-radius-md)',
                  border: '0.5px solid var(--color-border-tertiary)',
                  background: 'var(--color-background-primary)',
                  color: 'var(--color-text-primary)'
                }}
              >
                <option value="">Select market</option>
                <option value="us">United States (S&P 500)</option>
                <option value="eu">Europe (DAX, CAC, AEX)</option>
              </select>
            </div>

            {/* Email */}
            <div>
              <label style={{
                display: 'block',
                fontSize: '14px',
                fontWeight: 500,
                marginBottom: '0.75rem',
                color: 'var(--color-text-primary)'
              }}>
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                required
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  fontSize: '15px',
                  borderRadius: 'var(--border-radius-md)',
                  border: '0.5px solid var(--color-border-tertiary)',
                  background: 'var(--color-background-primary)',
                  color: 'var(--color-text-primary)',
                  boxSizing: 'border-box'
                }}
              />
            </div>

            {/* Name */}
            <div>
              <label style={{
                display: 'block',
                fontSize: '14px',
                fontWeight: 500,
                marginBottom: '0.75rem',
                color: 'var(--color-text-primary)'
              }}>
                Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Your name"
                required
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  fontSize: '15px',
                  borderRadius: 'var(--border-radius-md)',
                  border: '0.5px solid var(--color-border-tertiary)',
                  background: 'var(--color-background-primary)',
                  color: 'var(--color-text-primary)',
                  boxSizing: 'border-box'
                }}
              />
            </div>

            {/* Message */}
            {message && (
              <div style={{
                padding: '1rem',
                background: 'var(--color-background-danger)',
                color: 'var(--color-text-danger)',
                borderRadius: 'var(--border-radius-md)',
                fontSize: '14px',
                textAlign: 'center'
              }}>
                {message}
              </div>
            )}

            {/* Buttons */}
            <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
              <button
                type="button"
                onClick={() => setStep('choice')}
                disabled={loading}
                style={{
                  flex: 1,
                  padding: '0.75rem',
                  fontSize: '15px',
                  fontWeight: 500,
                  border: '0.5px solid var(--color-border-secondary)',
                  background: 'transparent',
                  color: 'var(--color-text-primary)',
                  borderRadius: 'var(--border-radius-md)',
                  cursor: 'pointer'
                }}
              >
                Back
              </button>
              <button
                type="submit"
                disabled={loading || !market}
                style={{
                  flex: 1,
                  padding: '0.75rem',
                  fontSize: '15px',
                  fontWeight: 500,
                  border: '0.5px solid var(--color-border-info)',
                  background: 'var(--color-background-info)',
                  color: 'var(--color-text-info)',
                  borderRadius: 'var(--border-radius-md)',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  opacity: loading ? 0.7 : 1
                }}
              >
                {loading ? 'Sending...' : 'Continue'}
              </button>
            </div>
          </form>
        )}

        {/* Step 3: Confirmation */}
        {step === 'confirmation' && (
          <div style={{
            background: 'var(--color-background-primary)',
            border: '0.5px solid var(--color-border-tertiary)',
            borderRadius: 'var(--border-radius-lg)',
            padding: '2rem',
            textAlign: 'center'
          }}>
            <div style={{
              fontSize: '48px',
              marginBottom: '1rem'
            }}>
              ✓
            </div>
            <h2 style={{
              fontSize: '20px',
              fontWeight: 500,
              margin: '0 0 1rem 0',
              color: 'var(--color-text-primary)'
            }}>
              {tier === 'free' ? 'Welcome!' : 'Almost there!'}
            </h2>
            <p style={{
              fontSize: '15px',
              color: 'var(--color-text-secondary)',
              margin: '0 0 1.5rem 0',
              lineHeight: 1.6
            }}>
              {tier === 'free' 
                ? 'Check your email to confirm your subscription. You\'ll receive your first newsletter on Monday.'
                : 'Check your email to confirm and complete payment. You\'ll gain access to premium insights immediately.'}
            </p>
            <button
              onClick={reset}
              style={{
                padding: '0.75rem 1.5rem',
                fontSize: '15px',
                fontWeight: 500,
                border: '0.5px solid var(--color-border-secondary)',
                background: 'transparent',
                color: 'var(--color-text-primary)',
                borderRadius: 'var(--border-radius-md)',
                cursor: 'pointer'
              }}
            >
              Back to home
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
