import { useState } from 'react'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      <h1 style={{ color: '#1a73e8' }}>NotebookLM Clone - Test Page</h1>
      <p>If you can see this, React is working!</p>
      <button
        onClick={() => setCount(count + 1)}
        style={{
          padding: '10px 20px',
          background: '#1a73e8',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer'
        }}
      >
        Count: {count}
      </button>
      <div style={{ marginTop: '20px', padding: '10px', background: '#f0f0f0', borderRadius: '4px' }}>
        <p><strong>Status:</strong> ✅ React is rendering correctly</p>
        <p><strong>Next step:</strong> Check browser console for errors</p>
      </div>
    </div>
  )
}

export default App
